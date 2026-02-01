"""
Generate a real-time ultradian rhythm dashboard.
Auto-refreshes every 60 seconds in the browser.
Timezone-aware: India (Asia/Kolkata) from Feb 1, 2026 onwards.
"""

import sqlite3
import json
from datetime import datetime, timedelta
import webbrowser
import os


def get_sleep_data():
    """Fetch sleep data from the database."""
    conn = sqlite3.connect('productivity.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT date, sleep_hours, sleep_quality, sleep_debt, sleep_start, sleep_end
        FROM wellness_records
        ORDER BY date DESC
        LIMIT 1
    ''')
    latest = cursor.fetchone()

    if not latest:
        conn.close()
        return None

    # Get hourly scores for overlay
    cursor.execute('''
        SELECT ps.hour, ps.score
        FROM productivity_scores ps
        JOIN wellness_records wr ON ps.wellness_record_id = wr.id
        WHERE wr.date = ?
        ORDER BY ps.hour
    ''', (latest[0],))
    hourly_scores = cursor.fetchall()
    conn.close()

    scores_dict = {h: s for h, s in hourly_scores}

    wake_time = "07:00"
    bed_time = "23:00"
    sleep_hours = latest[1] or 0
    sleep_debt = latest[3] or 0

    if latest[5]:
        try:
            dt = datetime.fromisoformat(latest[5].replace('Z', '+00:00'))
            wake_time = dt.strftime("%H:%M")
        except:
            pass

    if latest[4]:
        try:
            dt = datetime.fromisoformat(latest[4].replace('Z', '+00:00'))
            bed_time = dt.strftime("%H:%M")
        except:
            pass

    return {
        'date': latest[0],
        'wake_time': wake_time,
        'bed_time': bed_time,
        'sleep_hours': sleep_hours,
        'sleep_debt': sleep_debt,
        'sleep_quality': latest[2] or 0,
        'sleep_cycles': int(sleep_hours / 1.5),
        'hourly_scores': [scores_dict.get(h, 0) for h in range(24)]
    }


def generate_realtime_html(data):
    """Generate the real-time ultradian rhythm HTML page."""

    hourly_json = json.dumps(data['hourly_scores'])
    sleep_cycles = data['sleep_cycles']
    sleep_quality = int((data['sleep_quality'] / 5) * 100) if data['sleep_quality'] else 0
    quality_class = 'good' if sleep_quality >= 70 else ('moderate' if sleep_quality >= 50 else 'poor')
    debt_class = 'good' if data['sleep_debt'] <= 2 else ('moderate' if data['sleep_debt'] <= 5 else 'poor')

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Live Ultradian Rhythm</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}

        body {{
            background: linear-gradient(135deg, #0a0a1a 0%, #111128 40%, #0d1f3c 100%);
            min-height: 100vh;
            color: #ffffff;
            padding: 20px;
            overflow-x: hidden;
        }}

        .page {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }}

        .header-left h1 {{
            font-size: 1.8rem;
            font-weight: 300;
            background: linear-gradient(90deg, #10b981, #6366f1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .header-left .subtitle {{
            color: #8892b0;
            font-size: 0.85rem;
            margin-top: 4px;
        }}

        .header-right {{
            text-align: right;
        }}

        .live-clock {{
            font-size: 2.5rem;
            font-weight: 200;
            letter-spacing: 2px;
            font-variant-numeric: tabular-nums;
        }}

        .timezone-label {{
            font-size: 0.75rem;
            color: #8892b0;
            margin-top: 2px;
        }}

        .live-dot {{
            display: inline-block;
            width: 8px;
            height: 8px;
            background: #10b981;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 1; transform: scale(1); }}
            50% {{ opacity: 0.4; transform: scale(0.8); }}
        }}

        /* Top row: Current State */
        .state-row {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 20px;
            margin-bottom: 25px;
        }}

        .card {{
            background: rgba(255, 255, 255, 0.04);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            transition: transform 0.3s, box-shadow 0.3s;
        }}

        .card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 15px 30px rgba(0, 0, 0, 0.3);
        }}

        .card-label {{
            font-size: 0.75rem;
            color: #8892b0;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 12px;
        }}

        /* Current Focus State */
        .focus-state-display {{
            text-align: center;
        }}

        .state-icon {{
            font-size: 3rem;
            margin-bottom: 10px;
        }}

        .state-name {{
            font-size: 1.6rem;
            font-weight: 600;
            margin-bottom: 5px;
        }}

        .state-name.peak {{ color: #10b981; }}
        .state-name.high {{ color: #667eea; }}
        .state-name.moderate {{ color: #f59e0b; }}
        .state-name.rest {{ color: #8b5cf6; }}
        .state-name.wind-down {{ color: #6366f1; }}
        .state-name.sleep {{ color: #475569; }}

        .state-desc {{
            font-size: 0.85rem;
            color: #8892b0;
            line-height: 1.4;
        }}

        /* Cycle Progress */
        .cycle-progress {{
            text-align: center;
        }}

        .progress-ring {{
            position: relative;
            width: 140px;
            height: 140px;
            margin: 0 auto 15px;
        }}

        .progress-ring svg {{
            transform: rotate(-90deg);
        }}

        .progress-ring .bg {{
            fill: none;
            stroke: rgba(255, 255, 255, 0.08);
            stroke-width: 10;
        }}

        .progress-ring .fg {{
            fill: none;
            stroke-width: 10;
            stroke-linecap: round;
            transition: stroke-dashoffset 1s ease;
        }}

        .progress-ring .center-text {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
        }}

        .progress-ring .mins {{
            font-size: 2rem;
            font-weight: 700;
        }}

        .progress-ring .mins-label {{
            font-size: 0.7rem;
            color: #8892b0;
        }}

        /* Countdown */
        .countdown-card {{
            text-align: center;
        }}

        .countdown-value {{
            font-size: 3rem;
            font-weight: 700;
            font-variant-numeric: tabular-nums;
        }}

        .countdown-value.to-peak {{ background: linear-gradient(135deg, #10b981, #059669); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}
        .countdown-value.to-trough {{ background: linear-gradient(135deg, #f59e0b, #d97706); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}

        .countdown-label {{
            font-size: 0.9rem;
            color: #8892b0;
            margin-top: 5px;
        }}

        .countdown-sub {{
            font-size: 0.8rem;
            color: #a78bfa;
            margin-top: 10px;
        }}

        /* Wave Section */
        .wave-section {{
            margin-bottom: 25px;
        }}

        .wave-card {{
            padding: 25px;
        }}

        .wave-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}

        .wave-chart {{
            height: 200px;
            position: relative;
        }}

        .now-marker {{
            color: #10b981;
            font-size: 0.8rem;
            font-weight: 600;
        }}

        /* Focus Blocks Timeline */
        .timeline-section {{
            margin-bottom: 25px;
        }}

        .timeline {{
            display: flex;
            gap: 8px;
            overflow-x: auto;
            padding: 10px 0;
        }}

        .block {{
            flex: 0 0 auto;
            width: 110px;
            border-radius: 14px;
            padding: 14px 12px;
            text-align: center;
            position: relative;
            transition: all 0.5s;
            border: 2px solid transparent;
        }}

        .block.active {{
            border-color: #10b981;
            box-shadow: 0 0 20px rgba(16, 185, 129, 0.3);
            transform: scale(1.05);
        }}

        .block.past {{
            opacity: 0.4;
        }}

        .block.peak {{ background: rgba(16, 185, 129, 0.15); }}
        .block.high {{ background: rgba(102, 126, 234, 0.15); }}
        .block.moderate {{ background: rgba(245, 158, 11, 0.15); }}
        .block.rest {{ background: rgba(139, 92, 246, 0.15); }}
        .block.wind-down {{ background: rgba(99, 102, 241, 0.15); }}

        .block-time {{
            font-size: 0.8rem;
            font-weight: 600;
            margin-bottom: 4px;
        }}

        .block-label {{
            font-size: 0.65rem;
            color: #8892b0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .block-energy {{
            font-size: 0.75rem;
            color: #a78bfa;
            margin-top: 6px;
        }}

        .block .active-badge {{
            position: absolute;
            top: -8px;
            right: -8px;
            background: #10b981;
            color: #fff;
            font-size: 0.6rem;
            padding: 2px 6px;
            border-radius: 8px;
            font-weight: 700;
            text-transform: uppercase;
        }}

        /* Bottom Row */
        .bottom-row {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 25px;
        }}

        /* Insight */
        .insight-box {{
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.08), rgba(99, 102, 241, 0.08));
            border-radius: 16px;
            padding: 20px;
            border-left: 4px solid #10b981;
        }}

        .insight-title {{
            font-size: 0.85rem;
            font-weight: 600;
            color: #10b981;
            margin-bottom: 10px;
        }}

        .insight-text {{
            font-size: 0.9rem;
            color: #ccd6f6;
            line-height: 1.6;
        }}

        /* Sleep Foundation */
        .sleep-foundation {{
            display: flex;
            gap: 20px;
        }}

        .sleep-stat {{
            flex: 1;
            text-align: center;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 12px;
            padding: 15px 10px;
        }}

        .sleep-stat-value {{
            font-size: 1.8rem;
            font-weight: 700;
        }}

        .sleep-stat-value.good {{ color: #10b981; }}
        .sleep-stat-value.moderate {{ color: #f59e0b; }}
        .sleep-stat-value.poor {{ color: #ef4444; }}

        .sleep-stat-label {{
            font-size: 0.7rem;
            color: #8892b0;
            margin-top: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        /* Refresh bar */
        .refresh-bar {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: rgba(255, 255, 255, 0.05);
        }}

        .refresh-progress {{
            height: 100%;
            background: linear-gradient(90deg, #10b981, #6366f1);
            width: 0%;
            transition: width 1s linear;
        }}

        .footer {{
            text-align: center;
            padding: 15px;
            color: #475569;
            font-size: 0.75rem;
        }}

        .update-tag {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-size: 0.7rem;
            color: #8892b0;
            background: rgba(255, 255, 255, 0.05);
            padding: 4px 10px;
            border-radius: 10px;
        }}

        @media (max-width: 900px) {{
            .state-row {{ grid-template-columns: 1fr; }}
            .bottom-row {{ grid-template-columns: 1fr; }}
            .live-clock {{ font-size: 1.8rem; }}
            .header {{ flex-direction: column; text-align: center; gap: 15px; }}
            .header-right {{ text-align: center; }}
        }}
    </style>
</head>
<body>
    <div class="page">
        <div class="header">
            <div class="header-left">
                <h1>Ultradian Rhythm</h1>
                <div class="subtitle"><span class="live-dot"></span>Live energy tracking based on your sleep pattern</div>
            </div>
            <div class="header-right">
                <div class="live-clock" id="liveClock">--:--:--</div>
                <div class="timezone-label" id="tzLabel">Detecting timezone...</div>
            </div>
        </div>

        <!-- Current State Row -->
        <div class="state-row">
            <div class="card">
                <div class="card-label">Current State</div>
                <div class="focus-state-display">
                    <div class="state-icon" id="stateIcon">--</div>
                    <div class="state-name" id="stateName">Loading...</div>
                    <div class="state-desc" id="stateDesc">Analyzing your rhythm...</div>
                </div>
            </div>

            <div class="card">
                <div class="card-label">Cycle Progress</div>
                <div class="cycle-progress">
                    <div class="progress-ring">
                        <svg width="140" height="140" viewBox="0 0 140 140">
                            <defs>
                                <linearGradient id="ringGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                                    <stop offset="0%" stop-color="#10b981" />
                                    <stop offset="100%" stop-color="#6366f1" />
                                </linearGradient>
                            </defs>
                            <circle class="bg" cx="70" cy="70" r="58" />
                            <circle class="fg" id="progressArc" cx="70" cy="70" r="58"
                                stroke="url(#ringGrad)"
                                stroke-dasharray="364.42"
                                stroke-dashoffset="364.42" />
                        </svg>
                        <div class="center-text">
                            <div class="mins" id="cycleMinutes">--</div>
                            <div class="mins-label">min into cycle</div>
                        </div>
                    </div>
                    <div style="font-size: 0.8rem; color: #8892b0;">
                        Cycle <span id="cycleNum">-</span> of today
                        <span style="margin-left: 5px; color: #a78bfa;" id="cyclePhase"></span>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-label">Next Transition</div>
                <div class="countdown-card">
                    <div class="countdown-value" id="countdownValue">--:--</div>
                    <div class="countdown-label" id="countdownLabel">until next peak</div>
                    <div class="countdown-sub" id="countdownSub"></div>
                </div>
            </div>
        </div>

        <!-- Wave Chart -->
        <div class="wave-section">
            <div class="card wave-card">
                <div class="wave-header">
                    <div>
                        <div class="card-label" style="margin-bottom: 0;">Ultradian Energy Wave</div>
                        <div style="font-size: 0.75rem; color: #8892b0;">Predicted vs actual energy through the day</div>
                    </div>
                    <div class="update-tag">
                        <span class="live-dot" style="width: 6px; height: 6px;"></span>
                        <span id="lastUpdate">Updating...</span>
                    </div>
                </div>
                <div class="wave-chart">
                    <canvas id="waveChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Focus Blocks Timeline -->
        <div class="timeline-section">
            <div class="card">
                <div class="card-label" style="margin-bottom: 15px;">90-Minute Focus Blocks</div>
                <div class="timeline" id="blocksTimeline">
                    <!-- Generated by JS -->
                </div>
            </div>
        </div>

        <!-- Bottom Row -->
        <div class="bottom-row">
            <div class="card">
                <div class="card-label">Live Insight</div>
                <div class="insight-box">
                    <div class="insight-title" id="insightTitle">Analyzing...</div>
                    <div class="insight-text" id="insightText">Calculating your current energy state based on ultradian rhythm...</div>
                </div>
            </div>

            <div class="card">
                <div class="card-label">Sleep Foundation (Today)</div>
                <div class="sleep-foundation">
                    <div class="sleep-stat">
                        <div class="sleep-stat-value {quality_class}" id="sleepScore">{sleep_quality}%</div>
                        <div class="sleep-stat-label">Quality</div>
                    </div>
                    <div class="sleep-stat">
                        <div class="sleep-stat-value" style="color: #a78bfa;">{data['sleep_hours']:.1f}h</div>
                        <div class="sleep-stat-label">Duration</div>
                    </div>
                    <div class="sleep-stat">
                        <div class="sleep-stat-value" style="color: #6366f1;">{sleep_cycles}</div>
                        <div class="sleep-stat-label">Cycles</div>
                    </div>
                    <div class="sleep-stat">
                        <div class="sleep-stat-value {debt_class}">{data['sleep_debt']:.1f}h</div>
                        <div class="sleep-stat-label">Debt</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="footer">
            Ultradian Rhythm Tracker | Wake: {data['wake_time']} | Auto-refresh every 60s
        </div>
    </div>

    <div class="refresh-bar">
        <div class="refresh-progress" id="refreshBar"></div>
    </div>

    <script>
    // === CONFIGURATION ===
    const WAKE_TIME = "{data['wake_time']}";
    const BED_TIME = "{data['bed_time']}";
    const SLEEP_HOURS = {data['sleep_hours']};
    const SLEEP_DEBT = {data['sleep_debt']};
    const SLEEP_CYCLES = {sleep_cycles};
    const HOURLY_SCORES = {hourly_json};

    // Timezone logic: India (Asia/Kolkata) from Feb 1, 2026
    function getTimezone() {{
        const now = new Date();
        const indiaStart = new Date(2026, 1, 1); // Feb 1, 2026
        if (now >= indiaStart) {{
            return 'Asia/Kolkata';
        }}
        // Before Feb 1 - use local system timezone
        return Intl.DateTimeFormat().resolvedOptions().timeZone;
    }}

    function getNow() {{
        const tz = getTimezone();
        const now = new Date();
        const options = {{ timeZone: tz, hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }};
        const parts = new Intl.DateTimeFormat('en-GB', options).formatToParts(now);
        let h = 0, m = 0, s = 0;
        parts.forEach(p => {{
            if (p.type === 'hour') h = parseInt(p.value);
            if (p.type === 'minute') m = parseInt(p.value);
            if (p.type === 'second') s = parseInt(p.value);
        }});
        return {{ hours: h, minutes: m, seconds: s, totalMinutes: h * 60 + m, tz: tz }};
    }}

    function parseTime(timeStr) {{
        const [h, m] = timeStr.split(':').map(Number);
        return h * 60 + m;
    }}

    const WAKE_MINS = parseTime(WAKE_TIME);
    const BED_MINS = parseTime(BED_TIME);
    const CYCLE_LENGTH = 90; // minutes
    const BLOCK_GAP = 20;   // break between blocks
    const FULL_CYCLE = CYCLE_LENGTH + BLOCK_GAP; // 110 min total

    // === FOCUS BLOCK GENERATION ===
    // Ultradian rhythm continues oscillating all day with diminishing peaks.
    // Block type is calculated dynamically based on hours awake and circadian curve.
    function getBlockType(hoursAwake, sleepCycles) {{
        // Circadian energy envelope (peaks ~2-4h after wake, dips ~7-8h, slight rise ~10h)
        let circadianEnergy;
        if (hoursAwake < 1) circadianEnergy = 70;
        else if (hoursAwake < 4) circadianEnergy = 90;         // Morning peak
        else if (hoursAwake < 6) circadianEnergy = 80;
        else if (hoursAwake < 8) circadianEnergy = 55;         // Post-lunch dip
        else if (hoursAwake < 10) circadianEnergy = 70;        // Afternoon rebound
        else if (hoursAwake < 13) circadianEnergy = 60;        // Evening decline
        else circadianEnergy = 40;                              // Late evening

        // Sleep debt penalty: fewer cycles = lower ceiling
        const debtFactor = Math.min(1, sleepCycles / 5);
        const energy = circadianEnergy * debtFactor;

        if (energy >= 80) return {{ type: 'peak',      label: 'Peak Focus',      icon: '🔥' }};
        if (energy >= 65) return {{ type: 'high',       label: 'High Focus',      icon: '⚡' }};
        if (energy >= 50) return {{ type: 'moderate',   label: 'Steady Work',     icon: '🎯' }};
        if (energy >= 35) return {{ type: 'wind-down',  label: 'Light Tasks',     icon: '🌙' }};
        return                     {{ type: 'rest',      label: 'Rest & Recharge', icon: '🧘' }};
    }}

    function generateBlocks() {{
        const blocks = [];
        let startMin = WAKE_MINS;

        // Generate blocks until bedtime -- ultradian rhythm doesn't stop after 6 cycles
        for (let i = 0; i < 12; i++) {{
            const endMin = startMin + CYCLE_LENGTH;
            if (startMin >= BED_MINS) break;   // Stop at bedtime
            if (startMin > 24 * 60) break;

            const hoursAwake = (startMin - WAKE_MINS) / 60;
            const blockInfo = getBlockType(hoursAwake, SLEEP_CYCLES);

            const sh = Math.floor(startMin / 60) % 24;
            const sm = startMin % 60;
            const eh = Math.floor(endMin / 60) % 24;
            const em = endMin % 60;

            blocks.push({{
                start: startMin,
                end: endMin,
                startStr: `${{String(sh).padStart(2,'0')}}:${{String(sm).padStart(2,'0')}}`,
                endStr: `${{String(eh).padStart(2,'0')}}:${{String(em).padStart(2,'0')}}`,
                type: blockInfo.type,
                label: blockInfo.label,
                icon: blockInfo.icon,
                num: i + 1
            }});

            startMin += FULL_CYCLE;
        }}
        return blocks;
    }}

    const BLOCKS = generateBlocks();

    // === SLEEP DETECTION ===
    // Smart sleep detection: combines time-of-day, hours awake, and circadian model.
    // Rather than a hard cutoff, it models sleep probability.
    function isSleepWindow(nowMins) {{
        // Handle wrap-around: bed time like 23:00 means sleep window is 23:00 -> wake time next day
        // If bed < wake (overnight sleep), sleep window = [bed..24) + [0..wake)
        // If bed > wake (unusual), sleep window = [bed..wake)
        if (BED_MINS > WAKE_MINS) {{
            // Typical overnight: e.g. bed=23:00 (1380), wake=07:00 (420)
            // Sleep window: nowMins >= 1380 OR nowMins < 420
            return nowMins >= BED_MINS || nowMins < WAKE_MINS;
        }} else {{
            // Same-day: e.g. bed=01:00 (60), wake=09:00 (540)
            return nowMins >= BED_MINS && nowMins < WAKE_MINS;
        }}
    }}

    function getSleepCycleState(nowMins) {{
        // During sleep, determine which 90-min sleep cycle you're in
        let sleepStart = BED_MINS;
        let sleepMins;
        if (nowMins >= BED_MINS) {{
            sleepMins = nowMins - BED_MINS;
        }} else {{
            sleepMins = (24 * 60 - BED_MINS) + nowMins;
        }}

        const sleepCycleNum = Math.floor(sleepMins / 90) + 1;
        const posInCycle = sleepMins % 90;

        // Sleep stages within a 90-min cycle:
        // 0-15: Light Sleep (N1/N2), 15-45: Deep Sleep (N3), 45-75: REM, 75-90: Brief arousal
        let stage, stageIcon;
        if (posInCycle < 15)      {{ stage = 'Light Sleep (N1/N2)'; stageIcon = '💤'; }}
        else if (posInCycle < 45) {{ stage = 'Deep Sleep (N3)';     stageIcon = '🌊'; }}
        else if (posInCycle < 75) {{ stage = 'REM Sleep';           stageIcon = '🧠'; }}
        else                      {{ stage = 'Brief Arousal';       stageIcon = '👁️'; }}

        const totalSleepH = (sleepMins / 60).toFixed(1);
        return {{
            state: 'sleep', icon: stageIcon, name: stage,
            desc: `Sleep cycle ${{sleepCycleNum}} of ~${{Math.ceil(SLEEP_HOURS / 1.5)}} expected. You've been asleep ~${{totalSleepH}}h. ${{
                posInCycle < 15 ? 'Transitioning into deeper sleep. Body temperature dropping.' :
                posInCycle < 45 ? 'Deep restorative sleep. Growth hormone release, tissue repair, immune strengthening. Hardest to wake from this stage.' :
                posInCycle < 75 ? 'REM sleep. Brain is highly active — consolidating memories, processing emotions, creative problem solving.' :
                'Brief natural arousal between cycles. Normal to slightly wake here.'
            }}`,
            energy: 5, sleepCycleNum: sleepCycleNum, sleepStage: stage, posInCycle: posInCycle
        }};
    }}

    // === STATE CALCULATIONS ===
    function getCurrentState(nowMins) {{
        // Smart sleep detection
        if (isSleepWindow(nowMins)) {{
            return getSleepCycleState(nowMins);
        }}

        const awakeMinutes = nowMins - WAKE_MINS;
        const hoursAwake = awakeMinutes / 60;

        // Position within the 110-min full cycle (90 focus + 20 break)
        const posInFullCycle = awakeMinutes % FULL_CYCLE;
        const cycleNum = Math.floor(awakeMinutes / FULL_CYCLE) + 1;
        const isBreak = posInFullCycle >= CYCLE_LENGTH;

        // Circadian energy envelope (same model as block generation)
        let circadianEnergy;
        if (hoursAwake < 1) circadianEnergy = 70;
        else if (hoursAwake < 4) circadianEnergy = 90;
        else if (hoursAwake < 6) circadianEnergy = 80;
        else if (hoursAwake < 8) circadianEnergy = 55;
        else if (hoursAwake < 10) circadianEnergy = 70;
        else if (hoursAwake < 13) circadianEnergy = 60;
        else circadianEnergy = 40;

        // Sleep debt penalty
        const debtFactor = Math.min(1, SLEEP_CYCLES / 5);
        const circadianBase = circadianEnergy * debtFactor;

        if (isBreak) {{
            return {{
                state: 'rest', icon: '☕', name: 'Natural Break',
                desc: `Cycle #${{cycleNum}} complete (${{hoursAwake.toFixed(1)}}h awake). Your brain's ultradian trough — neural networks are resetting. Take a 15-20 min break: walk, hydrate, look at distant objects. Forcing deep work now fights your biology. Next focus wave starts soon.`,
                energy: Math.round(circadianBase * 0.5), cycleNum, cyclePosition: CYCLE_LENGTH, inBreak: true
            }};
        }}

        // Within a 90-min focus block
        const cyclePosition = posInFullCycle;
        let phase, phaseName;
        if (cyclePosition < 20) {{
            phase = 'ramp-up';
            phaseName = 'Ramping Up';
        }} else if (cyclePosition < 70) {{
            phase = 'peak-zone';
            phaseName = 'Peak Zone';
        }} else {{
            phase = 'winding';
            phaseName = 'Winding Down';
        }}

        // Ultradian wave within the cycle (sinusoidal peak at 45 min)
        const wavePosition = cyclePosition / CYCLE_LENGTH;
        const ultradianBoost = Math.sin(wavePosition * Math.PI) * 20;
        const energy = Math.min(100, Math.max(20, circadianBase + ultradianBoost));

        // Determine display state from the actual computed energy
        let state, icon, name, desc;
        if (energy >= 75) {{
            state = 'peak'; icon = '🔥'; name = 'Peak Performance';
            desc = `Cycle #${{cycleNum}}, ${{phaseName}} — ${{hoursAwake.toFixed(1)}}h awake. Circadian + ultradian alignment at ${{Math.round(energy)}}%. Your prefrontal cortex has peak blood flow. Use this for your hardest cognitive work: coding, writing, strategic decisions.`;
        }} else if (energy >= 60) {{
            state = 'high'; icon = '⚡'; name = 'High Focus';
            desc = `Cycle #${{cycleNum}}, ${{phaseName}} — ${{hoursAwake.toFixed(1)}}h awake. Strong cognitive window at ${{Math.round(energy)}}%. Ideal for deep work, complex problem-solving, or sustained creative thinking.`;
        }} else if (energy >= 45) {{
            state = 'moderate'; icon = '🎯'; name = 'Steady State';
            desc = `Cycle #${{cycleNum}}, ${{phaseName}} — ${{hoursAwake.toFixed(1)}}h awake. Energy at ${{Math.round(energy)}}%. Your ultradian cycle provides focus but circadian drive is lower. Good for collaborative work, routine tasks, or lighter coding.`;
        }} else if (energy >= 30) {{
            state = 'wind-down'; icon = '🌙'; name = 'Low Energy';
            desc = `Cycle #${{cycleNum}}, ${{phaseName}} — ${{hoursAwake.toFixed(1)}}h awake. Energy at ${{Math.round(energy)}}%.${{SLEEP_DEBT > 3 ? ' Sleep debt (' + SLEEP_DEBT.toFixed(1) + 'h) is dragging you down.' : ''}} Best for planning, organizing, email, or light creative work.`;
        }} else {{
            state = 'rest'; icon = '🧘'; name = 'Recovery Zone';
            desc = `${{hoursAwake.toFixed(1)}}h awake. Energy at ${{Math.round(energy)}}%. Your body is signaling for rest. Avoid blue light and caffeine. Gentle activities, reading, or meditation. Consider heading to bed soon.`;
        }}

        return {{ state, icon, name, desc, energy: Math.round(energy), cycleNum, cyclePosition, phase, phaseName }};
    }}

    function getNextTransition(nowMins) {{
        // If in sleep window, next transition is wake time
        if (isSleepWindow(nowMins)) {{
            let minsToWake;
            if (nowMins >= BED_MINS) {{
                minsToWake = (24 * 60 - nowMins) + WAKE_MINS;
            }} else {{
                minsToWake = WAKE_MINS - nowMins;
            }}
            // Also show next sleep cycle boundary
            let sleepMins = nowMins >= BED_MINS ? (nowMins - BED_MINS) : ((24 * 60 - BED_MINS) + nowMins);
            const nextCycleBoundary = (Math.floor(sleepMins / 90) + 1) * 90 - sleepMins;

            if (nextCycleBoundary < minsToWake) {{
                const cycleTime = (nowMins + nextCycleBoundary) % (24 * 60);
                const ch = Math.floor(cycleTime / 60) % 24;
                const cm = cycleTime % 60;
                return {{
                    mins: nextCycleBoundary,
                    label: 'until next sleep cycle',
                    type: 'peak',
                    time: `${{String(ch).padStart(2,'0')}}:${{String(cm).padStart(2,'0')}}`
                }};
            }}

            return {{ mins: minsToWake, label: 'until wake time', type: 'peak', time: WAKE_TIME }};
        }}

        const awakeMinutes = nowMins - WAKE_MINS;
        const posInFullCycle = awakeMinutes % FULL_CYCLE;

        if (posInFullCycle < CYCLE_LENGTH) {{
            // In focus block - next is break
            const minsToBreak = CYCLE_LENGTH - posInFullCycle;
            const breakTime = nowMins + minsToBreak;
            const bh = Math.floor(breakTime / 60) % 24;
            const bm = breakTime % 60;
            return {{
                mins: minsToBreak,
                label: 'until natural break',
                type: 'trough',
                time: `${{String(bh).padStart(2,'0')}}:${{String(bm).padStart(2,'0')}}`
            }};
        }} else {{
            // In break - next is focus
            const minsToFocus = FULL_CYCLE - posInFullCycle;
            const focusTime = nowMins + minsToFocus;
            const fh = Math.floor(focusTime / 60) % 24;
            const fm = focusTime % 60;
            return {{
                mins: minsToFocus,
                label: 'until next focus wave',
                type: 'peak',
                time: `${{String(fh).padStart(2,'0')}}:${{String(fm).padStart(2,'0')}}`
            }};
        }}
    }}

    // === WAVE DATA ===
    // Uses the same circadian + ultradian model as block generation and state detection
    function getEnergyAt(totalMins) {{
        if (isSleepWindow(totalMins)) return 5; // Sleeping

        const awake = totalMins - WAKE_MINS;
        if (awake < 0) return 5;
        const hoursAwake = awake / 60;

        // Circadian envelope (matches getBlockType and getCurrentState)
        let circadianEnergy;
        if (hoursAwake < 1) circadianEnergy = 70;
        else if (hoursAwake < 4) circadianEnergy = 90;
        else if (hoursAwake < 6) circadianEnergy = 80;
        else if (hoursAwake < 8) circadianEnergy = 55;     // Post-lunch dip
        else if (hoursAwake < 10) circadianEnergy = 70;    // Afternoon rebound
        else if (hoursAwake < 13) circadianEnergy = 60;
        else circadianEnergy = 40;

        // Sleep debt factor
        const debtFactor = Math.min(1, SLEEP_CYCLES / 5);
        const base = circadianEnergy * debtFactor;

        // Ultradian oscillation (continuous 90-min wave)
        const posInFullCycle = awake % FULL_CYCLE;
        const inBreak = posInFullCycle >= CYCLE_LENGTH;

        if (inBreak) {{
            // During break: energy drops to trough
            return Math.max(15, base * 0.5);
        }}

        // Sinusoidal peak at 45 min into 90-min focus block
        const cyclePos = posInFullCycle / CYCLE_LENGTH;
        const ultradianBoost = Math.sin(cyclePos * Math.PI) * 20;

        return Math.min(100, Math.max(15, base + ultradianBoost));
    }}

    function generateWaveData() {{
        const data = [];
        for (let hour = 0; hour < 24; hour++) {{
            for (let quarter = 0; quarter < 4; quarter++) {{
                const totalMins = hour * 60 + quarter * 15;
                data.push(getEnergyAt(totalMins));
            }}
        }}
        return data;
    }}

    // === UI UPDATE ===
    let waveChart = null;

    function updateUI() {{
        const now = getNow();
        const nowMins = now.totalMinutes;

        // Clock
        document.getElementById('liveClock').textContent =
            `${{String(now.hours).padStart(2,'0')}}:${{String(now.minutes).padStart(2,'0')}}:${{String(now.seconds).padStart(2,'0')}}`;
        document.getElementById('tzLabel').textContent = now.tz.replace('_', ' ');

        // Current state
        const state = getCurrentState(nowMins);
        document.getElementById('stateIcon').textContent = state.icon;
        const nameEl = document.getElementById('stateName');
        nameEl.textContent = state.name;
        nameEl.className = 'state-name ' + state.state;
        document.getElementById('stateDesc').textContent = state.desc;

        // Cycle progress ring
        const circumference = 2 * Math.PI * 58;
        if (state.state === 'sleep' && state.posInCycle !== undefined) {{
            // Sleep: show progress within the 90-min sleep cycle
            const progress = state.posInCycle / 90;
            document.getElementById('progressArc').style.strokeDashoffset = circumference - (progress * circumference);
            document.getElementById('cycleMinutes').textContent = Math.floor(state.posInCycle);
            document.getElementById('cycleNum').textContent = state.sleepCycleNum;
            document.getElementById('cyclePhase').textContent = state.sleepStage || 'Sleeping';
        }} else if (state.cyclePosition !== undefined) {{
            const progress = state.inBreak ? 1 : state.cyclePosition / CYCLE_LENGTH;
            document.getElementById('progressArc').style.strokeDashoffset = circumference - (progress * circumference);
            document.getElementById('cycleMinutes').textContent = Math.floor(state.cyclePosition);
            document.getElementById('cycleNum').textContent = state.cycleNum;
            document.getElementById('cyclePhase').textContent = state.phaseName || (state.inBreak ? 'Break' : '');
        }} else {{
            document.getElementById('progressArc').style.strokeDashoffset = circumference;
            document.getElementById('cycleMinutes').textContent = '--';
            document.getElementById('cycleNum').textContent = '-';
            document.getElementById('cyclePhase').textContent = state.name;
        }}

        // Countdown
        const next = getNextTransition(nowMins);
        const countdownMins = Math.max(0, next.mins);
        const cm = countdownMins % 60;
        const ch = Math.floor(countdownMins / 60);
        document.getElementById('countdownValue').textContent =
            ch > 0 ? `${{ch}}h ${{String(cm).padStart(2,'0')}}m` : `${{cm}} min`;
        document.getElementById('countdownValue').className =
            'countdown-value ' + (next.type === 'peak' ? 'to-peak' : 'to-trough');
        document.getElementById('countdownLabel').textContent = next.label;
        document.getElementById('countdownSub').textContent = `at ${{next.time}}`;

        // Focus blocks timeline
        const timeline = document.getElementById('blocksTimeline');
        timeline.innerHTML = '';
        BLOCKS.forEach(block => {{
            const isActive = nowMins >= block.start && nowMins < block.end;
            const isPast = nowMins >= block.end;
            const div = document.createElement('div');
            div.className = `block ${{block.type}} ${{isActive ? 'active' : ''}} ${{isPast ? 'past' : ''}}`;
            div.innerHTML = `
                ${{isActive ? '<span class="active-badge">NOW</span>' : ''}}
                <div style="font-size: 1.2rem; margin-bottom: 6px;">${{block.icon}}</div>
                <div class="block-time">${{block.startStr}}</div>
                <div class="block-time" style="font-size: 0.7rem; color: #475569;">${{block.endStr}}</div>
                <div class="block-label">${{block.label}}</div>
            `;
            timeline.appendChild(div);

            // Add break indicator between blocks
            if (!isPast && block.num < BLOCKS.length) {{
                const brk = document.createElement('div');
                brk.style.cssText = 'flex: 0 0 auto; display: flex; align-items: center; font-size: 0.7rem; color: #475569;';
                brk.textContent = '~20m';
                timeline.appendChild(brk);
            }}
        }});

        // Live insight
        generateInsight(state, now, next);

        // Update timestamp
        document.getElementById('lastUpdate').textContent =
            `Updated ${{String(now.hours).padStart(2,'0')}}:${{String(now.minutes).padStart(2,'0')}}`;
    }}

    function generateInsight(state, now, next) {{
        const titleEl = document.getElementById('insightTitle');
        const textEl = document.getElementById('insightText');

        if (state.state === 'sleep') {{
            const stg = state.sleepStage || 'Sleep';
            const cyc = state.sleepCycleNum || '?';
            titleEl.textContent = `${{stg}} — Cycle ${{cyc}}`;
            textEl.textContent = state.desc;
            return;
        }}

        const awakeHours = ((now.totalMinutes - WAKE_MINS) / 60).toFixed(1);

        if (state.inBreak) {{
            titleEl.textContent = `Ultradian Trough — Break Window`;
            textEl.textContent = `You've been awake ${{awakeHours}} hours. Cycle #${{state.cycleNum}} is complete. Your brain is in a natural 20-min recovery trough between 90-min focus waves. Take a break: walk, hydrate, stretch. Forcing deep work now works against your biology. Next focus wave at ${{next.time}}.`;
        }} else if (state.phase === 'ramp-up') {{
            titleEl.textContent = `Cycle #${{state.cycleNum}} Starting — Ramp Up`;
            textEl.textContent = `New 90-minute focus wave beginning (${{awakeHours}}h awake, energy ${{state.energy}}%). Your neural oscillations are synchronizing. Start with easier tasks for the first 15-20 min, then transition to your most demanding work as you approach peak zone.`;
        }} else if (state.phase === 'peak-zone') {{
            titleEl.textContent = `Cycle #${{state.cycleNum}} Peak Zone — Go Deep`;
            textEl.textContent = `You're in the golden window (${{awakeHours}}h awake, energy ${{state.energy}}%). Maximum prefrontal cortex activity. This is your biological best for complex reasoning, coding, writing, or decision-making. Protect this time. Next trough at ${{next.time}}.`;
        }} else if (state.phase === 'winding') {{
            const minsLeft = Math.round(CYCLE_LENGTH - state.cyclePosition);
            titleEl.textContent = `Cycle #${{state.cycleNum}} Winding — ${{minsLeft}} min left`;
            textEl.textContent = `Focus wave #${{state.cycleNum}} is fading (${{awakeHours}}h awake, energy ${{state.energy}}%). Wrap up current deep task. A natural 20-min break window opens at ${{next.time}}. Your ultradian rhythm will deliver another focus wave after the break.`;
        }} else {{
            titleEl.textContent = `${{state.name}} — Energy ${{state.energy}}%`;
            textEl.textContent = `${{awakeHours}}h awake, cycle #${{state.cycleNum}}. ${{SLEEP_DEBT > 3 ? 'Sleep debt (' + SLEEP_DEBT.toFixed(1) + 'h) is reducing your ceiling. ' : ''}}Your ultradian rhythm keeps oscillating — ${{state.energy >= 40 ? 'you still have usable focus windows for lighter work.' : 'consider winding down for the day. Your body needs recovery.'}}`;
        }}
    }}

    // === CHART ===
    function initChart() {{
        const ctx = document.getElementById('waveChart').getContext('2d');
        const waveData = generateWaveData();

        // Labels: every 15 mins
        const labels = [];
        for (let h = 0; h < 24; h++) {{
            for (let q = 0; q < 4; q++) {{
                labels.push(q === 0 ? `${{String(h).padStart(2,'0')}}:00` : '');
            }}
        }}

        // Current time marker
        const now = getNow();
        const nowIdx = now.hours * 4 + Math.floor(now.minutes / 15);

        // Actual energy (hourly, interpolated to quarter-hour)
        const actualData = [];
        for (let h = 0; h < 24; h++) {{
            const thisVal = HOURLY_SCORES[h];
            const nextVal = HOURLY_SCORES[(h + 1) % 24];
            for (let q = 0; q < 4; q++) {{
                actualData.push(thisVal + (nextVal - thisVal) * (q / 4));
            }}
        }}

        const waveGrad = ctx.createLinearGradient(0, 0, 0, 200);
        waveGrad.addColorStop(0, 'rgba(16, 185, 129, 0.5)');
        waveGrad.addColorStop(0.5, 'rgba(99, 102, 241, 0.3)');
        waveGrad.addColorStop(1, 'rgba(99, 102, 241, 0.05)');

        // Create "now" line plugin
        const nowLinePlugin = {{
            id: 'nowLine',
            afterDraw(chart) {{
                const now = getNow();
                const idx = now.hours * 4 + Math.floor(now.minutes / 15);
                const meta = chart.getDatasetMeta(0);
                if (meta.data[idx]) {{
                    const x = meta.data[idx].x;
                    const ctx = chart.ctx;
                    const yAxis = chart.scales.y;

                    ctx.save();
                    ctx.beginPath();
                    ctx.setLineDash([4, 4]);
                    ctx.strokeStyle = '#10b981';
                    ctx.lineWidth = 2;
                    ctx.moveTo(x, yAxis.top);
                    ctx.lineTo(x, yAxis.bottom);
                    ctx.stroke();

                    // "NOW" label
                    ctx.fillStyle = '#10b981';
                    ctx.font = 'bold 10px sans-serif';
                    ctx.textAlign = 'center';
                    ctx.fillText('NOW', x, yAxis.top - 5);
                    ctx.restore();
                }}
            }}
        }};

        waveChart = new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: labels,
                datasets: [
                    {{
                        label: 'Predicted Rhythm',
                        data: waveData,
                        fill: true,
                        backgroundColor: waveGrad,
                        borderColor: '#10b981',
                        borderWidth: 2,
                        tension: 0.4,
                        pointRadius: 0,
                        pointHoverRadius: 4
                    }},
                    {{
                        label: 'Actual Energy',
                        data: actualData,
                        fill: false,
                        borderColor: 'rgba(167, 139, 250, 0.5)',
                        borderWidth: 1.5,
                        borderDash: [4, 4],
                        tension: 0.3,
                        pointRadius: 0
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: true,
                        position: 'top',
                        align: 'end',
                        labels: {{ color: '#8892b0', font: {{ size: 10 }}, boxWidth: 12, usePointStyle: true }}
                    }},
                    tooltip: {{
                        backgroundColor: 'rgba(10, 10, 26, 0.95)',
                        titleColor: '#fff',
                        bodyColor: '#10b981',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: true,
                        filter: function(item) {{ return item.dataIndex % 4 === 0; }},
                        callbacks: {{
                            title: function(ctx) {{
                                const idx = ctx[0].dataIndex;
                                const h = Math.floor(idx / 4);
                                const m = (idx % 4) * 15;
                                return `${{String(h).padStart(2,'0')}}:${{String(m).padStart(2,'0')}}`;
                            }},
                            label: function(ctx) {{ return ctx.dataset.label + ': ' + Math.round(ctx.raw) + '%'; }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        grid: {{ color: 'rgba(255, 255, 255, 0.03)' }},
                        ticks: {{
                            color: '#8892b0',
                            font: {{ size: 9 }},
                            maxTicksLimit: 24,
                            callback: function(val, idx) {{ return idx % 4 === 0 ? this.getLabelForValue(val) : ''; }}
                        }}
                    }},
                    y: {{
                        min: 0, max: 100,
                        grid: {{ color: 'rgba(255, 255, 255, 0.03)' }},
                        ticks: {{ color: '#8892b0', font: {{ size: 9 }}, stepSize: 25 }}
                    }}
                }}
            }},
            plugins: [nowLinePlugin]
        }});
    }}

    // === REFRESH LOGIC ===
    let refreshCounter = 0;

    function tick() {{
        // Update clock every second
        const now = getNow();
        document.getElementById('liveClock').textContent =
            `${{String(now.hours).padStart(2,'0')}}:${{String(now.minutes).padStart(2,'0')}}:${{String(now.seconds).padStart(2,'0')}}`;

        // Refresh bar animation
        refreshCounter++;
        const progress = (refreshCounter / 60) * 100;
        document.getElementById('refreshBar').style.width = progress + '%';

        if (refreshCounter >= 60) {{
            refreshCounter = 0;
            updateUI();
            if (waveChart) waveChart.update();
        }}
    }}

    // === INIT ===
    window.addEventListener('load', () => {{
        initChart();
        updateUI();
        setInterval(tick, 1000);
    }});
    </script>
</body>
</html>'''

    return html


def main():
    """Generate and open the real-time ultradian rhythm page."""
    print("Fetching sleep data from database...")
    data = get_sleep_data()

    if not data:
        print("No data found in database!")
        return

    print(f"Generating real-time ultradian page (wake: {data['wake_time']}, sleep: {data['sleep_hours']:.1f}h)...")

    html = generate_realtime_html(data)

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ultradian_live.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Real-time dashboard saved to: {output_path}")
    webbrowser.open('file://' + os.path.realpath(output_path))
    print("Opened in browser! Auto-refreshes every 60 seconds.")


if __name__ == '__main__':
    main()

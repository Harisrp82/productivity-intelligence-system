"""
Generate a beautiful HTML dashboard from productivity data.
Inspired by modern health tracking UI designs.
"""

import sqlite3
import json
import math
from datetime import datetime, timedelta
import webbrowser
import os

def calculate_optimal_bedtime(wake_time_str, sleep_debt, avg_sleep_hours):
    """Calculate optimal bedtime windows based on wake time and sleep needs."""

    # Parse wake time
    if wake_time_str == "--:--":
        wake_hour = 7
        wake_minute = 0
    else:
        try:
            parts = wake_time_str.split(':')
            wake_hour = int(parts[0])
            wake_minute = int(parts[1])
        except:
            wake_hour = 7
            wake_minute = 0

    # Calculate target sleep duration
    # Base need: 7.5-8 hours (5-6 complete 90-min cycles)
    base_sleep_need = 7.5

    # Add extra time if sleep debt is high
    if sleep_debt > 5:
        extra_sleep = 1.0  # Add 1 hour for high debt
    elif sleep_debt > 2:
        extra_sleep = 0.5  # Add 30 mins for moderate debt
    else:
        extra_sleep = 0

    target_sleep = base_sleep_need + extra_sleep

    # Calculate bedtime windows (sleep gates occur every ~90 mins)
    # Work backwards from wake time
    bedtime_windows = []

    # Optimal cycles: 5, 5.5, 6 (7.5h, 8.25h, 9h)
    cycle_options = [
        (5, "5 cycles - 7.5h"),
        (5.5, "5.5 cycles - 8.25h"),
        (6, "6 cycles - 9h")
    ]

    for cycles, label in cycle_options:
        sleep_duration_mins = int(cycles * 90)

        # Calculate bedtime
        bed_minute = wake_minute - (sleep_duration_mins % 60)
        bed_hour = wake_hour - (sleep_duration_mins // 60)

        if bed_minute < 0:
            bed_minute += 60
            bed_hour -= 1

        if bed_hour < 0:
            bed_hour += 24

        # Add 15 mins to account for falling asleep
        fall_asleep_mins = 15
        bed_minute -= fall_asleep_mins
        if bed_minute < 0:
            bed_minute += 60
            bed_hour -= 1
        if bed_hour < 0:
            bed_hour += 24

        bedtime_str = f"{bed_hour:02d}:{bed_minute:02d}"

        # Determine if this is the recommended window
        total_sleep = cycles * 1.5
        is_recommended = False
        if sleep_debt > 5 and cycles >= 6:
            is_recommended = True
        elif sleep_debt > 2 and cycles >= 5.5:
            is_recommended = True
        elif sleep_debt <= 2 and cycles == 5:
            is_recommended = True

        bedtime_windows.append({
            'time': bedtime_str,
            'cycles': cycles,
            'duration': total_sleep,
            'label': label,
            'recommended': is_recommended
        })

    # Calculate ideal bedtime based on sleep debt
    if sleep_debt > 5:
        ideal_cycles = 6
        recovery_note = "High sleep debt - aim for 6 full cycles to recover"
    elif sleep_debt > 2:
        ideal_cycles = 5.5
        recovery_note = "Moderate debt - extra half cycle recommended"
    else:
        ideal_cycles = 5
        recovery_note = "Well rested - 5 cycles maintains optimal recovery"

    ideal_duration_mins = int(ideal_cycles * 90) + 15  # +15 for falling asleep
    ideal_bed_minute = wake_minute - (ideal_duration_mins % 60)
    ideal_bed_hour = wake_hour - (ideal_duration_mins // 60)

    if ideal_bed_minute < 0:
        ideal_bed_minute += 60
        ideal_bed_hour -= 1
    if ideal_bed_hour < 0:
        ideal_bed_hour += 24

    # Calculate sleep gate windows (natural melatonin peaks)
    # These occur roughly at 9 PM, 10:30 PM, 12 AM based on typical circadian rhythm
    sleep_gates = []
    gate_start = 21  # 9 PM
    for i in range(4):
        gate_hour = gate_start + int(i * 1.5)
        gate_minute = 30 if i % 2 == 1 else 0
        if gate_hour >= 24:
            gate_hour -= 24
        sleep_gates.append(f"{gate_hour:02d}:{gate_minute:02d}")

    return {
        'ideal_bedtime': f"{ideal_bed_hour:02d}:{ideal_bed_minute:02d}",
        'ideal_cycles': ideal_cycles,
        'target_wake': f"{wake_hour:02d}:{wake_minute:02d}",
        'windows': bedtime_windows,
        'sleep_gates': sleep_gates,
        'recovery_note': recovery_note,
        'sleep_debt': sleep_debt
    }


def calculate_ultradian_cycles(wake_time_str, sleep_hours):
    """Calculate ultradian rhythm cycles and focus blocks from wake time."""

    # Default wake time if not available
    if wake_time_str == "--:--":
        wake_hour = 7
        wake_minute = 0
    else:
        try:
            parts = wake_time_str.split(':')
            wake_hour = int(parts[0])
            wake_minute = int(parts[1])
        except:
            wake_hour = 7
            wake_minute = 0

    # Calculate complete sleep cycles (each cycle is ~90 minutes)
    sleep_cycles_complete = int(sleep_hours / 1.5)
    sleep_cycles_partial = (sleep_hours % 1.5) / 1.5

    # Calculate focus blocks based on 90-minute ultradian rhythm
    # After waking, energy follows a 90-120 minute cycle
    focus_blocks = []
    current_hour = wake_hour
    current_minute = wake_minute

    # Generate 8 focus blocks throughout the day (covering ~12 hours of waking time)
    for i in range(8):
        block_start = f"{current_hour:02d}:{current_minute:02d}"

        # Each focus block is 90 minutes
        end_minute = current_minute + 90
        end_hour = current_hour + (end_minute // 60)
        end_minute = end_minute % 60

        if end_hour >= 24:
            end_hour = end_hour % 24

        block_end = f"{end_hour:02d}:{end_minute:02d}"

        # Determine block type based on position in day
        if i < 2:
            block_type = "peak"  # First 3 hours after waking - highest alertness
        elif i < 4:
            block_type = "high"  # Mid-morning/afternoon focus
        elif i < 6:
            block_type = "moderate"  # Post-lunch dip expected
        else:
            block_type = "wind-down"  # Evening - prepare for sleep

        # Calculate energy level for this block (ultradian wave pattern)
        # Peaks at 0, 90, 180 mins etc., troughs at 45, 135 mins etc.
        base_energy = 75 - (i * 5)  # Gradual decline through day

        focus_blocks.append({
            'start': block_start,
            'end': block_end,
            'type': block_type,
            'block_num': i + 1,
            'energy': max(40, base_energy)
        })

        # Move to next block (90 min focus + 20 min break = 110 min cycle)
        current_minute = current_minute + 110
        current_hour = current_hour + (current_minute // 60)
        current_minute = current_minute % 60

        if current_hour >= 24:
            break

    # Calculate recommended break times (every 90 minutes)
    break_times = []
    current_hour = wake_hour
    current_minute = wake_minute + 90  # First break after 90 mins

    for i in range(6):
        if current_minute >= 60:
            current_hour += current_minute // 60
            current_minute = current_minute % 60

        if current_hour >= 22:  # Stop breaks after 10 PM
            break

        break_times.append({
            'time': f"{current_hour:02d}:{current_minute:02d}",
            'duration': 15 if i % 2 == 0 else 20,  # Alternate 15/20 min breaks
            'type': 'short' if i % 2 == 0 else 'long'
        })

        current_minute += 110  # Next break in 110 mins

    # Generate ultradian wave data (energy fluctuation throughout day)
    wave_data = []
    for hour in range(24):
        if hour < wake_hour or hour >= 23:
            wave_data.append(0)  # Sleeping hours
        else:
            hours_awake = hour - wake_hour
            # Ultradian wave: peaks every 90 mins, troughs every 45 mins between peaks
            cycle_position = (hours_awake * 60) % 90  # Position within 90-min cycle
            # Sinusoidal wave pattern
            wave_value = 50 + 30 * math.cos(math.pi * cycle_position / 45)
            # Apply circadian envelope (gradual decline)
            circadian_factor = 1 - (hours_awake / 32)  # Slow decline
            wave_data.append(max(20, min(100, wave_value * circadian_factor)))

    return {
        'sleep_cycles_complete': sleep_cycles_complete,
        'sleep_cycles_partial': sleep_cycles_partial,
        'sleep_cycles_quality': 'Optimal' if sleep_cycles_complete >= 5 else ('Good' if sleep_cycles_complete >= 4 else 'Suboptimal'),
        'focus_blocks': focus_blocks[:6],  # Limit to 6 blocks
        'break_times': break_times[:5],  # Limit to 5 breaks
        'wave_data': wave_data,
        'next_peak_in': 90 - ((datetime.now().hour - wake_hour) * 60 + datetime.now().minute) % 90
    }


def get_data_from_db():
    """Fetch all required data from the database."""
    conn = sqlite3.connect('productivity.db')
    cursor = conn.cursor()

    # Get latest wellness data
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

    date_str = latest[0]

    # Get hourly scores
    cursor.execute('''
        SELECT ps.hour, ps.score
        FROM productivity_scores ps
        JOIN wellness_records wr ON ps.wellness_record_id = wr.id
        WHERE wr.date = ?
        ORDER BY ps.hour
    ''', (date_str,))
    hourly_scores = cursor.fetchall()

    # Get weekly data
    cursor.execute('''
        SELECT date, sleep_hours, sleep_quality, sleep_debt
        FROM wellness_records
        ORDER BY date DESC
        LIMIT 7
    ''')
    weekly_data = cursor.fetchall()

    conn.close()

    # Process data
    scores_dict = {h: s for h, s in hourly_scores}

    # Calculate energy phases
    morning = [scores_dict.get(h, 0) for h in range(6, 12)]
    midday = [scores_dict.get(h, 0) for h in range(12, 14)]
    afternoon = [scores_dict.get(h, 0) for h in range(14, 18)]
    evening = [scores_dict.get(h, 0) for h in range(18, 22)]

    phases = {
        'morning': sum(morning) / len(morning) if morning else 0,
        'midday': sum(midday) / len(midday) if midday else 0,
        'afternoon': sum(afternoon) / len(afternoon) if afternoon else 0,
        'evening': sum(evening) / len(evening) if evening else 0
    }

    # Find peak windows
    peak_hours = sorted(
        [(h, scores_dict.get(h, 0)) for h in range(6, 22) if scores_dict.get(h, 0) > 65],
        key=lambda x: -x[1]
    )[:3]

    # Parse sleep times
    sleep_start = latest[4]
    sleep_end = latest[5]

    bed_time = "--:--"
    wake_time = "--:--"
    wake_datetime = None

    if sleep_start:
        try:
            dt = datetime.fromisoformat(sleep_start.replace('Z', '+00:00'))
            bed_time = dt.strftime("%H:%M")
        except:
            pass

    if sleep_end:
        try:
            dt = datetime.fromisoformat(sleep_end.replace('Z', '+00:00'))
            wake_time = dt.strftime("%H:%M")
            wake_datetime = dt
        except:
            pass

    # Calculate ultradian rhythm data
    sleep_hours = latest[1] or 0
    sleep_debt = latest[3] or 0
    ultradian = calculate_ultradian_cycles(wake_time, sleep_hours)

    # Calculate optimal bedtime
    optimal_bedtime = calculate_optimal_bedtime(wake_time, sleep_debt, sleep_hours)

    return {
        'date': date_str,
        'sleep_hours': latest[1] or 0,
        'sleep_quality': latest[2] or 0,
        'sleep_debt': latest[3] or 0,
        'bed_time': bed_time,
        'wake_time': wake_time,
        'hourly_scores': [scores_dict.get(h, 0) for h in range(24)],
        'phases': phases,
        'peak_hours': peak_hours,
        'weekly_data': list(reversed(weekly_data)),
        'ultradian': ultradian,
        'optimal_bedtime': optimal_bedtime
    }


def get_bar_class(hours):
    """Get CSS class for sleep bar based on hours."""
    if hours >= 8:
        return 'excellent'
    elif hours >= 7:
        return 'good'
    elif hours >= 6:
        return 'moderate'
    else:
        return 'poor'


def get_heatmap_level(score):
    """Get heatmap level (1-5) based on score."""
    if score >= 80:
        return 5
    elif score >= 65:
        return 4
    elif score >= 50:
        return 3
    elif score >= 35:
        return 2
    else:
        return 1


def get_debt_class(debt):
    """Get CSS class for debt based on hours."""
    if debt <= 0:
        return 'good'
    elif debt <= 5:
        return 'warning'
    else:
        return 'danger'


def get_debt_status(debt):
    """Get status text for debt."""
    if debt <= 0:
        return 'Fully Recovered'
    elif debt <= 2:
        return 'Minor Debt'
    elif debt <= 5:
        return 'Moderate Debt'
    else:
        return 'High Debt - Rest Needed'


def generate_html(data):
    """Generate the HTML dashboard."""

    # Format date
    date_obj = datetime.strptime(data['date'], '%Y-%m-%d')
    formatted_date = date_obj.strftime('%B %d, %Y')

    # Calculate sleep score (quality * 20 to get percentage)
    sleep_score = int((data['sleep_quality'] / 5) * 100) if data['sleep_quality'] else 0

    # Find peak phase
    phases = data['phases']
    peak_phase = max(phases, key=phases.get)

    # Generate weekly bars HTML
    weekly_bars_html = ""
    for row in data['weekly_data']:
        date, hours, quality, debt = row
        hours = hours or 0
        bar_class = get_bar_class(hours)
        date_label = datetime.strptime(date, '%Y-%m-%d').strftime('%b %d')
        height = min(100, (hours / 12) * 100)
        weekly_bars_html += f'''
                    <div class="day-column">
                        <div class="day-bar-container">
                            <div class="day-bar {bar_class}" style="height: {height}%" data-hours="{hours:.1f}h"></div>
                        </div>
                        <span class="day-label">{date_label}</span>
                    </div>'''

    # Generate heatmap cells HTML
    heatmap_cells_html = ""
    for hour in range(24):
        score = data['hourly_scores'][hour]
        level = get_heatmap_level(score)
        heatmap_cells_html += f'                    <div class="heatmap-cell level-{level}">{int(score)}</div>\n'

    # Generate peak windows HTML
    peak_windows_html = ""
    labels = ['Peak Performance', 'High Focus', 'Strong Energy']
    for i, (hour, score) in enumerate(data['peak_hours'][:3]):
        peak_windows_html += f'''
                    <div class="window-item">
                        <span class="window-rank">#{i+1}</span>
                        <div class="window-info">
                            <div class="window-time">{hour:02d}:00 - {hour+1:02d}:00</div>
                            <div class="window-label">{labels[i]}</div>
                        </div>
                        <span class="window-score">{int(score)}%</span>
                    </div>'''

    # Debt styling
    debt_class = get_debt_class(data['sleep_debt'])
    debt_status = get_debt_status(data['sleep_debt'])

    # Phase peak badges
    def phase_badge(phase_name):
        if phase_name == peak_phase:
            return '<span class="peak-badge">PEAK</span>'
        return ''

    # Calculate progress offset for circular chart
    circumference = 2 * 3.14159 * 80
    offset = circumference - (sleep_score / 100) * circumference

    # Hourly scores as JSON for chart
    hourly_json = json.dumps(data['hourly_scores'])

    # Optimal bedtime data
    bedtime_data = data['optimal_bedtime']
    ideal_bedtime = bedtime_data['ideal_bedtime']
    ideal_cycles = bedtime_data['ideal_cycles']
    target_wake = bedtime_data['target_wake']
    recovery_note = bedtime_data['recovery_note']

    # Generate bedtime windows HTML
    bedtime_windows_html = ""
    for window in bedtime_data['windows']:
        rec_class = "recommended" if window['recommended'] else ""
        rec_badge = '<span class="rec-badge">Best</span>' if window['recommended'] else ""
        bedtime_windows_html += f'''
                    <div class="bedtime-option {rec_class}">
                        <div>
                            <span class="time">{window['time']}</span>
                            <span class="cycles">{window['label']}</span>
                        </div>
                        {rec_badge}
                    </div>'''

    # Generate sleep gates HTML
    sleep_gates_html = ""
    for gate in bedtime_data['sleep_gates']:
        sleep_gates_html += f'\n                        <span class="gate-pill">{gate}</span>'

    # Ultradian rhythm data
    ultradian = data['ultradian']
    ultradian_cycles = ultradian['sleep_cycles_complete']
    ultradian_quality = ultradian['sleep_cycles_quality']
    next_peak_mins = max(0, ultradian['next_peak_in'])
    ultradian_wave_json = json.dumps(ultradian['wave_data'])

    # Generate focus blocks HTML
    focus_blocks_html = ""
    for block in ultradian['focus_blocks']:
        focus_blocks_html += f'''
                                <div class="focus-block {block['type']}">
                                    <span class="block-num">#{block['block_num']}</span>
                                    <div class="block-time">{block['start']} - {block['end']}</div>
                                    <div class="block-type">{block['type'].replace('-', ' ')}</div>
                                </div>'''

    # Generate break times HTML
    break_times_html = ""
    for brk in ultradian['break_times']:
        icon = "☕" if brk['type'] == 'short' else "🚶"
        break_times_html += f'''
                                <div class="break-pill">
                                    <span class="break-icon">{icon}</span>
                                    <span class="break-time">{brk['time']}</span>
                                    <span class="break-duration">{brk['duration']}min</span>
                                </div>'''

    # Generate ultradian insight
    if ultradian_cycles >= 5:
        ultradian_insight = f"Excellent! You completed {ultradian_cycles} full 90-minute sleep cycles, allowing optimal memory consolidation and hormone regulation. Your energy should follow a natural 90-minute wave pattern throughout the day. Schedule demanding cognitive tasks during the first 60 minutes of each focus block, then allow 15-20 minutes for a natural energy dip before the next peak."
    elif ultradian_cycles >= 4:
        ultradian_insight = f"Good recovery with {ultradian_cycles} complete sleep cycles. Your ultradian rhythm will support focused work in 90-minute blocks. Watch for energy dips around mid-cycle (45 min) - these are natural rest points, not productivity failures. Consider a short 10-15 minute break or task switch during these troughs."
    else:
        ultradian_insight = f"With only {ultradian_cycles} complete sleep cycles, your ultradian rhythm may be less stable today. Consider shorter 45-60 minute focus blocks instead of full 90-minute sessions. Take more frequent breaks and prioritize high-priority tasks during your natural morning peak (first 2-3 hours after waking)."

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Productivity Intelligence Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}

        body {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            color: #ffffff;
            padding: 20px;
        }}

        .dashboard {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}

        .header h1 {{
            font-size: 2.5rem;
            font-weight: 300;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .header .date {{
            color: #8892b0;
            font-size: 1.1rem;
            margin-top: 5px;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(12, 1fr);
            gap: 20px;
        }}

        .card {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}

        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }}

        .card-title {{
            font-size: 0.9rem;
            color: #8892b0;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 15px;
        }}

        .sleep-score {{ grid-column: span 3; text-align: center; }}
        .sleep-debt {{ grid-column: span 3; }}
        .optimal-bedtime {{ grid-column: span 6; }}
        .energy-flow {{ grid-column: span 6; }}
        .energy-phases {{ grid-column: span 6; }}
        .peak-windows {{ grid-column: span 6; }}
        .ultradian-rhythm {{ grid-column: span 12; }}
        .weekly-trend {{ grid-column: span 6; }}
        .heatmap {{ grid-column: span 12; }}

        .circular-progress {{
            position: relative;
            width: 180px;
            height: 180px;
            margin: 0 auto 20px;
        }}

        .circular-progress svg {{ transform: rotate(-90deg); }}
        .circular-progress .bg {{ fill: none; stroke: rgba(255, 255, 255, 0.1); stroke-width: 12; }}
        .circular-progress .progress {{
            fill: none;
            stroke: url(#gradient);
            stroke-width: 12;
            stroke-linecap: round;
            stroke-dasharray: {circumference:.0f};
            stroke-dashoffset: {offset:.0f};
        }}

        .circular-progress .score-value {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
        }}

        .circular-progress .score-value .number {{
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .circular-progress .score-value .label {{ font-size: 0.9rem; color: #8892b0; }}

        .sleep-details {{ display: flex; justify-content: space-around; margin-top: 15px; }}
        .sleep-detail {{ text-align: center; }}
        .sleep-detail .value {{ font-size: 1.4rem; font-weight: 600; color: #a78bfa; }}
        .sleep-detail .label {{ font-size: 0.75rem; color: #8892b0; margin-top: 3px; }}

        .debt-indicator {{ text-align: center; padding: 20px 0; }}
        .debt-value {{ font-size: 3.5rem; font-weight: 700; }}
        .debt-value.good {{ color: #10b981; }}
        .debt-value.warning {{ color: #f59e0b; }}
        .debt-value.danger {{ color: #ef4444; }}
        .debt-label {{ font-size: 1rem; color: #8892b0; margin-top: 5px; }}
        .debt-status {{ display: inline-block; padding: 8px 20px; border-radius: 20px; font-size: 0.85rem; margin-top: 15px; }}
        .debt-status.good {{ background: rgba(16, 185, 129, 0.2); color: #10b981; }}
        .debt-status.warning {{ background: rgba(245, 158, 11, 0.2); color: #f59e0b; }}
        .debt-status.danger {{ background: rgba(239, 68, 68, 0.2); color: #ef4444; }}

        /* Optimal Bedtime Styles */
        .bedtime-main {{ text-align: center; padding: 15px 0; margin-bottom: 20px; }}
        .bedtime-value {{ font-size: 3.5rem; font-weight: 700; background: linear-gradient(135deg, #6366f1, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}
        .bedtime-label {{ font-size: 1rem; color: #8892b0; margin-top: 5px; }}
        .bedtime-note {{ display: inline-block; padding: 8px 16px; background: rgba(99, 102, 241, 0.15); border-radius: 20px; font-size: 0.8rem; color: #a78bfa; margin-top: 12px; }}

        .bedtime-windows {{ margin-top: 15px; }}
        .window-title {{ font-size: 0.8rem; color: #8892b0; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px; }}
        .bedtime-option {{ display: flex; align-items: center; justify-content: space-between; padding: 12px 15px; background: rgba(255, 255, 255, 0.03); border-radius: 10px; margin-bottom: 8px; border-left: 3px solid transparent; transition: all 0.3s; }}
        .bedtime-option:hover {{ background: rgba(255, 255, 255, 0.06); }}
        .bedtime-option.recommended {{ border-left-color: #10b981; background: rgba(16, 185, 129, 0.08); }}
        .bedtime-option .time {{ font-size: 1.3rem; font-weight: 600; color: #fff; }}
        .bedtime-option .cycles {{ font-size: 0.8rem; color: #8892b0; }}
        .bedtime-option .rec-badge {{ font-size: 0.65rem; background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 3px 8px; border-radius: 10px; text-transform: uppercase; letter-spacing: 0.5px; }}

        .sleep-gates {{ margin-top: 20px; padding-top: 15px; border-top: 1px solid rgba(255, 255, 255, 0.1); }}
        .gates-title {{ font-size: 0.8rem; color: #8892b0; margin-bottom: 10px; display: flex; align-items: center; gap: 8px; }}
        .gates-title .info-icon {{ font-size: 0.9rem; cursor: help; }}
        .gate-pills {{ display: flex; gap: 8px; flex-wrap: wrap; }}
        .gate-pill {{ background: rgba(139, 92, 246, 0.15); color: #a78bfa; padding: 6px 14px; border-radius: 15px; font-size: 0.85rem; font-weight: 500; }}

        .chart-container {{ height: 200px; margin-top: 10px; }}

        .phase-bars {{ margin-top: 15px; }}
        .phase-bar {{ margin-bottom: 18px; }}
        .phase-header {{ display: flex; justify-content: space-between; margin-bottom: 8px; }}
        .phase-name {{ display: flex; align-items: center; gap: 8px; font-size: 0.95rem; }}
        .phase-icon {{ font-size: 1.2rem; }}
        .phase-value {{ font-weight: 600; color: #a78bfa; }}
        .phase-track {{ height: 10px; background: rgba(255, 255, 255, 0.1); border-radius: 5px; overflow: hidden; }}
        .phase-fill {{ height: 100%; border-radius: 5px; transition: width 1s ease-out; }}
        .phase-fill.morning {{ background: linear-gradient(90deg, #fbbf24, #f59e0b); }}
        .phase-fill.midday {{ background: linear-gradient(90deg, #fb923c, #ea580c); }}
        .phase-fill.afternoon {{ background: linear-gradient(90deg, #a78bfa, #7c3aed); }}
        .phase-fill.evening {{ background: linear-gradient(90deg, #60a5fa, #3b82f6); }}
        .peak-badge {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; font-size: 0.7rem; padding: 2px 8px; border-radius: 10px; margin-left: 8px; }}

        .window-list {{ margin-top: 15px; }}
        .window-item {{ display: flex; align-items: center; padding: 15px; background: rgba(255, 255, 255, 0.03); border-radius: 12px; margin-bottom: 10px; border-left: 4px solid; }}
        .window-item:nth-child(1) {{ border-left-color: #10b981; }}
        .window-item:nth-child(2) {{ border-left-color: #667eea; }}
        .window-item:nth-child(3) {{ border-left-color: #8b5cf6; }}
        .window-rank {{ font-size: 1.5rem; font-weight: 700; color: rgba(255, 255, 255, 0.3); margin-right: 15px; width: 30px; }}
        .window-info {{ flex: 1; }}
        .window-time {{ font-size: 1.1rem; font-weight: 600; }}
        .window-label {{ font-size: 0.8rem; color: #8892b0; }}
        .window-score {{ font-size: 1.8rem; font-weight: 700; background: linear-gradient(135deg, #10b981, #059669); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}

        .weekly-bars {{ display: flex; justify-content: space-between; align-items: flex-end; height: 150px; margin-top: 20px; padding: 0 10px; }}
        .day-column {{ display: flex; flex-direction: column; align-items: center; flex: 1; }}
        .day-bar-container {{ height: 120px; width: 100%; display: flex; align-items: flex-end; justify-content: center; }}
        .day-bar {{ width: 30px; border-radius: 8px 8px 0 0; transition: height 1s ease-out; position: relative; }}
        .day-bar::after {{ content: attr(data-hours); position: absolute; top: -25px; left: 50%; transform: translateX(-50%); font-size: 0.75rem; color: #8892b0; }}
        .day-bar.excellent {{ background: linear-gradient(180deg, #10b981, #059669); }}
        .day-bar.good {{ background: linear-gradient(180deg, #667eea, #764ba2); }}
        .day-bar.moderate {{ background: linear-gradient(180deg, #f59e0b, #d97706); }}
        .day-bar.poor {{ background: linear-gradient(180deg, #ef4444, #dc2626); }}
        .day-label {{ margin-top: 10px; font-size: 0.8rem; color: #8892b0; }}

        .heatmap-grid {{ display: grid; grid-template-columns: 60px repeat(24, 1fr); gap: 3px; margin-top: 15px; }}
        .heatmap-label {{ font-size: 0.75rem; color: #8892b0; display: flex; align-items: center; }}
        .heatmap-cell {{ aspect-ratio: 1; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 0.65rem; font-weight: 600; transition: transform 0.2s; }}
        .heatmap-cell:hover {{ transform: scale(1.2); z-index: 10; }}
        .heatmap-cell.level-5 {{ background: linear-gradient(135deg, #10b981, #059669); }}
        .heatmap-cell.level-4 {{ background: linear-gradient(135deg, #667eea, #764ba2); }}
        .heatmap-cell.level-3 {{ background: linear-gradient(135deg, #f59e0b, #d97706); }}
        .heatmap-cell.level-2 {{ background: linear-gradient(135deg, #f97316, #ea580c); }}
        .heatmap-cell.level-1 {{ background: linear-gradient(135deg, #ef4444, #dc2626); }}
        .hour-label {{ font-size: 0.7rem; color: #8892b0; text-align: center; }}

        .heatmap-legend {{ display: flex; justify-content: center; gap: 15px; margin-top: 15px; }}
        .legend-item {{ display: flex; align-items: center; gap: 5px; font-size: 0.75rem; color: #8892b0; }}
        .legend-color {{ width: 12px; height: 12px; border-radius: 3px; }}

        /* Ultradian Rhythm Styles */
        .ultradian-container {{ display: grid; grid-template-columns: 280px 1fr; gap: 30px; }}
        .ultradian-stats {{ display: flex; flex-direction: column; gap: 20px; }}
        .ultradian-stat {{ background: rgba(255, 255, 255, 0.03); border-radius: 15px; padding: 20px; border-left: 4px solid; }}
        .ultradian-stat.cycles {{ border-left-color: #a78bfa; }}
        .ultradian-stat.next-peak {{ border-left-color: #10b981; }}
        .ultradian-stat.quality {{ border-left-color: #f59e0b; }}
        .stat-label {{ font-size: 0.8rem; color: #8892b0; text-transform: uppercase; letter-spacing: 0.5px; }}
        .stat-value {{ font-size: 2.2rem; font-weight: 700; margin: 8px 0; }}
        .stat-value.cycles {{ background: linear-gradient(135deg, #a78bfa, #7c3aed); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}
        .stat-value.next-peak {{ color: #10b981; }}
        .stat-sublabel {{ font-size: 0.85rem; color: #a78bfa; }}

        .ultradian-visual {{ display: flex; flex-direction: column; }}
        .focus-blocks-container {{ margin-bottom: 20px; }}
        .focus-blocks {{ display: flex; gap: 8px; flex-wrap: wrap; }}
        .focus-block {{ flex: 1; min-width: 140px; background: rgba(255, 255, 255, 0.03); border-radius: 12px; padding: 15px; text-align: center; position: relative; overflow: hidden; }}
        .focus-block::before {{ content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px; }}
        .focus-block.peak::before {{ background: linear-gradient(90deg, #10b981, #059669); }}
        .focus-block.high::before {{ background: linear-gradient(90deg, #667eea, #764ba2); }}
        .focus-block.moderate::before {{ background: linear-gradient(90deg, #f59e0b, #d97706); }}
        .focus-block.wind-down::before {{ background: linear-gradient(90deg, #6366f1, #4f46e5); }}
        .block-time {{ font-size: 0.9rem; font-weight: 600; color: #fff; margin-bottom: 5px; }}
        .block-type {{ font-size: 0.7rem; color: #8892b0; text-transform: uppercase; letter-spacing: 0.5px; }}
        .block-num {{ position: absolute; top: 10px; right: 10px; font-size: 0.7rem; color: rgba(255, 255, 255, 0.3); font-weight: 700; }}

        .wave-chart-container {{ height: 120px; margin-top: 15px; }}

        .break-times {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 15px; }}
        .break-pill {{ display: flex; align-items: center; gap: 8px; background: rgba(255, 255, 255, 0.05); border-radius: 20px; padding: 8px 15px; }}
        .break-icon {{ font-size: 1rem; }}
        .break-time {{ font-size: 0.85rem; font-weight: 600; }}
        .break-duration {{ font-size: 0.7rem; color: #8892b0; }}

        .ultradian-insight {{ margin-top: 20px; background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1)); border-radius: 12px; padding: 15px 20px; border-left: 4px solid #667eea; }}
        .insight-title {{ font-size: 0.85rem; font-weight: 600; color: #667eea; margin-bottom: 8px; }}
        .insight-text {{ font-size: 0.9rem; color: #ccd6f6; line-height: 1.5; }}

        .footer {{ text-align: center; margin-top: 30px; padding: 20px; color: #8892b0; font-size: 0.85rem; }}

        @media (max-width: 1200px) {{
            .grid {{ grid-template-columns: repeat(6, 1fr); }}
            .sleep-score, .sleep-debt, .energy-flow, .energy-phases, .peak-windows, .weekly-trend {{ grid-column: span 3; }}
            .optimal-bedtime {{ grid-column: span 6; }}
            .heatmap, .ultradian-rhythm {{ grid-column: span 6; }}
            .ultradian-container {{ grid-template-columns: 1fr; }}
            .focus-blocks {{ justify-content: center; }}
        }}

        @media (max-width: 768px) {{
            .grid {{ grid-template-columns: 1fr; }}
            .sleep-score, .sleep-debt, .optimal-bedtime, .energy-flow, .energy-phases, .peak-windows, .weekly-trend, .heatmap, .ultradian-rhythm {{ grid-column: span 1; }}
            .ultradian-container {{ grid-template-columns: 1fr; gap: 20px; }}
            .ultradian-stats {{ flex-direction: row; flex-wrap: wrap; }}
            .ultradian-stat {{ flex: 1; min-width: 150px; }}
            .focus-block {{ min-width: 120px; }}
            .bedtime-value {{ font-size: 2.5rem; }}
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <header class="header">
            <h1>Productivity Intelligence</h1>
            <p class="date">{formatted_date}</p>
        </header>

        <div class="grid">
            <!-- Sleep Score -->
            <div class="card sleep-score">
                <h3 class="card-title">Sleep Quality</h3>
                <div class="circular-progress">
                    <svg width="180" height="180" viewBox="0 0 180 180">
                        <defs>
                            <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%" stop-color="#667eea" />
                                <stop offset="100%" stop-color="#764ba2" />
                            </linearGradient>
                        </defs>
                        <circle class="bg" cx="90" cy="90" r="80" />
                        <circle class="progress" cx="90" cy="90" r="80" />
                    </svg>
                    <div class="score-value">
                        <div class="number">{sleep_score}</div>
                        <div class="label">Score</div>
                    </div>
                </div>
                <div class="sleep-details">
                    <div class="sleep-detail">
                        <div class="value">{data['sleep_hours']:.1f}h</div>
                        <div class="label">Duration</div>
                    </div>
                    <div class="sleep-detail">
                        <div class="value">{data['bed_time']}</div>
                        <div class="label">Bedtime</div>
                    </div>
                    <div class="sleep-detail">
                        <div class="value">{data['wake_time']}</div>
                        <div class="label">Wake up</div>
                    </div>
                </div>
            </div>

            <!-- Sleep Debt -->
            <div class="card sleep-debt">
                <h3 class="card-title">Sleep Debt</h3>
                <div class="debt-indicator">
                    <div class="debt-value {debt_class}">{data['sleep_debt']:.1f}h</div>
                    <div class="debt-label">Accumulated Debt</div>
                    <span class="debt-status {debt_class}">{debt_status}</span>
                </div>
            </div>

            <!-- Optimal Bedtime -->
            <div class="card optimal-bedtime">
                <h3 class="card-title">Optimal Bedtime Tonight</h3>
                <div class="bedtime-main">
                    <div class="bedtime-value">{ideal_bedtime}</div>
                    <div class="bedtime-label">Recommended for {ideal_cycles} sleep cycles</div>
                    <div class="bedtime-note">{recovery_note}</div>
                </div>
                <div class="bedtime-windows">
                    <div class="window-title">Bedtime Options (for {target_wake} wake)</div>
{bedtime_windows_html}
                </div>
                <div class="sleep-gates">
                    <div class="gates-title">
                        <span>Natural Sleep Gates</span>
                        <span class="info-icon" title="Sleep gates are windows when melatonin peaks, making it easier to fall asleep">&#9432;</span>
                    </div>
                    <div class="gate-pills">{sleep_gates_html}
                    </div>
                </div>
            </div>

            <!-- Energy Flow Chart -->
            <div class="card energy-flow">
                <h3 class="card-title">24-Hour Energy Flow</h3>
                <div class="chart-container">
                    <canvas id="energyChart"></canvas>
                </div>
            </div>

            <!-- Energy Phases -->
            <div class="card energy-phases">
                <h3 class="card-title">Energy Phases</h3>
                <div class="phase-bars">
                    <div class="phase-bar">
                        <div class="phase-header">
                            <span class="phase-name">
                                <span class="phase-icon">🌅</span> Morning (6-12)
                                {phase_badge('morning')}
                            </span>
                            <span class="phase-value">{phases['morning']:.0f}%</span>
                        </div>
                        <div class="phase-track">
                            <div class="phase-fill morning" style="width: {phases['morning']}%"></div>
                        </div>
                    </div>
                    <div class="phase-bar">
                        <div class="phase-header">
                            <span class="phase-name">
                                <span class="phase-icon">☀️</span> Midday (12-14)
                                {phase_badge('midday')}
                            </span>
                            <span class="phase-value">{phases['midday']:.0f}%</span>
                        </div>
                        <div class="phase-track">
                            <div class="phase-fill midday" style="width: {phases['midday']}%"></div>
                        </div>
                    </div>
                    <div class="phase-bar">
                        <div class="phase-header">
                            <span class="phase-name">
                                <span class="phase-icon">🌤️</span> Afternoon (14-18)
                                {phase_badge('afternoon')}
                            </span>
                            <span class="phase-value">{phases['afternoon']:.0f}%</span>
                        </div>
                        <div class="phase-track">
                            <div class="phase-fill afternoon" style="width: {phases['afternoon']}%"></div>
                        </div>
                    </div>
                    <div class="phase-bar">
                        <div class="phase-header">
                            <span class="phase-name">
                                <span class="phase-icon">🌙</span> Evening (18-22)
                                {phase_badge('evening')}
                            </span>
                            <span class="phase-value">{phases['evening']:.0f}%</span>
                        </div>
                        <div class="phase-track">
                            <div class="phase-fill evening" style="width: {phases['evening']}%"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Peak Windows -->
            <div class="card peak-windows">
                <h3 class="card-title">Optimal Deep Work Windows</h3>
                <div class="window-list">{peak_windows_html}
                </div>
            </div>

            <!-- Ultradian Rhythm -->
            <div class="card ultradian-rhythm">
                <h3 class="card-title">Ultradian Rhythm Insights</h3>
                <div class="ultradian-container">
                    <div class="ultradian-stats">
                        <div class="ultradian-stat cycles">
                            <div class="stat-label">Sleep Cycles Completed</div>
                            <div class="stat-value cycles">{ultradian_cycles}</div>
                            <div class="stat-sublabel">{ultradian_quality} ({data['sleep_hours']:.1f}h / 1.5h per cycle)</div>
                        </div>
                        <div class="ultradian-stat next-peak">
                            <div class="stat-label">Next Energy Peak In</div>
                            <div class="stat-value next-peak">{next_peak_mins} min</div>
                            <div class="stat-sublabel">Based on 90-min ultradian cycle</div>
                        </div>
                        <div class="ultradian-stat quality">
                            <div class="stat-label">Recommended Breaks</div>
                            <div class="break-times">{break_times_html}
                            </div>
                        </div>
                    </div>
                    <div class="ultradian-visual">
                        <div class="focus-blocks-container">
                            <div class="stat-label" style="margin-bottom: 12px;">90-Minute Focus Blocks (from wake time {data['wake_time']})</div>
                            <div class="focus-blocks">{focus_blocks_html}
                            </div>
                        </div>
                        <div class="stat-label" style="margin-top: 20px; margin-bottom: 10px;">Ultradian Energy Wave</div>
                        <div class="wave-chart-container">
                            <canvas id="ultradianWaveChart"></canvas>
                        </div>
                        <div class="ultradian-insight">
                            <div class="insight-title">Ultradian Rhythm Insight</div>
                            <div class="insight-text">{ultradian_insight}</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Weekly Trend -->
            <div class="card weekly-trend">
                <h3 class="card-title">Weekly Sleep Trend</h3>
                <div class="weekly-bars">{weekly_bars_html}
                </div>
            </div>

            <!-- 24-Hour Heatmap -->
            <div class="card heatmap">
                <h3 class="card-title">Energy Heatmap</h3>
                <div class="heatmap-grid">
                    <div class="heatmap-label"></div>
                    <div class="hour-label">0</div><div class="hour-label">1</div><div class="hour-label">2</div>
                    <div class="hour-label">3</div><div class="hour-label">4</div><div class="hour-label">5</div>
                    <div class="hour-label">6</div><div class="hour-label">7</div><div class="hour-label">8</div>
                    <div class="hour-label">9</div><div class="hour-label">10</div><div class="hour-label">11</div>
                    <div class="hour-label">12</div><div class="hour-label">13</div><div class="hour-label">14</div>
                    <div class="hour-label">15</div><div class="hour-label">16</div><div class="hour-label">17</div>
                    <div class="hour-label">18</div><div class="hour-label">19</div><div class="hour-label">20</div>
                    <div class="hour-label">21</div><div class="hour-label">22</div><div class="hour-label">23</div>
                    <div class="heatmap-label">Today</div>
{heatmap_cells_html}
                </div>
                <div class="heatmap-legend">
                    <div class="legend-item"><div class="legend-color" style="background: linear-gradient(135deg, #ef4444, #dc2626)"></div><span>&lt;35%</span></div>
                    <div class="legend-item"><div class="legend-color" style="background: linear-gradient(135deg, #f97316, #ea580c)"></div><span>35-50%</span></div>
                    <div class="legend-item"><div class="legend-color" style="background: linear-gradient(135deg, #f59e0b, #d97706)"></div><span>50-65%</span></div>
                    <div class="legend-item"><div class="legend-color" style="background: linear-gradient(135deg, #667eea, #764ba2)"></div><span>65-80%</span></div>
                    <div class="legend-item"><div class="legend-color" style="background: linear-gradient(135deg, #10b981, #059669)"></div><span>80%+</span></div>
                </div>
            </div>
        </div>

        <footer class="footer">
            Productivity Intelligence Dashboard | Data synced from Amazfit Watch via Google Fit | Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </footer>
    </div>

    <script>
        const hourlyData = {hourly_json};
        const ctx = document.getElementById('energyChart').getContext('2d');
        const gradient = ctx.createLinearGradient(0, 0, 0, 200);
        gradient.addColorStop(0, 'rgba(102, 126, 234, 0.8)');
        gradient.addColorStop(1, 'rgba(118, 75, 162, 0.1)');

        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: ['0','1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20','21','22','23'],
                datasets: [{{
                    label: 'Energy Score',
                    data: hourlyData,
                    fill: true,
                    backgroundColor: gradient,
                    borderColor: '#667eea',
                    borderWidth: 3,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 6,
                    pointHoverBackgroundColor: '#667eea',
                    pointHoverBorderColor: '#fff',
                    pointHoverBorderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        backgroundColor: 'rgba(26, 26, 46, 0.9)',
                        titleColor: '#fff',
                        bodyColor: '#a78bfa',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: false,
                        callbacks: {{
                            title: function(context) {{ return context[0].label + ':00'; }},
                            label: function(context) {{ return 'Energy: ' + context.raw + '%'; }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        grid: {{ color: 'rgba(255, 255, 255, 0.05)' }},
                        ticks: {{ color: '#8892b0', font: {{ size: 10 }} }}
                    }},
                    y: {{
                        min: 0, max: 100,
                        grid: {{ color: 'rgba(255, 255, 255, 0.05)' }},
                        ticks: {{ color: '#8892b0', font: {{ size: 10 }}, callback: function(v) {{ return v + '%'; }} }}
                    }}
                }}
            }}
        }});

        // Ultradian Wave Chart
        const waveData = {ultradian_wave_json};
        const waveCtx = document.getElementById('ultradianWaveChart').getContext('2d');
        const waveGradient = waveCtx.createLinearGradient(0, 0, 0, 120);
        waveGradient.addColorStop(0, 'rgba(16, 185, 129, 0.6)');
        waveGradient.addColorStop(0.5, 'rgba(102, 126, 234, 0.4)');
        waveGradient.addColorStop(1, 'rgba(118, 75, 162, 0.1)');

        new Chart(waveCtx, {{
            type: 'line',
            data: {{
                labels: ['0','1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20','21','22','23'],
                datasets: [{{
                    label: 'Ultradian Energy Wave',
                    data: waveData,
                    fill: true,
                    backgroundColor: waveGradient,
                    borderColor: '#10b981',
                    borderWidth: 2,
                    tension: 0.5,
                    pointRadius: 0,
                    pointHoverRadius: 5,
                    pointHoverBackgroundColor: '#10b981',
                    pointHoverBorderColor: '#fff',
                    pointHoverBorderWidth: 2
                }},
                {{
                    label: 'Actual Energy',
                    data: hourlyData,
                    fill: false,
                    borderColor: 'rgba(167, 139, 250, 0.5)',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    tension: 0.4,
                    pointRadius: 0
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: true,
                        position: 'top',
                        align: 'end',
                        labels: {{
                            color: '#8892b0',
                            font: {{ size: 10 }},
                            boxWidth: 12,
                            padding: 10,
                            usePointStyle: true
                        }}
                    }},
                    tooltip: {{
                        backgroundColor: 'rgba(26, 26, 46, 0.9)',
                        titleColor: '#fff',
                        bodyColor: '#10b981',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: true,
                        callbacks: {{
                            title: function(context) {{ return context[0].label + ':00'; }},
                            label: function(context) {{
                                const label = context.dataset.label;
                                return label + ': ' + Math.round(context.raw) + '%';
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        grid: {{ color: 'rgba(255, 255, 255, 0.03)' }},
                        ticks: {{ color: '#8892b0', font: {{ size: 9 }} }}
                    }},
                    y: {{
                        min: 0, max: 100,
                        grid: {{ color: 'rgba(255, 255, 255, 0.03)' }},
                        ticks: {{ color: '#8892b0', font: {{ size: 9 }}, stepSize: 25 }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>'''

    return html


def main():
    """Generate and open the dashboard."""
    print("Fetching data from database...")
    data = get_data_from_db()

    if not data:
        print("No data found in database!")
        return

    print(f"Generating dashboard for {data['date']}...")
    html = generate_html(data)

    # Save to file
    output_path = os.path.join(os.path.dirname(__file__), 'dashboard.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Dashboard saved to: {output_path}")

    # Open in browser
    webbrowser.open('file://' + os.path.realpath(output_path))
    print("Dashboard opened in browser!")


if __name__ == '__main__':
    main()

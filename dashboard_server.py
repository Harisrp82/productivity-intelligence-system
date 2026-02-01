"""
Real-time Productivity Dashboard Server

A Flask server that provides:
- API endpoints for live data from productivity.db
- Serves the live dashboard HTML
- Auto-updates every time the page fetches data

Run with: python dashboard_server.py
Then open: http://localhost:5000
"""

import sqlite3
import json
import math
from datetime import datetime
from flask import Flask, jsonify, send_file, Response
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'productivity.db')


def get_db_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def calculate_optimal_bedtime(wake_time_str, sleep_debt, avg_sleep_hours):
    """Calculate optimal bedtime windows based on wake time and sleep needs."""
    if wake_time_str == "--:--":
        wake_hour, wake_minute = 7, 0
    else:
        try:
            parts = wake_time_str.split(':')
            wake_hour, wake_minute = int(parts[0]), int(parts[1])
        except:
            wake_hour, wake_minute = 7, 0

    bedtime_windows = []
    cycle_options = [
        (5, "5 cycles - 7.5h"),
        (5.5, "5.5 cycles - 8.25h"),
        (6, "6 cycles - 9h")
    ]

    for cycles, label in cycle_options:
        sleep_duration_mins = int(cycles * 90)
        bed_minute = wake_minute - (sleep_duration_mins % 60)
        bed_hour = wake_hour - (sleep_duration_mins // 60)

        if bed_minute < 0:
            bed_minute += 60
            bed_hour -= 1
        if bed_hour < 0:
            bed_hour += 24

        fall_asleep_mins = 15
        bed_minute -= fall_asleep_mins
        if bed_minute < 0:
            bed_minute += 60
            bed_hour -= 1
        if bed_hour < 0:
            bed_hour += 24

        bedtime_str = f"{bed_hour:02d}:{bed_minute:02d}"
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

    if sleep_debt > 5:
        ideal_cycles = 6
        recovery_note = "High sleep debt - aim for 6 full cycles to recover"
    elif sleep_debt > 2:
        ideal_cycles = 5.5
        recovery_note = "Moderate debt - extra half cycle recommended"
    else:
        ideal_cycles = 5
        recovery_note = "Well rested - 5 cycles maintains optimal recovery"

    ideal_duration_mins = int(ideal_cycles * 90) + 15
    ideal_bed_minute = wake_minute - (ideal_duration_mins % 60)
    ideal_bed_hour = wake_hour - (ideal_duration_mins // 60)

    if ideal_bed_minute < 0:
        ideal_bed_minute += 60
        ideal_bed_hour -= 1
    if ideal_bed_hour < 0:
        ideal_bed_hour += 24

    sleep_gates = []
    gate_start = 21
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
    if wake_time_str == "--:--":
        wake_hour, wake_minute = 7, 0
    else:
        try:
            parts = wake_time_str.split(':')
            wake_hour, wake_minute = int(parts[0]), int(parts[1])
        except:
            wake_hour, wake_minute = 7, 0

    sleep_cycles_complete = int(sleep_hours / 1.5)

    focus_blocks = []
    current_hour = wake_hour
    current_minute = wake_minute

    for i in range(8):
        block_start = f"{current_hour:02d}:{current_minute:02d}"
        end_minute = current_minute + 90
        end_hour = current_hour + (end_minute // 60)
        end_minute = end_minute % 60

        if end_hour >= 24:
            end_hour = end_hour % 24

        block_end = f"{end_hour:02d}:{end_minute:02d}"

        if i < 2:
            block_type = "peak"
        elif i < 4:
            block_type = "high"
        elif i < 6:
            block_type = "moderate"
        else:
            block_type = "wind-down"

        base_energy = 75 - (i * 5)

        focus_blocks.append({
            'start': block_start,
            'end': block_end,
            'type': block_type,
            'block_num': i + 1,
            'energy': max(40, base_energy)
        })

        current_minute = current_minute + 110
        current_hour = current_hour + (current_minute // 60)
        current_minute = current_minute % 60

        if current_hour >= 24:
            break

    break_times = []
    current_hour = wake_hour
    current_minute = wake_minute + 90

    for i in range(6):
        if current_minute >= 60:
            current_hour += current_minute // 60
            current_minute = current_minute % 60

        if current_hour >= 22:
            break

        break_times.append({
            'time': f"{current_hour:02d}:{current_minute:02d}",
            'duration': 15 if i % 2 == 0 else 20,
            'type': 'short' if i % 2 == 0 else 'long'
        })

        current_minute += 110

    wave_data = []
    for hour in range(24):
        if hour < wake_hour or hour >= 23:
            wave_data.append(0)
        else:
            hours_awake = hour - wake_hour
            cycle_position = (hours_awake * 60) % 90
            wave_value = 50 + 30 * math.cos(math.pi * cycle_position / 45)
            circadian_factor = 1 - (hours_awake / 32)
            wave_data.append(max(20, min(100, wave_value * circadian_factor)))

    next_peak_in = 90 - ((datetime.now().hour - wake_hour) * 60 + datetime.now().minute) % 90

    return {
        'sleep_cycles_complete': sleep_cycles_complete,
        'sleep_cycles_quality': 'Optimal' if sleep_cycles_complete >= 5 else ('Good' if sleep_cycles_complete >= 4 else 'Suboptimal'),
        'focus_blocks': focus_blocks[:6],
        'break_times': break_times[:5],
        'wave_data': wave_data,
        'next_peak_in': max(0, next_peak_in)
    }


@app.route('/api/dashboard-data')
def get_dashboard_data():
    """Get all dashboard data as JSON."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get latest wellness data
        cursor.execute('''
            SELECT id, date, sleep_hours, sleep_quality, sleep_debt, sleep_start, sleep_end
            FROM wellness_records
            ORDER BY date DESC
            LIMIT 1
        ''')
        latest = cursor.fetchone()

        if not latest:
            conn.close()
            return jsonify({'error': 'No data found in database'}), 404

        record_id = latest['id']
        date_str = latest['date']

        # Get hourly scores
        cursor.execute('''
            SELECT hour, score, circadian_component, recovery_component
            FROM productivity_scores
            WHERE wellness_record_id = ?
            ORDER BY hour
        ''', (record_id,))
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
        scores_dict = {row['hour']: row['score'] for row in hourly_scores}
        hourly_list = [scores_dict.get(h, 0) for h in range(24)]

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
        bed_time = "--:--"
        wake_time = "--:--"

        if latest['sleep_start']:
            try:
                dt = datetime.fromisoformat(str(latest['sleep_start']).replace('Z', '+00:00'))
                bed_time = dt.strftime("%H:%M")
            except:
                pass

        if latest['sleep_end']:
            try:
                dt = datetime.fromisoformat(str(latest['sleep_end']).replace('Z', '+00:00'))
                wake_time = dt.strftime("%H:%M")
            except:
                pass

        sleep_hours = latest['sleep_hours'] or 0
        sleep_debt = latest['sleep_debt'] or 0
        sleep_quality = latest['sleep_quality'] or 0

        # Calculate ultradian and bedtime data
        ultradian = calculate_ultradian_cycles(wake_time, sleep_hours)
        optimal_bedtime = calculate_optimal_bedtime(wake_time, sleep_debt, sleep_hours)

        # Format weekly data
        weekly_formatted = []
        for row in reversed(list(weekly_data)):
            weekly_formatted.append({
                'date': row['date'],
                'sleep_hours': row['sleep_hours'] or 0,
                'sleep_quality': row['sleep_quality'] or 0,
                'sleep_debt': row['sleep_debt'] or 0
            })

        # Build response
        data = {
            'timestamp': datetime.now().isoformat(),
            'date': date_str,
            'sleep_hours': sleep_hours,
            'sleep_quality': sleep_quality,
            'sleep_debt': sleep_debt,
            'bed_time': bed_time,
            'wake_time': wake_time,
            'hourly_scores': hourly_list,
            'phases': phases,
            'peak_hours': [{'hour': h, 'score': s} for h, s in peak_hours],
            'weekly_data': weekly_formatted,
            'ultradian': ultradian,
            'optimal_bedtime': optimal_bedtime
        }

        return jsonify(data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'database': os.path.exists(DB_PATH)
    })


@app.route('/')
def serve_dashboard():
    """Serve the live dashboard HTML."""
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dashboard_live.html')
    if os.path.exists(html_path):
        return send_file(html_path)
    else:
        return "Dashboard not found. Please run the setup.", 404


@app.route('/ultradian')
def serve_ultradian():
    """Serve the ultradian rhythm page."""
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ultradian_live.html')
    if os.path.exists(html_path):
        return send_file(html_path)
    else:
        return "Ultradian dashboard not found.", 404


if __name__ == '__main__':
    print("=" * 50)
    print("  Productivity Dashboard Server")
    print("=" * 50)
    print(f"\n  Database: {DB_PATH}")
    print(f"  Database exists: {os.path.exists(DB_PATH)}")
    print("\n  Dashboard: http://localhost:5000")
    print("  Ultradian: http://localhost:5000/ultradian")
    print("  API:       http://localhost:5000/api/dashboard-data")
    print("\n  Press Ctrl+C to stop the server")
    print("=" * 50)

    app.run(host='0.0.0.0', port=5000, debug=True)

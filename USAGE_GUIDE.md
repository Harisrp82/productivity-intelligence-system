# Productivity Intelligence System - Usage Guide

A step-by-step guide to run this project independently via terminal.

---

## Table of Contents
1. [First-Time Setup](#first-time-setup)
2. [Daily Usage](#daily-usage)
3. [Common Commands](#common-commands)
4. [Customization](#customization)
5. [Troubleshooting](#troubleshooting)

---

## First-Time Setup

### Step 1: Open Terminal
```bash
# Windows: Open Command Prompt or PowerShell
# Navigate to project folder
cd "D:\Projects\Amazfit Watch Project"
```

### Step 2: Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
```bash
# Copy example file
copy .env.example .env

# Edit .env file with your settings:
# - GROK_API_KEY=your_grok_api_key
# - GOOGLE_DOC_ID=your_google_doc_id
# - TIMEZONE=Asia/Kolkata (or your timezone)
```

### Step 5: Setup Google Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project or select existing one
3. Enable these APIs:
   - Google Docs API
   - Google Fitness API
4. Create OAuth 2.0 credentials (Desktop App)
5. Download `credentials.json` and place in project root

### Step 6: First Run (Authenticate)
```bash
python daily_workflow.py
```
- A browser window will open for Google authentication
- Grant permissions for Google Fit and Google Docs
- Tokens will be saved for future use

---

## Daily Usage

### Run the Complete Workflow
```bash
cd "D:\Projects\Amazfit Watch Project"
python daily_workflow.py
```

This will:
1. Fetch your sleep/wellness data from Google Fit
2. Calculate productivity scores based on your wake time
3. Generate AI insights using Grok
4. Send the report to your Google Doc

### Expected Output
```
Starting Productivity Intelligence System - Daily Workflow
================================================================================
Step 1: Collecting wellness data
Using Zepp/Amazfit sleep data (preferred source)
Sleep data for 2026-01-15: 7.8 hours

Step 2: Calculating productivity scores

Step 3: Storing data in database

Step 4: Generating AI insights
Step 4a: Analyzing optimal deep work windows

Step 5: Storing report in database

Step 6: Delivering report to Google Docs
Successfully delivered report to Google Docs

Daily workflow completed successfully for 2026-01-15
```

---

## Common Commands

### Check Your Sleep Data
```bash
python -c "
from datetime import datetime
from src.data_collection import GoogleFitCollector

collector = GoogleFitCollector()
collector.authenticate()
data = collector.get_sleep_data(datetime.now())
print(f'Sleep: {data[\"sleep_hours\"]} hours')
print(f'Start: {data[\"sleep_start\"]}')
print(f'End: {data[\"sleep_end\"]}')
"
```

### View Energy Flow Prediction
```bash
python -c "
from datetime import time
from src.scoring.circadian_model import CircadianModel

# Change wake_time to your actual wake time
wake_time = time(13, 49)  # 1:49 PM
sleep_hours = 7.8

model = CircadianModel()
flow = model.get_energy_flow_prediction(wake_time, sleep_hours)

print('HIGH ENERGY WINDOWS:')
for w in flow['high_energy_windows']:
    print(f'  {w[\"name\"]}: {w[\"start\"]} - {w[\"end\"]} ({w[\"energy_level\"]}%)')

print('\\nLOW ENERGY WINDOWS:')
for w in flow['low_energy_windows']:
    print(f'  {w[\"name\"]}: {w[\"start\"]} - {w[\"end\"]} ({w[\"energy_level\"]}%)')

print(f'\\nSUMMARY: {flow[\"summary\"]}')
"
```

### Generate Energy Flow Graph
```bash
python -c "
from PIL import Image, ImageDraw
from datetime import time
from src.scoring.circadian_model import CircadianModel

wake_time = time(13, 49)  # Your wake time
model = CircadianModel()

# Generate graph (see energy_flow_graph.png)
# ... (full code in project)
print('Graph saved to energy_flow_graph.png')
"
```

### View Today's Report from Database
```bash
python -c "
from src.database import DatabaseConnection, DailyReport
from datetime import datetime

db = DatabaseConnection()
today = datetime.now().strftime('%Y-%m-%d')

with db.get_session() as session:
    report = session.query(DailyReport).filter_by(date=today).first()
    if report:
        print(report.full_report)
    else:
        print('No report found for today')
"
```

### Run for a Specific Date
```bash
python -c "
from datetime import datetime
from daily_workflow import DailyWorkflow

workflow = DailyWorkflow()
# Change to your desired date
date = datetime(2026, 1, 15)
workflow.run(date)
"
```

### Test Google Fit Connection
```bash
python -c "
from src.data_collection import GoogleFitCollector

collector = GoogleFitCollector()
if collector.test_connection():
    print('Connection successful!')
else:
    print('Connection failed - check credentials')
"
```

### List All Sleep Sources
```bash
python -c "
from datetime import datetime, timedelta
from src.data_collection import GoogleFitCollector

collector = GoogleFitCollector()
collector.authenticate()

today = datetime.now()
start = today - timedelta(hours=18)
end = today

sessions = collector.service.users().sessions().list(
    userId='me',
    startTime=start.isoformat() + 'Z',
    endTime=end.isoformat() + 'Z',
    activityType=72
).execute()

for s in sessions.get('session', []):
    app = s.get('application', {}).get('packageName', 'Unknown')
    duration = (int(s['endTimeMillis']) - int(s['startTimeMillis'])) / 3600000
    print(f'{app}: {duration:.1f} hours')
"
```

---

## Customization

### Change Wake/Sleep Time Defaults
Edit `src/scoring/productivity_calculator.py`:
```python
def __init__(self, typical_wake_time: time = time(7, 0),  # Change default
             typical_sleep_time: time = time(23, 0)):      # Change default
```

### Adjust Energy Model Parameters
Edit `src/scoring/circadian_model.py`:
```python
# Adaptive circadian parameters (hours AFTER waking)
FIRST_PEAK_HOURS_AFTER_WAKE = 3.0    # First energy peak
DIP_HOURS_AFTER_WAKE = 7.0           # Energy dip
SECOND_PEAK_HOURS_AFTER_WAKE = 10.0  # Second peak
DECLINE_START_HOURS = 14.0           # When decline starts
```

### Change AI Model
Edit `.env`:
```env
# For different Grok models
GROK_MODEL=llama-3.3-70b-versatile
```

### Change Google Doc Target
Edit `.env`:
```env
GOOGLE_DOC_ID=your_new_document_id
```
(Get the ID from the Google Doc URL: `docs.google.com/document/d/{THIS_IS_THE_ID}/edit`)

---

## Troubleshooting

### "No sleep data found"
```bash
# Check if Zepp is syncing to Google Fit
# 1. Open Google Fit app on phone
# 2. Go to Profile > Settings > Manage connected apps
# 3. Ensure Zepp is connected and syncing

# Test data availability:
python -c "
from datetime import datetime
from src.data_collection import GoogleFitCollector
collector = GoogleFitCollector()
collector.authenticate()
print(collector.get_sleep_data(datetime.now()))
"
```

### "Authentication failed"
```bash
# Delete tokens and re-authenticate
del token.json
del token_fit.json
python daily_workflow.py
```

### "Using wrong sleep source (Pillow instead of Zepp)"
The system automatically prioritizes Zepp. Check logs for:
```
Using Zepp/Amazfit sleep data (preferred source)
```
If you see a different source, ensure Zepp is syncing to Google Fit.

### "Google Docs delivery failed"
```bash
# Test Docs connection
python -c "
from src.delivery import GoogleDocsClient
import os

client = GoogleDocsClient()
client.authenticate()
doc_id = os.getenv('GOOGLE_DOC_ID')
title = client.get_document_title(doc_id)
print(f'Document: {title}')
"
```

### "Module not found" errors
```bash
# Ensure you're in the right directory
cd "D:\Projects\Amazfit Watch Project"

# Ensure virtual environment is activated
venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

### View Logs
```bash
# Check the log file for detailed errors
type logs\daily_workflow.log

# Or tail the last 50 lines (PowerShell)
Get-Content logs\daily_workflow.log -Tail 50
```

---

## Scheduled Automation (Windows)

### Using Task Scheduler

1. Open Task Scheduler (search in Start menu)
2. Click "Create Basic Task"
3. Name: "Productivity Intelligence Daily Report"
4. Trigger: Daily at your preferred time (e.g., 2:00 PM after you wake)
5. Action: Start a program
6. Program: `python`
7. Arguments: `daily_workflow.py`
8. Start in: `D:\Projects\Amazfit Watch Project`

### Using a Batch File
Create `run_daily.bat`:
```batch
@echo off
cd /d "D:\Projects\Amazfit Watch Project"
call venv\Scripts\activate
python daily_workflow.py
pause
```
Double-click to run manually, or schedule via Task Scheduler.

---

## Quick Reference

| Task | Command |
|------|---------|
| Run daily workflow | `python daily_workflow.py` |
| Check sleep data | See "Check Your Sleep Data" section |
| View energy prediction | See "View Energy Flow Prediction" section |
| Re-authenticate Google | Delete `token.json` and `token_fit.json`, then run workflow |
| View logs | `type logs\daily_workflow.log` |
| Check database | `sqlite3 productivity.db ".tables"` |

---

## Support

- Repository: https://github.com/Harisrp82/productivity-intelligence-system
- Issues: Create an issue on GitHub for bugs or feature requests

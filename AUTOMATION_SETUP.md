# Automation Setup Guide

How to automate daily runs on different platforms.

## Windows (Task Scheduler)

### Method 1: Using Task Scheduler GUI

1. **Open Task Scheduler**
   - Press `Win + R`
   - Type `taskschd.msc`
   - Press Enter

2. **Create Basic Task**
   - Click "Create Basic Task" in right panel
   - Name: `Productivity Intelligence`
   - Description: `Daily productivity report generation`
   - Click Next

3. **Set Trigger**
   - When: `Daily`
   - Start date: Today
   - Time: `06:00:00` (6 AM)
   - Recur every: `1` days
   - Click Next

4. **Set Action**
   - Action: `Start a program`
   - Click Next

5. **Program Settings**
   - Program/script: Browse to your Python executable
     - Example: `C:\Python311\python.exe`
     - Or: `C:\Users\YourName\AppData\Local\Programs\Python\Python311\python.exe`

   - Add arguments: `daily_workflow.py`

   - Start in: Path to your project folder
     - Example: `D:\Projects\Amazfit Watch Project`

   - Click Next

6. **Finish**
   - Check "Open Properties dialog"
   - Click Finish

7. **Advanced Settings**
   - In Properties dialog:
     - Check "Run whether user is logged on or not"
     - Check "Run with highest privileges"
     - Check "Hidden" (optional, hides console window)
   - Click OK

8. **Test**
   - Right-click the task
   - Select "Run"
   - Check logs folder for output

### Method 2: Using Command Line

Create a file `create_task.bat`:

```batch
@echo off
set PYTHON_PATH=C:\Python311\python.exe
set PROJECT_PATH=D:\Projects\Amazfit Watch Project
set SCRIPT_PATH=%PROJECT_PATH%\daily_workflow.py

schtasks /create ^
  /tn "Productivity Intelligence" ^
  /tr "\"%PYTHON_PATH%\" \"%SCRIPT_PATH%\"" ^
  /sc daily ^
  /st 06:00 ^
  /f

echo Task created successfully!
pause
```

Run as Administrator.

### Troubleshooting Windows

**Task doesn't run**:
- Check Windows Event Viewer (Event Viewer → Task Scheduler → History)
- Verify Python path is correct
- Ensure project path has no typos
- Run task manually to test

**Console window appears**:
- In task properties, set "Run whether user is logged on or not"
- Or use `pythonw.exe` instead of `python.exe`

**Permission errors**:
- Run task with highest privileges
- Verify user has write access to logs folder

---

## Linux (Cron)

### Setup Cron Job

1. **Edit crontab**:
```bash
crontab -e
```

2. **Add this line**:
```bash
# Run at 6 AM daily
0 6 * * * cd /path/to/project && /usr/bin/python3 daily_workflow.py >> logs/cron.log 2>&1
```

3. **Save and exit**
   - For nano: `Ctrl+O`, `Enter`, `Ctrl+X`
   - For vim: `Esc`, `:wq`, `Enter`

### Alternative: Using Virtual Environment

If using a virtual environment:

```bash
0 6 * * * cd /path/to/project && /path/to/project/venv/bin/python daily_workflow.py >> logs/cron.log 2>&1
```

### Check if Cron is Running

```bash
# View your crontab
crontab -l

# Check cron logs
grep CRON /var/log/syslog
```

### Troubleshooting Linux

**Cron job doesn't run**:
- Check cron is running: `sudo service cron status`
- Verify paths are absolute (not relative)
- Check permissions on script and logs folder

**Environment variables not loaded**:
- Add to crontab:
```bash
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin

0 6 * * * cd /path/to/project && python3 daily_workflow.py >> logs/cron.log 2>&1
```

**No output/errors**:
- Check `logs/cron.log` for stderr/stdout
- Test command manually first

---

## macOS (Cron or launchd)

### Option 1: Cron (Simple)

Same as Linux - edit crontab:
```bash
crontab -e
```

Add:
```bash
0 6 * * * cd /path/to/project && /usr/local/bin/python3 daily_workflow.py >> logs/cron.log 2>&1
```

### Option 2: launchd (Recommended for macOS)

More reliable than cron on macOS.

1. **Create plist file**: `~/Library/LaunchAgents/com.productivity.intelligence.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.productivity.intelligence</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/path/to/project/daily_workflow.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/path/to/project</string>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>6</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>/path/to/project/logs/launchd.log</string>

    <key>StandardErrorPath</key>
    <string>/path/to/project/logs/launchd_error.log</string>
</dict>
</plist>
```

2. **Load the job**:
```bash
launchctl load ~/Library/LaunchAgents/com.productivity.intelligence.plist
```

3. **Test immediately**:
```bash
launchctl start com.productivity.intelligence
```

4. **Check status**:
```bash
launchctl list | grep productivity
```

### Troubleshooting macOS

**launchd job not running**:
- Check logs: `~/Library/Logs/`
- Verify plist syntax: `plutil -lint ~/Library/LaunchAgents/com.productivity.intelligence.plist`
- Check permissions: `chmod 644 ~/Library/LaunchAgents/com.productivity.intelligence.plist`

**Unload job**:
```bash
launchctl unload ~/Library/LaunchAgents/com.productivity.intelligence.plist
```

---

## Docker (All Platforms)

For containerized deployment:

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "daily_workflow.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  productivity-intelligence:
    build: .
    volumes:
      - ./logs:/app/logs
      - ./productivity.db:/app/productivity.db
      - ./.env:/app/.env
      - ./token.json:/app/token.json
      - ./credentials.json:/app/credentials.json
    restart: unless-stopped
```

### Run with Cron in Docker

```bash
# Build
docker-compose build

# Run once
docker-compose run productivity-intelligence

# Schedule with host cron
0 6 * * * cd /path/to/project && docker-compose run productivity-intelligence >> logs/docker.log 2>&1
```

---

## Cloud Platforms

### AWS Lambda

Use AWS EventBridge (CloudWatch Events) to trigger Lambda daily.

1. Package application with dependencies
2. Upload to Lambda
3. Create EventBridge rule: `cron(0 6 * * ? *)`
4. Set environment variables in Lambda

### Google Cloud Functions

Use Cloud Scheduler to trigger function daily.

1. Deploy function to Cloud Functions
2. Create Cloud Scheduler job: `0 6 * * *`
3. Configure function URL as target

### Azure Functions

Use Timer Trigger.

```python
# function.json
{
  "bindings": [{
    "name": "myTimer",
    "type": "timerTrigger",
    "direction": "in",
    "schedule": "0 0 6 * * *"
  }]
}
```

---

## Testing Automation

### Manual Test Run

Before setting up automation, test manually:

```bash
# Navigate to project
cd /path/to/project

# Activate venv if using one
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Run script
python daily_workflow.py

# Check logs
cat logs/daily_workflow.log      # Linux/Mac
type logs\daily_workflow.log     # Windows
```

### Verify Automation Works

After setting up automation:

1. **Trigger manually** (don't wait for scheduled time)
   - Windows: Right-click task → Run
   - Linux/Mac: `launchctl start com.productivity.intelligence`

2. **Check logs**:
   - Look for `logs/daily_workflow.log`
   - Should show successful completion

3. **Verify Google Doc**:
   - Open your Google Doc
   - Should see new report appended

4. **Check database**:
   ```bash
   python scripts/view_data.py
   ```

---

## Monitoring & Alerts

### Simple Email Alerts (Linux)

Install `mailutils` and configure:

```bash
0 6 * * * cd /path/to/project && python3 daily_workflow.py || echo "Workflow failed" | mail -s "Productivity Intelligence Error" you@example.com
```

### Log Rotation

Prevent logs from growing too large:

**Linux** - Create `/etc/logrotate.d/productivity-intelligence`:
```
/path/to/project/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    missingok
}
```

**Windows** - Use Task Scheduler to run cleanup script monthly

### Health Check Script

Create `scripts/health_check.py`:
```python
import os
from datetime import datetime, timedelta
from src.database import DatabaseConnection, DailyReport

db = DatabaseConnection(os.getenv('DATABASE_URL', 'sqlite:///productivity.db'))

with db.get_session() as session:
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    report = session.query(DailyReport).filter_by(date=yesterday).first()

    if not report:
        print(f"ERROR: No report for {yesterday}")
        exit(1)

    if report.delivery_status != 'delivered':
        print(f"ERROR: Report not delivered for {yesterday}")
        exit(1)

    print(f"OK: Report delivered for {yesterday}")
    exit(0)
```

Run after workflow:
```bash
0 7 * * * cd /path/to/project && python scripts/health_check.py || echo "Health check failed" | mail -s "Alert" you@email.com
```

---

## Best Practices

1. **Use absolute paths** everywhere
2. **Test manually first** before automating
3. **Check logs regularly** initially
4. **Set up notifications** for failures
5. **Backup database** periodically
6. **Keep credentials secure** (don't commit `.env`)
7. **Document your setup** for future reference

---

## Common Issues

### "Module not found" error
- Verify Python environment (venv vs system)
- Check `sys.path` in script
- Install requirements in correct environment

### Workflow runs but no report
- Check Google Docs authentication
- Verify doc ID in `.env`
- Look for errors in logs

### Old Python version
- Update Python to 3.11+
- Or modify code for compatibility

### Time zone issues
- Set `TIMEZONE` in `.env`
- Verify system timezone matches

---

## Example Complete Setup

**Linux with virtualenv**:

```bash
#!/bin/bash
# save as: run_productivity_intelligence.sh

cd /home/user/productivity-intelligence-system
source venv/bin/activate
python daily_workflow.py
deactivate
```

Make executable:
```bash
chmod +x run_productivity_intelligence.sh
```

Crontab:
```bash
0 6 * * * /home/user/productivity-intelligence-system/run_productivity_intelligence.sh >> /home/user/productivity-intelligence-system/logs/cron.log 2>&1
```

This ensures:
- Correct working directory
- Virtual environment activated
- All output captured
- Clean environment after run

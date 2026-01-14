# Quick Start Guide

Get your Productivity Intelligence System up and running in 15 minutes.

## Prerequisites

- Python 3.11 or higher
- Amazfit watch with data syncing to [Intervals.icu](https://intervals.icu)
- [Anthropic API key](https://console.anthropic.com/)
- Google account with access to Google Docs

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Configure Environment Variables

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your credentials:

```bash
# Get from https://intervals.icu/settings -> API Key
INTERVALS_API_KEY=your_actual_api_key_here
INTERVALS_ATHLETE_ID=i123456

# Get from https://console.anthropic.com/
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Create a new Google Doc and copy its ID from the URL
# URL format: https://docs.google.com/document/d/YOUR_DOC_ID/edit
GOOGLE_DOC_ID=your_google_doc_id_here

# Leave these as defaults
DATABASE_URL=sqlite:///productivity.db
LOG_LEVEL=INFO
TIMEZONE=Asia/Kolkata  # Change to your timezone
```

### How to Get Your Intervals.icu API Key:
1. Go to https://intervals.icu
2. Sign in with your account
3. Click your profile icon → Settings
4. Scroll to "API Key" section
5. Generate a new API key
6. Note your Athlete ID (starts with "i" like i123456)

### How to Get Your Anthropic API Key:
1. Go to https://console.anthropic.com/
2. Sign in or create account
3. Go to API Keys section
4. Create a new API key
5. Copy and save it (you won't see it again!)

## Step 3: Setup Google Docs Authentication

1. **Enable Google Docs API:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project (or use existing)
   - Enable "Google Docs API"

2. **Create OAuth Credentials:**
   - Go to APIs & Services → Credentials
   - Create Credentials → OAuth client ID
   - Choose "Desktop app" as application type
   - Download the JSON file
   - Rename it to `credentials.json`
   - Place it in your project root directory

3. **Run the authentication setup:**
```bash
python scripts/setup_google_auth.py
```

This will open a browser for you to authorize the app. Grant access to Google Docs.

## Step 4: Initialize Database

```bash
python scripts/setup_database.py
```

This creates the SQLite database with all necessary tables.

## Step 5: Test Your Setup

### Test 1: Intervals.icu Connection
```bash
python scripts/test_data_collection.py
```

This verifies:
- API authentication works
- Wellness data is available
- Recent activities can be fetched

### Test 2: Complete Workflow (Dry Run)
```bash
python scripts/test_full_workflow.py
```

This runs the complete workflow WITHOUT posting to Google Docs:
- Collects data
- Calculates productivity scores
- Generates AI insights
- Displays the report in terminal

## Step 6: Run Your First Report

```bash
python daily_workflow.py
```

This will:
1. Collect yesterday's wellness data
2. Calculate 24 hourly productivity scores
3. Generate personalized AI insights
4. Store everything in the database
5. Post the report to your Google Doc

Check your Google Doc - you should see the report!

## Step 7: Automate Daily Runs

### On Windows (Task Scheduler):

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 6:00 AM
4. Action: Start a program
   - Program: `C:\Path\To\Python\python.exe`
   - Arguments: `C:\Path\To\Project\daily_workflow.py`
   - Start in: `C:\Path\To\Project\`

### On Linux/Mac (cron):

Add to crontab:
```bash
# Edit crontab
crontab -e

# Add this line (runs at 6 AM daily)
0 6 * * * cd /path/to/project && /path/to/python daily_workflow.py >> logs/cron.log 2>&1
```

## Troubleshooting

### "No wellness data available"
- Check that your Amazfit watch is syncing to Zepp app
- Verify Zepp app is syncing to Intervals.icu
- Wait 10-15 minutes after waking for sync to complete
- Try running the script later in the morning

### "Authentication failed" (Google Docs)
- Delete `token.json`
- Run `python scripts/setup_google_auth.py` again
- Make sure you have edit access to the Google Doc

### "Invalid API key" (Intervals.icu)
- Double-check the API key in `.env`
- Make sure there are no extra spaces
- Verify the key is still active in Intervals.icu settings

### "Claude API error"
- Check your Anthropic API key
- Verify you have credits/billing set up
- Check the API key has correct permissions

## What Happens Daily

Every morning at 6 AM, the system will:

1. **Collect Data**: Fetch yesterday's sleep, HRV, RHR from Intervals.icu
2. **Analyze**: Calculate productivity scores for all 24 hours of today
3. **Generate Insights**: Use Claude AI to create personalized recommendations
4. **Deliver**: Post complete report to your Google Doc
5. **Store**: Save all data in local database for future analysis

## What You Get

Each daily report includes:

- **Recovery Status**: Overall physiological state based on HRV, RHR, sleep
- **Peak Productivity Hours**: Best 5 hours for focused work
- **Optimal Focus Blocks**: 2-3 hour windows for deep work
- **AI Insights**: Personalized recommendations from Claude
- **Energy Management Tips**: How to work with your circadian rhythm

## Next Steps

- Review your first few reports to understand the patterns
- Adjust your schedule to align with peak productivity windows
- Track how recovery status correlates with your energy levels
- Use the insights to optimize your work and rest cycles

## Support

If you encounter issues:
1. Check the logs in `logs/daily_workflow.log`
2. Re-run the test scripts to diagnose the problem
3. Verify all API keys and credentials are correct
4. Make sure your Amazfit data is syncing properly

Enjoy optimizing your productivity! 🚀

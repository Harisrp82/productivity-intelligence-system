# Setup Checklist ✅

Use this checklist to track your setup progress. Follow in order!

## Pre-Setup Requirements

- [ ] Python 3.11+ installed
- [ ] pip working (`pip --version`)
- [ ] Amazfit watch syncing to Zepp app
- [ ] Zepp app syncing to Intervals.icu
- [ ] Text editor for editing `.env` file

---

## Step 1: Installation (5 minutes)

- [ ] Download/clone project to your computer
- [ ] Open terminal/command prompt in project folder
- [ ] Run installation script:
  - Windows: `install.bat`
  - Linux/Mac: `chmod +x install.sh && ./install.sh`
- [ ] Verify dependencies installed successfully

---

## Step 2: Get API Keys (5 minutes)

### Intervals.icu API Key
- [ ] Go to https://intervals.icu/settings
- [ ] Sign in with your account
- [ ] Scroll to "API Key" section
- [ ] Click "Generate API Key"
- [ ] Copy the key (save it somewhere safe)
- [ ] Note your Athlete ID (starts with "i" like i123456)

### Anthropic API Key
- [ ] Go to https://console.anthropic.com/
- [ ] Sign up or sign in
- [ ] Go to API Keys section
- [ ] Click "Create Key"
- [ ] Copy the key (starts with sk-ant-)
- [ ] **Important**: Add billing/credits if needed

### Google Doc ID
- [ ] Create a new Google Doc for your reports
- [ ] Name it something like "Daily Productivity Reports"
- [ ] Copy the document ID from URL
  - URL format: `https://docs.google.com/document/d/YOUR_DOC_ID/edit`
  - Copy just the `YOUR_DOC_ID` part

---

## Step 3: Configure Environment (2 minutes)

- [ ] Copy `.env.example` to `.env`
  - Windows: `copy .env.example .env`
  - Linux/Mac: `cp .env.example .env`
- [ ] Open `.env` in text editor
- [ ] Add your Intervals.icu API key
- [ ] Add your Athlete ID (e.g., i123456)
- [ ] Add your Anthropic API key
- [ ] Add your Google Doc ID
- [ ] Change TIMEZONE if needed (e.g., America/New_York)
- [ ] Save and close `.env`

---

## Step 4: Google Cloud Setup (5 minutes)

### Enable Google Docs API
- [ ] Go to https://console.cloud.google.com/
- [ ] Create new project or select existing
- [ ] Click "Enable APIs and Services"
- [ ] Search for "Google Docs API"
- [ ] Click "Enable"

### Create OAuth Credentials
- [ ] Go to "APIs & Services" → "Credentials"
- [ ] Click "Create Credentials" → "OAuth client ID"
- [ ] Configure consent screen if prompted:
  - User Type: External
  - App name: Productivity Intelligence
  - User support email: your email
  - Developer email: your email
  - Save
- [ ] Application type: "Desktop app"
- [ ] Name: Productivity Intelligence
- [ ] Click "Create"
- [ ] Click "Download JSON"
- [ ] Rename file to `credentials.json`
- [ ] Move to project root directory

---

## Step 5: Run Setup Scripts (3 minutes)

### Initialize Database
- [ ] Run: `python scripts/setup_database.py`
- [ ] Verify output says "Database setup complete!"
- [ ] Check that `productivity.db` file was created

### Setup Google Authentication
- [ ] Run: `python scripts/setup_google_auth.py`
- [ ] Browser window opens automatically
- [ ] Sign in with Google account
- [ ] Click "Allow" to grant permissions
- [ ] Return to terminal
- [ ] Verify output says "Setup complete!"
- [ ] Check that `token.json` file was created

---

## Step 6: Test Everything (5 minutes)

### Test Data Collection
- [ ] Run: `python scripts/test_data_collection.py`
- [ ] Verify connection successful
- [ ] Check wellness data is retrieved
- [ ] Confirm baseline calculations work
- [ ] Note any missing data (normal if recent)

### Test Full Workflow
- [ ] Run: `python scripts/test_full_workflow.py`
- [ ] Wait for completion (~15 seconds)
- [ ] Review generated report in terminal
- [ ] Check all sections present:
  - Recovery summary
  - Peak productivity hours
  - AI insights
  - Recommended focus blocks

---

## Step 7: First Real Run (1 minute)

- [ ] Run: `python daily_workflow.py`
- [ ] Wait for completion
- [ ] Check terminal output for "Workflow completed successfully"
- [ ] Open your Google Doc
- [ ] Verify report was added
- [ ] Review the content

---

## Step 8: Automate Daily Runs (5 minutes)

Choose your platform:

### Windows (Task Scheduler)
- [ ] Open Task Scheduler
- [ ] Follow instructions in [AUTOMATION_SETUP.md](AUTOMATION_SETUP.md#windows-task-scheduler)
- [ ] Create task to run at 6:00 AM daily
- [ ] Test by right-clicking task → Run
- [ ] Verify it works

### Linux (Cron)
- [ ] Run: `crontab -e`
- [ ] Add line: `0 6 * * * cd /path/to/project && python3 daily_workflow.py >> logs/cron.log 2>&1`
- [ ] Save and exit
- [ ] Test with: `crontab -l` (should show your entry)

### macOS (launchd or cron)
- [ ] Follow instructions in [AUTOMATION_SETUP.md](AUTOMATION_SETUP.md#macos-cron-or-launchd)
- [ ] Create launchd plist or crontab entry
- [ ] Test the job

---

## Step 9: Monitor First Week (optional)

- [ ] Check logs daily: `logs/daily_workflow.log`
- [ ] Verify reports appear in Google Doc
- [ ] Compare productivity scores to actual energy
- [ ] Note any patterns or issues
- [ ] Adjust wake time in `.env` if needed

---

## Troubleshooting Checklist

If something doesn't work:

### Data Collection Issues
- [ ] Amazfit watch is charged and syncing
- [ ] Zepp app shows recent data
- [ ] Intervals.icu shows recent wellness data
- [ ] API key in `.env` is correct (no spaces)
- [ ] Athlete ID in `.env` is correct

### Google Docs Issues
- [ ] `credentials.json` exists in project root
- [ ] `token.json` exists (re-run setup if not)
- [ ] Google Doc ID is correct
- [ ] You have edit access to the doc
- [ ] Try deleting `token.json` and re-authenticating

### API Key Issues
- [ ] Anthropic API key starts with `sk-ant-`
- [ ] You have credits/billing set up
- [ ] No extra spaces in `.env` file
- [ ] Keys are on correct lines

### General Issues
- [ ] Check logs: `logs/daily_workflow.log`
- [ ] Re-run test scripts
- [ ] Verify Python version: `python --version` (should be 3.11+)
- [ ] Try running with verbose logging: `LOG_LEVEL=DEBUG` in `.env`

---

## Success Criteria ✅

You're all set when:
- ✅ `test_data_collection.py` runs successfully
- ✅ `test_full_workflow.py` generates complete report
- ✅ `daily_workflow.py` posts to Google Doc
- ✅ Automation is scheduled for 6 AM daily
- ✅ You understand where to find logs

---

## Next Steps After Setup

1. **Review your first week of reports** to understand your patterns
2. **Adjust your schedule** to align with peak productivity hours
3. **Track correlations** between sleep/recovery and productivity
4. **Experiment** with different sleep schedules
5. **Share insights** with coaches or teammates if desired

---

## Quick Reference

### Daily Commands
```bash
# Manual run
python daily_workflow.py

# View recent data
python scripts/view_data.py

# View specific date
python scripts/view_data.py 2024-01-15

# Check logs
cat logs/daily_workflow.log          # Linux/Mac
type logs\daily_workflow.log         # Windows
```

### Important Files
- `.env` - Your configuration
- `credentials.json` - Google OAuth (keep private)
- `token.json` - Access token (keep private)
- `productivity.db` - Your data (backup regularly)
- `logs/daily_workflow.log` - Operation logs

### Documentation
- [QUICKSTART.md](QUICKSTART.md) - Detailed setup guide
- [AUTOMATION_SETUP.md](AUTOMATION_SETUP.md) - Platform automation
- [ARCHITECTURE.md](ARCHITECTURE.md) - How it works
- [INDEX.md](INDEX.md) - Complete navigation

---

## Backup Recommendations

- [ ] **Weekly**: Copy `productivity.db` to backup location
- [ ] **Monthly**: Export `.env` (securely!) in case of system failure
- [ ] **Never**: Commit credentials to git/cloud

---

## Support

Stuck on something?

1. Check [QUICKSTART.md](QUICKSTART.md) Troubleshooting section
2. Review logs in `logs/daily_workflow.log`
3. Re-run test scripts to isolate the issue
4. Check API status pages:
   - Intervals.icu: https://intervals.icu
   - Anthropic: https://status.anthropic.com
   - Google: https://www.google.com/appsstatus

---

**Congratulations on setting up your Productivity Intelligence System!** 🎉

You now have an AI-powered system that will help you optimize your daily schedule based on your body's natural rhythms and recovery status.

**Time to complete setup**: ~30 minutes
**Daily time cost**: 0 minutes (fully automated!)
**Benefit**: Optimized productivity and energy management ⚡

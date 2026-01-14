# Configuration Guide - API Keys & Setup

This guide will walk you through getting all the API keys and configuring the system.

---

## 📋 Overview: What You Need

You need **3 API keys** and **1 Google Doc ID**:

1. ✅ **Intervals.icu API Key** (for getting Amazfit watch data)
2. ✅ **Anthropic Claude API Key** (for AI insights)
3. ✅ **Google OAuth Credentials** (for posting to Google Docs)
4. ✅ **Google Doc ID** (where reports will be posted)

---

## 1️⃣ Intervals.icu API Key

### What it does:
Fetches your sleep, HRV, and heart rate data from your Amazfit watch.

### How to get it:

1. **Go to**: https://intervals.icu
2. **Sign in** with your account (the one connected to your Zepp/Amazfit)
3. Click your **profile icon** (top right)
4. Select **Settings**
5. Scroll down to find **"API Key"** section
6. Click **"Generate API Key"** button
7. **Copy the key** (it will look like a long random string)
8. **Also note your Athlete ID** - it's shown at the top of the settings page (format: `i123456`)

### Where to use it:
Open the `.env` file and paste:
```
INTERVALS_API_KEY=paste_your_key_here
INTERVALS_ATHLETE_ID=i123456
```

---

## 2️⃣ Anthropic Claude API Key

### What it does:
Powers the AI that generates personalized productivity insights.

### How to get it:

1. **Go to**: https://console.anthropic.com/
2. **Sign up** or **Sign in**
3. Once logged in, go to **"API Keys"** (left sidebar)
4. Click **"Create Key"** button
5. Give it a name (e.g., "Productivity System")
6. **Copy the key** (starts with `sk-ant-`)
   - ⚠️ **Important**: Save it immediately - you won't see it again!
7. **Set up billing**:
   - Go to **"Billing"** section
   - Add a payment method
   - Add credits (minimum $5 recommended)
   - Your usage will be ~$0.50-1.00 per month

### Where to use it:
Open the `.env` file and paste:
```
ANTHROPIC_API_KEY=sk-ant-your_key_here
```

---

## 3️⃣ Google OAuth Credentials (for Google Docs)

### What it does:
Allows the system to post reports to your Google Docs.

### How to get it:

#### Step A: Create Google Cloud Project

1. **Go to**: https://console.cloud.google.com/
2. Click **"Select a project"** (top bar)
3. Click **"New Project"**
4. **Project name**: `Productivity Intelligence` (or any name)
5. Click **"Create"**
6. Wait for project to be created (takes 10-20 seconds)

#### Step B: Enable Google Docs API

1. Make sure your new project is selected (check top bar)
2. Go to **"APIs & Services"** → **"Library"** (left sidebar)
3. Search for **"Google Docs API"**
4. Click on it
5. Click **"Enable"** button
6. Wait for it to enable

#### Step C: Configure OAuth Consent Screen

1. Go to **"APIs & Services"** → **"OAuth consent screen"** (left sidebar)
2. Choose **"External"** (unless you have Google Workspace)
3. Click **"Create"**
4. Fill in the form:
   - **App name**: `Productivity Intelligence System`
   - **User support email**: Select your email
   - **Developer contact email**: Your email
   - Leave other fields blank
5. Click **"Save and Continue"**
6. **Scopes page**: Click **"Save and Continue"** (no changes needed)
7. **Test users page**: Click **"Add Users"**
   - Add your own email address
   - Click **"Add"**
8. Click **"Save and Continue"**
9. Review and click **"Back to Dashboard"**

#### Step D: Create OAuth Credentials

1. Go to **"APIs & Services"** → **"Credentials"** (left sidebar)
2. Click **"+ Create Credentials"** (top)
3. Select **"OAuth client ID"**
4. **Application type**: Choose **"Desktop app"**
5. **Name**: `Productivity Desktop Client`
6. Click **"Create"**
7. A popup appears - click **"Download JSON"**
8. **Save the file** to your computer

#### Step E: Add Credentials to Project

1. **Rename** the downloaded file to `credentials.json`
2. **Move it** to your project folder: `d:\Projects\Amazfit Watch Project\`
3. Make sure it's in the **root** of the project (same folder as `daily_workflow.py`)

### Where to use it:
The `credentials.json` file is automatically used by the system. Just make sure it's in the project root folder.

---

## 4️⃣ Google Doc ID (Where Reports Will Go)

### What it does:
This is the document where your daily reports will be posted.

### How to get it:

1. **Go to**: https://docs.google.com/
2. Click **"+ Blank"** to create a new document
3. **Name the document**: `Daily Productivity Reports` (or any name you like)
4. Look at the **URL** in your browser - it looks like:
   ```
   https://docs.google.com/document/d/1abc123xyz456def789ghi/edit
                                    ^^^^^^^^^^^^^^^^^^^^^^
                                    This is your Doc ID
   ```
5. **Copy just the ID part** (the random letters/numbers between `/d/` and `/edit`)
   - Example: `1abc123xyz456def789ghi`

### Where to use it:
Open the `.env` file and paste:
```
GOOGLE_DOC_ID=your_doc_id_here
```

---

## 📝 Complete .env File Configuration

Now open the `.env` file in your project folder and fill in ALL values:

```bash
# Intervals.icu API (from https://intervals.icu/settings)
INTERVALS_API_KEY=your_intervals_key_here
INTERVALS_ATHLETE_ID=i123456

# Anthropic Claude API (from https://console.anthropic.com/)
ANTHROPIC_API_KEY=sk-ant-your_anthropic_key_here

# Google Docs (your document ID from the URL)
GOOGLE_DOC_ID=your_google_doc_id_here

# Database (leave as default)
DATABASE_URL=sqlite:///productivity.db

# Settings
LOG_LEVEL=INFO
TIMEZONE=Asia/Kolkata
```

### ⚠️ Important Notes:
- **No quotes** needed around the values
- **No spaces** before or after the `=` sign
- Change `TIMEZONE` to your timezone if different (e.g., `America/New_York`, `Europe/London`)

---

## ✅ Verify Your Configuration

### Check 1: .env File
Open `.env` and make sure:
- ✅ All 4 values are filled in (INTERVALS_API_KEY, INTERVALS_ATHLETE_ID, ANTHROPIC_API_KEY, GOOGLE_DOC_ID)
- ✅ No placeholder text like "your_key_here" remains
- ✅ Keys look correct (Anthropic key starts with `sk-ant-`)

### Check 2: credentials.json File
- ✅ File exists in project root: `d:\Projects\Amazfit Watch Project\credentials.json`
- ✅ File is named exactly `credentials.json` (not `credentials (1).json` or similar)
- ✅ File size is around 2-5 KB (contains JSON data)

---

## 🚀 Run Setup Scripts

Now that everything is configured, run these scripts in order:

### 1. Initialize Database
```bash
python scripts/setup_database.py
```
**Expected output**: "Database setup complete!"

### 2. Setup Google Authentication
```bash
python scripts/setup_google_auth.py
```
**What happens**:
- A browser window opens automatically
- Sign in with your Google account (the one that owns the Google Doc)
- Click "Allow" to grant permissions
- Browser shows "The authentication flow has completed"
- Return to terminal - should say "Setup complete!"

**Creates**: `token.json` file in your project folder

### 3. Test Data Collection
```bash
python scripts/test_data_collection.py
```
**Expected output**:
- ✅ Connection test successful
- ✅ Wellness data retrieved (sleep, HRV, RHR)
- ✅ Baseline calculated
- ✅ Recent activities found

**If you see errors**:
- Check that Amazfit watch synced to Zepp app
- Verify Zepp app synced to Intervals.icu
- Wait 10-15 minutes after waking for sync to complete

### 4. Test Full Workflow (Dry Run)
```bash
python scripts/test_full_workflow.py
```
**What happens**:
- Collects yesterday's data
- Calculates productivity scores
- Generates AI insights
- **Displays report in terminal** (does NOT post to Google Docs yet)

**Review the report** - this is what will be posted daily.

### 5. First Real Run
```bash
python daily_workflow.py
```
**What happens**:
- Collects data
- Calculates scores
- Generates AI insights
- **Posts report to Google Docs** ✅
- Saves everything to database

**After running**:
1. Open your Google Doc
2. Scroll to the bottom
3. You should see your first report!

---

## 📊 What Your Report Will Look Like

Each morning, a report like this will be added to your Google Doc:

```markdown
================================================================================

# Productivity Intelligence Report
## 2024-01-15

---

### Quick Stats

- Sleep: 7.5 hours
- Recovery Score: 82/100 (good)
- Avg Productivity: 74/100

### Peak Productivity Hours

- 09:00 - Score: 89/100
- 10:00 - Score: 91/100
- 11:00 - Score: 88/100
- 15:00 - Score: 83/100
- 16:00 - Score: 80/100

### AI Insights

**Recovery Summary**: Your recovery is good today. HRV is slightly
elevated (+2.5ms), indicating strong parasympathetic activity.
Resting heart rate is normal. Your body is well-prepared for a
productive day.

**Today's Optimal Windows**: Your peak cognitive performance will
occur between 9:00-12:00, with a secondary peak from 15:00-17:00.
The late morning window (9-12) is ideal for your most demanding
analytical work.

**Energy Management**: Expect a natural dip around 14:00-15:00.
Use this time for lighter tasks, meetings, or a brief walk. Avoid
scheduling important decisions during this window.

**Recommendations**:
1. Schedule your most important deep work for 9:00-11:00
2. Use the afternoon peak (15:00-17:00) for creative tasks
3. Given good recovery, today is suitable for high-intensity
   training if planned

---

### Recommended Focus Blocks

1. 09:00 - 12:00 - 3 hours (Score: 89)
2. 15:00 - 17:00 - 2 hours (Score: 81)

---

*Generated automatically by Productivity Intelligence System*
*Powered by Claude AI and Intervals.icu data*
```

---

## 🔄 Automate Daily Runs

Once everything is working, set up automation so it runs every morning at 6 AM.

See **[AUTOMATION_SETUP.md](AUTOMATION_SETUP.md)** for platform-specific instructions:
- Windows: Task Scheduler
- Linux: Cron
- macOS: launchd or cron

---

## 🐛 Troubleshooting

### "No wellness data available"
- ✅ Check Amazfit watch battery and Bluetooth connection
- ✅ Open Zepp app and force sync
- ✅ Log into Intervals.icu website and verify data is there
- ✅ Try running the script later in the day (data may not have synced yet)

### "Invalid API key" (Intervals.icu)
- ✅ Copy the key again from Intervals.icu settings
- ✅ Make sure no extra spaces in `.env` file
- ✅ Verify Athlete ID is correct (starts with `i`)

### "Authentication error" (Claude)
- ✅ Check API key starts with `sk-ant-`
- ✅ Verify billing/credits are set up in Anthropic console
- ✅ Check https://console.anthropic.com/ for any issues

### "Could not access document" (Google Docs)
- ✅ Verify Google Doc ID is correct
- ✅ Make sure you have edit access to the document
- ✅ Delete `token.json` and run `setup_google_auth.py` again
- ✅ Check that you granted permissions during OAuth flow

### "Module not found" errors
- ✅ Run: `pip install -r requirements.txt`
- ✅ Make sure you're in the project directory
- ✅ Check Python version: `python --version` (should be 3.11+)

---

## 📞 Need Help?

1. **Check logs**: `logs/daily_workflow.log`
2. **Re-run test scripts** to isolate the issue
3. **Verify all API keys** are correct in `.env`
4. **Check API status pages**:
   - Intervals.icu: https://intervals.icu
   - Anthropic: https://status.anthropic.com
   - Google: https://www.google.com/appsstatus

---

## ✅ Success Checklist

You're ready to go when:
- ✅ `.env` file has all 4 keys filled in
- ✅ `credentials.json` exists in project root
- ✅ `token.json` created by setup_google_auth.py
- ✅ `test_data_collection.py` runs successfully
- ✅ `test_full_workflow.py` generates a report
- ✅ `daily_workflow.py` posts to your Google Doc
- ✅ You can see the report in your Google Doc

---

**You're all set!** The system will now automatically analyze your sleep and recovery each day and provide personalized productivity insights. 🚀

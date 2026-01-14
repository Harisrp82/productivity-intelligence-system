# Quick Setup - Get Running in 15 Minutes ⚡

## Step-by-Step Setup

### 📦 Step 1: Install Dependencies (2 min)

```bash
# Windows
install.bat

# Linux/Mac
chmod +x install.sh
./install.sh
```

---

### 🔑 Step 2: Get Your API Keys (10 min)

#### A. Intervals.icu → For Amazfit Watch Data

1. Go to: **https://intervals.icu/settings**
2. Click "Generate API Key"
3. Copy the key
4. Note your Athlete ID (format: `i123456`)

#### B. Anthropic Claude → For AI Insights

1. Go to: **https://console.anthropic.com/**
2. Sign up/Sign in
3. Go to "API Keys" → "Create Key"
4. Copy the key (starts with `sk-ant-`)
5. ⚠️ Add billing: Go to "Billing" → Add payment method + credits

#### C. Google Cloud → For Posting Reports

1. Go to: **https://console.cloud.google.com/**
2. Create new project: "Productivity Intelligence"
3. Enable "Google Docs API"
4. Create OAuth credentials:
   - Go to "Credentials" → "Create Credentials" → "OAuth client ID"
   - Type: "Desktop app"
   - Download JSON file
5. Rename to `credentials.json`
6. Move to project folder

#### D. Google Doc → Where Reports Go

1. Go to: **https://docs.google.com/**
2. Create new blank document
3. Name it: "Daily Productivity Reports"
4. Copy the ID from URL:
   ```
   https://docs.google.com/document/d/YOUR_DOC_ID_HERE/edit
   ```

---

### ⚙️ Step 3: Configure .env File (2 min)

**File to edit**: `d:\Projects\Amazfit Watch Project\.env`

If `.env` doesn't exist, copy from `.env.example`:
```bash
copy .env.example .env
```

**Open `.env` in any text editor** and fill in:

```bash
# FROM INTERVALS.ICU
INTERVALS_API_KEY=paste_your_intervals_key_here
INTERVALS_ATHLETE_ID=i123456

# FROM ANTHROPIC
ANTHROPIC_API_KEY=sk-ant-paste_your_anthropic_key_here

# FROM GOOGLE DOCS URL
GOOGLE_DOC_ID=paste_your_doc_id_here

# LEAVE THESE AS DEFAULT
DATABASE_URL=sqlite:///productivity.db
LOG_LEVEL=INFO
TIMEZONE=Asia/Kolkata  # Change if needed
```

**Save the file!**

---

### 🗂️ Step 4: Add Google Credentials (1 min)

**File location**: `d:\Projects\Amazfit Watch Project\credentials.json`

1. Take the JSON file you downloaded from Google Cloud
2. Rename it to exactly: `credentials.json`
3. Place it in the project root folder (same location as `daily_workflow.py`)

---

### ✅ Step 5: Run Setup Scripts (3 min)

Open terminal/command prompt in project folder and run:

#### 1. Initialize Database
```bash
python scripts/setup_database.py
```
✅ Should say: "Database setup complete!"

#### 2. Authenticate with Google
```bash
python scripts/setup_google_auth.py
```
✅ Browser opens → Sign in → Click "Allow" → Done!

#### 3. Test Data Collection
```bash
python scripts/test_data_collection.py
```
✅ Should show your sleep data, HRV, RHR

#### 4. Test Full Workflow (Dry Run)
```bash
python scripts/test_full_workflow.py
```
✅ Generates and displays a report (doesn't post to Google Docs yet)

#### 5. First Real Run
```bash
python daily_workflow.py
```
✅ Posts report to your Google Doc!

**Check your Google Doc** - you should see the report! 🎉

---

## 📁 Files You Need to Edit/Create

```
d:\Projects\Amazfit Watch Project\
│
├── .env                          ← EDIT THIS (add your API keys)
│   ├── INTERVALS_API_KEY         ← From intervals.icu/settings
│   ├── INTERVALS_ATHLETE_ID      ← From intervals.icu/settings
│   ├── ANTHROPIC_API_KEY         ← From console.anthropic.com
│   └── GOOGLE_DOC_ID             ← From Google Doc URL
│
└── credentials.json              ← ADD THIS (download from Google Cloud)
```

**That's it!** Only 2 files to configure.

---

## 🎯 What Each API Does

| API | What It Does | Cost |
|-----|-------------|------|
| **Intervals.icu** | Fetches your Amazfit watch data (sleep, HRV, RHR) | Free |
| **Anthropic Claude** | Generates personalized AI insights | ~$1/month |
| **Google Docs** | Posts daily reports to your doc | Free |

---

## 📊 What You'll Get

Every morning at 6 AM, a new report appears in your Google Doc:

- ✅ Recovery status (based on HRV, RHR, sleep)
- ✅ 24 hourly productivity scores
- ✅ Peak productivity hours
- ✅ Optimal focus blocks
- ✅ Personalized AI recommendations

---

## 🔄 Automate (Optional)

To run automatically every morning:

**Windows**: Use Task Scheduler
**Linux/Mac**: Use cron

See [AUTOMATION_SETUP.md](AUTOMATION_SETUP.md) for detailed instructions.

---

## ❓ Common Questions

### Q: Where does my Amazfit data come from?
**A**: Amazfit watch → Zepp app → Intervals.icu → This system

Make sure:
1. Watch syncs to Zepp app (Bluetooth)
2. Zepp app syncs to Intervals.icu (automatic)

### Q: Do I need to run this manually every day?
**A**: No! Set up automation (Step 6 above) and it runs automatically at 6 AM.

### Q: Can I test without posting to Google Docs?
**A**: Yes! Use `python scripts/test_full_workflow.py` - shows report in terminal only.

### Q: What if I don't have yesterday's data yet?
**A**: Wait until morning. Data needs time to sync from watch → Zepp → Intervals.icu.

### Q: How much does this cost?
**A**: < $2/month (only Anthropic Claude API, ~$0.50-1.00/month)

---

## 🐛 Something Not Working?

See detailed troubleshooting in:
- [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md) - Complete API setup guide
- [QUICKSTART.md](QUICKSTART.md) - Full setup instructions
- Check logs: `logs/daily_workflow.log`

---

## 🎉 You're Done!

Once `daily_workflow.py` posts to your Google Doc successfully, you're all set!

The system will now:
1. Wake up at 6 AM daily (if automated)
2. Collect your wellness data
3. Calculate productivity scores
4. Generate AI insights
5. Post to Google Doc
6. Store in database

Enjoy optimized productivity! 🚀

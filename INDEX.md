# Productivity Intelligence System - Complete Index

## 📋 Quick Navigation

### Getting Started
- **[QUICKSTART.md](QUICKSTART.md)** - 15-minute setup guide
- **[README.md](README.md)** - Project overview
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - What this system does

### Installation
- **[install.bat](install.bat)** - Windows installation script
- **[install.sh](install.sh)** - Linux/Mac installation script
- **[requirements.txt](requirements.txt)** - Python dependencies

### Configuration
- **[.env.example](.env.example)** - Environment variables template
- Copy to `.env` and add your API keys

### Documentation
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical architecture details
- **[AUTOMATION_SETUP.md](AUTOMATION_SETUP.md)** - Platform-specific automation guides

---

## 🔧 Core Application

### Main Script
- **[daily_workflow.py](daily_workflow.py)** - Main automation script (run this daily)

### Source Code Structure

```
src/
├── __init__.py
│
├── data_collection/
│   ├── __init__.py
│   └── intervals_icu_collector.py       # Intervals.icu API client
│
├── scoring/
│   ├── __init__.py
│   ├── circadian_model.py               # Two-process sleep model
│   ├── recovery_analyzer.py             # HRV/RHR analysis
│   └── productivity_calculator.py       # Hourly score calculator
│
├── ai/
│   ├── __init__.py
│   ├── claude_client.py                 # Anthropic API wrapper
│   ├── prompt_templates.py              # AI prompts
│   └── insight_generator.py             # Insight orchestration
│
├── database/
│   ├── __init__.py
│   ├── models.py                        # SQLAlchemy models
│   └── connection.py                    # Database connection
│
└── delivery/
    ├── __init__.py
    └── google_docs.py                   # Google Docs API client
```

---

## 🧪 Testing & Setup Scripts

### Setup Scripts
- **[scripts/setup_database.py](scripts/setup_database.py)** - Initialize SQLite database
- **[scripts/setup_google_auth.py](scripts/setup_google_auth.py)** - Configure Google OAuth

### Testing Scripts
- **[scripts/test_data_collection.py](scripts/test_data_collection.py)** - Test Intervals.icu connection
- **[scripts/test_full_workflow.py](scripts/test_full_workflow.py)** - End-to-end workflow test
- **[scripts/view_data.py](scripts/view_data.py)** - View stored historical data

---

## 📚 Documentation Files

### User Documentation
| File | Purpose |
|------|---------|
| **README.md** | Project overview and features |
| **QUICKSTART.md** | Step-by-step setup guide (start here!) |
| **PROJECT_SUMMARY.md** | Complete system description and use cases |
| **AUTOMATION_SETUP.md** | Platform-specific automation instructions |

### Technical Documentation
| File | Purpose |
|------|---------|
| **ARCHITECTURE.md** | System architecture, algorithms, and design |
| **INDEX.md** | This file - navigation hub |

---

## 🗂️ Configuration Files

### Required Setup
| File | Purpose | Status |
|------|---------|--------|
| **.env** | API keys and configuration | Create from .env.example |
| **credentials.json** | Google OAuth credentials | Download from Google Cloud Console |
| **token.json** | Google access token | Auto-created by setup_google_auth.py |

### Auto-Generated
| File | Purpose |
|------|---------|
| **productivity.db** | SQLite database (auto-created) |
| **logs/*.log** | Application logs |

---

## 📖 How to Use This Project

### First Time Setup (15 minutes)

1. **Install dependencies**
   ```bash
   # Windows
   install.bat

   # Linux/Mac
   chmod +x install.sh
   ./install.sh
   ```

2. **Configure API keys**
   - Copy `.env.example` to `.env`
   - Add your Intervals.icu API key
   - Add your Anthropic API key
   - Add your Google Doc ID

3. **Setup Google OAuth**
   - Download credentials from Google Cloud Console
   - Save as `credentials.json`
   - Run: `python scripts/setup_google_auth.py`

4. **Initialize database**
   ```bash
   python scripts/setup_database.py
   ```

5. **Test everything**
   ```bash
   python scripts/test_data_collection.py
   python scripts/test_full_workflow.py
   ```

6. **Run first report**
   ```bash
   python daily_workflow.py
   ```

7. **Automate**
   - See [AUTOMATION_SETUP.md](AUTOMATION_SETUP.md)
   - Setup cron (Linux/Mac) or Task Scheduler (Windows)

### Daily Usage (Automated)

Once set up, the system runs automatically:
- **6 AM daily**: Collects yesterday's data, generates report
- **Output**: New report appended to your Google Doc
- **Storage**: All data saved in `productivity.db`

### Viewing Data

```bash
# View recent records
python scripts/view_data.py

# View specific date
python scripts/view_data.py 2024-01-15
```

---

## 🔑 Key Components Explained

### Data Collection
**File**: `src/data_collection/intervals_icu_collector.py`

- Fetches wellness data from Intervals.icu API
- Retrieves sleep duration, HRV, resting heart rate
- Calculates 7-day rolling baselines
- Collects recent activity context

### Productivity Scoring
**Files**:
- `src/scoring/circadian_model.py` - Circadian rhythm calculations
- `src/scoring/recovery_analyzer.py` - Recovery from HRV/RHR
- `src/scoring/productivity_calculator.py` - Combines into hourly scores

**Algorithm**:
- Process C: 24-hour circadian rhythm (peak ~10 AM)
- Process S: Homeostatic sleep pressure
- Recovery: Weighted HRV (45%) + RHR (35%) + Sleep (20%)
- **Final Score**: (Circadian × 50%) + (Recovery × 50%)

### AI Insights
**Files**:
- `src/ai/claude_client.py` - API wrapper
- `src/ai/prompt_templates.py` - Structured prompts
- `src/ai/insight_generator.py` - Orchestration

**Output**:
- Recovery summary
- Peak productivity hours
- Energy management tips
- Personalized action items

### Database Storage
**Files**:
- `src/database/models.py` - Data models
- `src/database/connection.py` - SQLite connection

**Tables**:
- `wellness_records` - Daily wellness metrics
- `productivity_scores` - Hourly scores (24 per day)
- `daily_reports` - Generated insights

### Report Delivery
**File**: `src/delivery/google_docs.py`

- Authenticates with Google OAuth
- Appends formatted reports to Google Doc
- Updates delivery status in database

---

## 🎯 What Each File Does

### Application Files

| File | Lines | Purpose |
|------|-------|---------|
| **daily_workflow.py** | ~250 | Main orchestration script |
| **intervals_icu_collector.py** | ~200 | Fetch data from API |
| **circadian_model.py** | ~150 | Circadian rhythm calculations |
| **recovery_analyzer.py** | ~200 | Recovery score from HRV/RHR |
| **productivity_calculator.py** | ~150 | Combine into hourly scores |
| **claude_client.py** | ~100 | Claude API wrapper |
| **prompt_templates.py** | ~150 | AI prompt templates |
| **insight_generator.py** | ~150 | Generate AI insights |
| **models.py** | ~100 | Database schema |
| **connection.py** | ~70 | Database connection |
| **google_docs.py** | ~150 | Google Docs API client |

### Script Files

| File | Purpose |
|------|---------|
| **setup_database.py** | Create database tables |
| **setup_google_auth.py** | OAuth authentication flow |
| **test_data_collection.py** | Verify API connection |
| **test_full_workflow.py** | End-to-end test |
| **view_data.py** | View stored data |

---

## 🚀 Common Tasks

### Running Reports

```bash
# Run for yesterday (default)
python daily_workflow.py

# View what was generated
python scripts/view_data.py
```

### Troubleshooting

```bash
# Test API connection
python scripts/test_data_collection.py

# Test without posting to Google Docs
python scripts/test_full_workflow.py

# Check logs
type logs\daily_workflow.log        # Windows
cat logs/daily_workflow.log         # Linux/Mac
```

### Viewing Historical Data

```bash
# Recent records
python scripts/view_data.py

# Specific date
python scripts/view_data.py 2024-01-15

# Database stats
python scripts/view_data.py
```

---

## 📊 System Requirements

### Software
- Python 3.11 or higher
- pip (Python package manager)
- Internet connection

### APIs & Services
- Intervals.icu account (free)
- Anthropic API key (~$1/month)
- Google account (free)
- Google Cloud project (free)

### Hardware
- Any computer (Windows/Linux/Mac)
- Minimal: 100 MB disk space, 256 MB RAM
- Can run on Raspberry Pi

---

## 💰 Cost Breakdown

| Service | Cost |
|---------|------|
| Intervals.icu | Free |
| Anthropic Claude API | $0.50-1.00/month |
| Google Docs API | Free |
| **Total** | **< $2/month** |

---

## 🔐 Security Notes

### Files to Keep Private
- `.env` - Contains API keys (gitignored)
- `credentials.json` - Google OAuth (gitignored)
- `token.json` - Access token (gitignored)
- `productivity.db` - Personal data (gitignored)

### Safe to Share
- All source code files
- Documentation files
- Configuration templates

---

## 🎓 Learning Resources

### To Understand Circadian Rhythms
- Look at `circadian_model.py`
- Read comments explaining two-process model
- See ARCHITECTURE.md for algorithm details

### To Understand Recovery Analysis
- Look at `recovery_analyzer.py`
- HRV and RHR explained in comments
- Weighted scoring methodology

### To Modify AI Prompts
- Edit `prompt_templates.py`
- Adjust system prompts for different tone
- Modify report structure

---

## 🛠️ Customization Options

### Change Wake Time
Edit in `daily_workflow.py` or per-run calculation

### Adjust Scoring Weights
Modify in:
- `recovery_analyzer.py` - HRV/RHR/Sleep weights
- `productivity_calculator.py` - Circadian/Recovery balance

### Modify Report Format
Edit `prompt_templates.py`:
- Change report structure
- Adjust tone and style
- Add/remove sections

### Change Delivery Method
Extend `src/delivery/` to add:
- Email delivery
- Slack notifications
- Custom webhooks

---

## 📈 Future Enhancements

Potential additions:
- [ ] Weekly trend analysis
- [ ] Predictive modeling
- [ ] Web dashboard
- [ ] Mobile app
- [ ] Multi-user support
- [ ] Activity-based adjustments
- [ ] Weather integration
- [ ] Calendar integration

---

## 🤝 Contributing

This is a personal project, but feel free to:
- Fork and customize for your needs
- Share improvements
- Report issues
- Suggest features

---

## 📞 Support

### Check First
1. **Logs**: `logs/daily_workflow.log`
2. **Documentation**: README.md, QUICKSTART.md
3. **Test scripts**: Run diagnostic scripts

### Common Issues
- See QUICKSTART.md Troubleshooting section
- Check AUTOMATION_SETUP.md for platform issues

---

## ✅ Project Status

**Status**: Complete and functional ✅

All core features implemented:
- ✅ Data collection from Intervals.icu
- ✅ Productivity scoring algorithms
- ✅ AI insight generation
- ✅ Database storage
- ✅ Google Docs delivery
- ✅ Automation support
- ✅ Testing utilities
- ✅ Complete documentation

Ready for production use!

---

## 📝 License

MIT License - Free to use, modify, and distribute

---

**Questions?** Start with [QUICKSTART.md](QUICKSTART.md)

**Want details?** Read [ARCHITECTURE.md](ARCHITECTURE.md)

**Ready to begin?** Run `install.bat` (Windows) or `./install.sh` (Linux/Mac)

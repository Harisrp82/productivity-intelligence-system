# Productivity Intelligence System - Project Summary

## What This System Does

An automated AI-powered productivity intelligence system that:

1. **Collects** your wellness data from Amazfit watches via Intervals.icu
2. **Analyzes** your circadian rhythm, sleep pressure, and recovery status
3. **Calculates** hourly productivity scores for all 24 hours of each day
4. **Generates** personalized insights using Claude AI
5. **Delivers** daily reports to Google Docs automatically every morning

## Key Features

### 🔬 Science-Based Scoring
- Implements two-process model of sleep regulation (circadian + homeostatic)
- Analyzes HRV and RHR for recovery assessment
- Combines multiple physiological signals for accurate predictions

### 🤖 AI-Powered Insights
- Uses Claude Sonnet 4.5 for personalized recommendations
- Contextual analysis based on your specific patterns
- Actionable advice for energy management and scheduling

### 📊 Comprehensive Analysis
- 24 hourly productivity scores (0-100 scale)
- Peak performance windows identification
- Optimal focus blocks for deep work
- Recovery status tracking

### 🚀 Fully Automated
- Runs daily via cron/Task Scheduler
- Zero manual intervention required
- Automatic data collection, analysis, and delivery

## Project Structure

```
productivity-intelligence-system/
├── .env                       # Your API credentials
├── requirements.txt           # Python dependencies
├── daily_workflow.py          # Main automation script
├── QUICKSTART.md             # Setup guide
├── ARCHITECTURE.md           # Technical details
│
├── src/
│   ├── data_collection/      # Intervals.icu API integration
│   ├── scoring/              # Productivity calculation
│   │   ├── circadian_model.py
│   │   ├── recovery_analyzer.py
│   │   └── productivity_calculator.py
│   ├── ai/                   # Claude AI integration
│   ├── database/             # SQLite storage
│   └── delivery/             # Google Docs posting
│
└── scripts/
    ├── setup_database.py         # Initialize database
    ├── setup_google_auth.py      # Configure Google OAuth
    ├── test_data_collection.py   # Test Intervals.icu
    ├── test_full_workflow.py     # End-to-end test
    └── view_data.py              # View stored data
```

## Technology Stack

- **Language**: Python 3.11+
- **Data Source**: Intervals.icu REST API
- **AI**: Anthropic Claude API (Sonnet 4.5)
- **Database**: SQLite
- **Delivery**: Google Docs API
- **Automation**: Cron (Linux/Mac) or Task Scheduler (Windows)

## Setup Time

- **Initial setup**: ~15 minutes
- **Daily runtime**: ~10-15 seconds
- **Maintenance**: None (fully automated)

## Cost

- **Intervals.icu**: Free
- **Claude API**: ~$0.50-1.00/month (30 daily reports)
- **Google Docs**: Free
- **Total**: < $2/month

## What You Get Each Morning

A comprehensive report in your Google Doc with:

### Recovery Summary
- Overall physiological state
- HRV, RHR, and sleep analysis
- Comparison to your personal baseline

### Peak Productivity Hours
- Top 5 hours for optimal performance
- Specific time windows with scores

### Optimal Focus Blocks
- 2-3 hour continuous windows for deep work
- Ideal for scheduling important tasks

### AI Insights
- Personalized recommendations from Claude
- Energy management strategies
- Circadian-based scheduling advice

### Action Items
- 2-3 specific things to do today
- Based on your current recovery state

## Sample Report Output

```
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

**Recovery Summary**: Your recovery is good today. HRV is
slightly elevated (+2.5ms), and resting heart rate is normal.
Sleep duration was adequate at 7.5 hours. Your body is
well-prepared for a productive day.

**Today's Optimal Windows**: Your peak cognitive performance
will occur between 9:00-12:00, with a secondary peak from
15:00-17:00. The late morning window (9-12) is ideal for your
most demanding analytical work.

**Energy Management**: Expect a natural dip around 14:00-15:00.
Use this time for lighter tasks, meetings, or a brief walk.
Avoid scheduling important decisions during this window.

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
```

## Scientific Foundation

### Circadian Rhythm Model
Based on the two-process model (Borbély, 1982):
- **Process C**: 24-hour circadian rhythm with natural peaks/troughs
- **Process S**: Homeostatic sleep pressure that builds during waking

### Recovery Metrics
Evidence-based physiological indicators:
- **HRV**: Reflects autonomic nervous system balance
- **RHR**: Indicates recovery and cardiovascular stress
- **Sleep**: Duration and quality affect cognitive performance

### Productivity Calculation
Combines multiple validated factors:
- Circadian alertness (50% weight)
- Recovery status (50% weight)
- Personalized to your baseline patterns

## Use Cases

### For Knowledge Workers
- Schedule deep work during peak cognitive hours
- Plan meetings during lower-energy windows
- Optimize daily schedule based on natural rhythms

### For Athletes
- Time training based on recovery status
- Balance intensity with physiological readiness
- Track impact of training on recovery

### For Anyone Optimizing Performance
- Understand your energy patterns
- Make data-driven scheduling decisions
- Improve work-life balance through better energy management

## Quick Start

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Configure `.env`**: Add your API keys
3. **Setup Google OAuth**: Run `python scripts/setup_google_auth.py`
4. **Initialize database**: Run `python scripts/setup_database.py`
5. **Test**: Run `python scripts/test_full_workflow.py`
6. **Go live**: Run `python daily_workflow.py`
7. **Automate**: Set up cron/Task Scheduler for 6 AM daily

See [QUICKSTART.md](QUICKSTART.md) for detailed setup instructions.

## Files Overview

### Core Application
- `daily_workflow.py` - Main automation script (run this daily)
- `.env` - Your configuration (API keys, doc ID)
- `requirements.txt` - Python dependencies

### Source Code (`src/`)
All the core logic organized by function:
- Data collection from Intervals.icu
- Productivity scoring algorithms
- Claude AI integration
- Database models and operations
- Google Docs delivery

### Setup Scripts (`scripts/`)
One-time setup and testing utilities:
- `setup_database.py` - Create database tables
- `setup_google_auth.py` - Configure Google OAuth
- `test_data_collection.py` - Verify Intervals.icu connection
- `test_full_workflow.py` - End-to-end test without delivery
- `view_data.py` - View historical data

### Documentation
- `README.md` - Project overview
- `QUICKSTART.md` - Step-by-step setup guide
- `ARCHITECTURE.md` - Technical architecture details
- `PROJECT_SUMMARY.md` - This file

## Next Steps After Setup

1. **Review First Report**: Check your first generated report
2. **Validate Patterns**: Compare scores to your actual energy levels
3. **Adjust Schedule**: Start aligning work with peak hours
4. **Track Trends**: Watch how recovery affects productivity
5. **Optimize**: Use insights to improve sleep and recovery habits

## Troubleshooting

Common issues and solutions:

**No data available**:
- Ensure Amazfit watch syncs to Zepp app
- Verify Zepp syncs to Intervals.icu
- Wait 10-15 minutes after waking for sync

**API errors**:
- Double-check API keys in `.env`
- Verify no extra spaces in keys
- Check API credits/billing (for Claude)

**Google Docs auth failed**:
- Delete `token.json`
- Re-run `setup_google_auth.py`
- Verify document permissions

See logs in `logs/daily_workflow.log` for detailed error information.

## Support & Maintenance

### Logs
- All operations logged to `logs/daily_workflow.log`
- Check this file if something goes wrong

### Viewing Data
```bash
# View recent records and stats
python scripts/view_data.py

# View specific date details
python scripts/view_data.py 2024-01-15
```

### Database
- Location: `productivity.db` (SQLite file)
- Backup: Simply copy the file
- View: Use any SQLite browser

## Future Enhancements

Potential additions:
- Weekly trend analysis
- Predictive modeling (forecast tomorrow)
- Correlation analysis (sleep quality vs productivity)
- Web dashboard for visualization
- Mobile app for quick access
- Multi-user support
- Email/Slack notifications
- Export to CSV/JSON

## License

MIT License - Free to use, modify, and distribute

## Credits

Built with:
- [Intervals.icu](https://intervals.icu) - Wellness data platform
- [Claude AI](https://anthropic.com) - AI insights generation
- [Google Docs API](https://developers.google.com/docs) - Report delivery

## Getting Help

1. Check the logs: `logs/daily_workflow.log`
2. Review documentation: `QUICKSTART.md` and `ARCHITECTURE.md`
3. Test individual components using scripts in `scripts/`
4. Verify API credentials in `.env`

---

**Ready to optimize your productivity?**

Start with: `python scripts/test_data_collection.py`

Then follow: [QUICKSTART.md](QUICKSTART.md)

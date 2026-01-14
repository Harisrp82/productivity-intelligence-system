# Productivity Intelligence System

An automated AI-powered system that analyzes your sleep, recovery, and circadian rhythm to generate personalized hourly productivity scores and daily insights.

## Features

- **Automated Data Collection**: Syncs wellness data from Amazfit watches via Intervals.icu API
- **Circadian Intelligence**: Calculates optimal productivity windows based on your natural rhythm
- **Recovery Analysis**: Factors in HRV, RHR, and sleep quality for accurate energy predictions
- **AI Insights**: Uses Claude AI to generate personalized recommendations
- **Daily Reports**: Automatically delivers insights to Google Docs every morning

## Data Flow

```
Amazfit Watch → Zepp App → Intervals.icu → System → Claude AI → Google Docs
```

## Setup

### 1. Prerequisites
- Python 3.11+
- Amazfit watch with data syncing to Intervals.icu
- Anthropic API key
- Google Cloud project with Docs API enabled

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 4. Initialize Database
```bash
python scripts/setup_database.py
```

### 5. Setup Google Authentication
```bash
python scripts/setup_google_auth.py
```

### 6. Test Data Collection
```bash
python scripts/test_data_collection.py
```

## Usage

### Manual Run
```bash
python daily_workflow.py
```

### Automated Daily Run (Linux/Mac)
Add to crontab to run daily at 6 AM:
```bash
0 6 * * * cd /path/to/project && /path/to/python daily_workflow.py
```

### Automated Daily Run (Windows)
Use Task Scheduler to run `daily_workflow.py` at 6 AM daily.

## Project Structure

- `src/data_collection/` - Intervals.icu API integration
- `src/scoring/` - Productivity calculation algorithms
- `src/ai/` - Claude AI integration
- `src/database/` - SQLite data models
- `src/delivery/` - Google Docs reporting
- `scripts/` - Setup and testing utilities

## Configuration

Edit `.env` file to customize:
- Timezone for accurate circadian calculations
- Log level for debugging
- Database location

## Troubleshooting

### No data from Intervals.icu
- Verify API key in Intervals.icu settings
- Check that Zepp app is syncing data
- Run `test_data_collection.py` to diagnose

### Google Docs authentication fails
- Re-run `setup_google_auth.py`
- Check credentials.json is present

## License

MIT

# Productivity Intelligence System

An automated AI-powered system that analyzes your sleep, recovery, and circadian rhythm to generate personalized hourly productivity scores, optimal deep work windows, and daily insights delivered to Google Docs.

## Key Features

### Data Collection
- **Google Fit Integration**: Collects wellness data directly from Google Fit API
- **Zepp/Amazfit Priority**: Automatically prioritizes data from Zepp (Amazfit) over other sources like Pillow
- **Multi-Source Support**: Falls back to other data sources when Zepp data is unavailable
- **7-Day Baseline**: Calculates rolling averages for accurate comparisons

### Adaptive Circadian Model
- **Wake-Time Based**: Energy predictions shift dynamically based on your actual wake time
- **Not Fixed Clock**: Unlike traditional models that assume 7 AM wake time, this adapts to your schedule
- **Energy Flow Prediction**: Predicts high/low energy windows relative to when you wake up:
  - **First Peak**: ~3 hours after waking (highest energy)
  - **Energy Dip**: ~7 hours after waking (natural slump)
  - **Second Peak**: ~10 hours after waking (recovery surge)
  - **Decline**: ~14+ hours after waking (fatigue sets in)

### AI-Powered Analysis
- **Deep Work Windows**: LLM analyzes your data to recommend optimal focus periods
- **Personalized Insights**: Grok AI generates daily recommendations based on your metrics
- **Recovery Analysis**: Factors in sleep quality, heart rate, and HRV for accurate predictions

### Reporting & Visualization
- **Google Docs Delivery**: Automatically posts daily reports to your Google Doc
- **Energy Flow Graphs**: Generates visual graphs showing energy levels throughout the day
- **Interactive HTML Charts**: Creates interactive Plotly charts for detailed analysis

## Data Flow

```
Amazfit Watch → Zepp App → Google Fit → System → Grok AI → Google Docs
                                ↓
                    Adaptive Circadian Model
                                ↓
                    Energy Flow Prediction
                                ↓
                    Deep Work Window Analysis
```

## Sample Report Output

```
### Quick Stats
- Sleep: 7.8 hours
- Recovery Score: 78.8/100 (excellent)
- Avg Productivity: 64.1/100

### Energy Flow (Adaptive to Wake Time)
Wake Time: 13:49 | Sleep: 7.8 hours

High Energy Windows (Best for Deep Work):
- Morning Peak: 15:18 - 18:18 (1.5 - 4.5 hours after waking)
  Energy: 95% | Best for: Deep focused work, complex problem solving
- Afternoon Peak: 22:18 - 01:18 (8.5 - 11.5 hours after waking)
  Energy: 85% | Best for: Creative work, collaboration

Low Energy Windows (Avoid Deep Work):
- Post-Lunch Dip: 19:48 - 21:48 (6 - 8 hours after waking)
  Energy: 55% | Best for: Light tasks, emails, breaks
```

## Setup

### 1. Prerequisites
- Python 3.10+
- Amazfit watch syncing to Google Fit via Zepp app
- Grok API key (or other LLM API)
- Google Cloud project with Docs API and Fitness API enabled

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```env
GROK_API_KEY=your_grok_api_key
GOOGLE_DOC_ID=your_google_doc_id
DATABASE_URL=sqlite:///productivity.db
TIMEZONE=UTC
```

### 4. Setup Google Authentication

Place your `credentials.json` from Google Cloud Console in the project root, then run:
```bash
python daily_workflow.py
```

The first run will open a browser for OAuth authentication. Tokens are saved for future use.

### 5. Verify Data Collection
```python
from src.data_collection import GoogleFitCollector

collector = GoogleFitCollector()
if collector.test_connection():
    print("Connection successful!")
```

## Usage

### Run Daily Workflow
```bash
python daily_workflow.py
```

This will:
1. Collect wellness data from Google Fit (prioritizing Zepp)
2. Calculate productivity scores using the adaptive circadian model
3. Generate energy flow predictions based on your wake time
4. Analyze optimal deep work windows using AI
5. Generate personalized insights with Grok AI
6. Deliver the report to your Google Doc

### Generate Energy Flow Graph
```python
from src.scoring.circadian_model import CircadianModel
from datetime import time

model = CircadianModel()
wake_time = time(13, 49)  # Your wake time
sleep_hours = 7.8

# Get energy flow prediction
energy_flow = model.get_energy_flow_prediction(wake_time, sleep_hours)
print(energy_flow['summary'])
```

### Automated Daily Run

**Windows (Task Scheduler):**
Create a task to run `python daily_workflow.py` at your preferred time.

**Linux/Mac (Crontab):**
```bash
0 6 * * * cd /path/to/project && python daily_workflow.py
```

## Project Structure

```
├── daily_workflow.py              # Main orchestration script
├── src/
│   ├── data_collection/
│   │   ├── google_fit_collector.py   # Google Fit API integration
│   │   └── intervals_icu_collector.py # Legacy Intervals.icu support
│   ├── scoring/
│   │   ├── circadian_model.py        # Adaptive circadian rhythm model
│   │   ├── productivity_calculator.py # Hourly productivity scoring
│   │   └── recovery_analyzer.py      # Recovery status analysis
│   ├── ai/
│   │   ├── grok_client.py            # Grok AI API client
│   │   ├── insight_generator.py      # AI insight orchestration
│   │   └── prompt_templates.py       # LLM prompts for analysis
│   ├── database/
│   │   ├── connection.py             # SQLite connection management
│   │   └── models.py                 # Data models
│   └── delivery/
│       └── google_docs.py            # Google Docs API client
├── credentials.json                  # Google OAuth credentials
├── token.json                        # Google Docs API token
├── token_fit.json                    # Google Fit API token
└── productivity.db                   # SQLite database
```

## Key Components

### Adaptive Circadian Model (`src/scoring/circadian_model.py`)

The circadian model calculates energy levels based on hours since waking:

| Hours After Wake | Energy Phase | Typical Energy Level |
|------------------|--------------|---------------------|
| 0 - 0.5 | Wake-up Ramp | 50-70% |
| 1.5 - 4.5 | First Peak | 90-95% |
| 6 - 8 | Energy Dip | 50-55% |
| 8.5 - 11.5 | Second Peak | 80-85% |
| 14+ | Decline | 40-50% |

### Data Source Priority (`src/data_collection/google_fit_collector.py`)

Sleep data is prioritized from these sources:
1. `com.huami.watch` (Zepp/Amazfit) - Primary
2. `com.huami.midong` (Zepp Life) - Secondary
3. Other sources (Pillow, etc.) - Fallback

### Deep Work Analysis (`src/ai/insight_generator.py`)

The LLM analyzes your data to provide:
- Primary deep work window (highest quality)
- Secondary deep work window (backup)
- Windows to avoid
- Daily deep work capacity estimate

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `GROK_API_KEY` | API key for Grok AI | Required |
| `GOOGLE_DOC_ID` | Target Google Doc ID | Required |
| `DATABASE_URL` | SQLite database path | `sqlite:///productivity.db` |
| `TIMEZONE` | Your timezone | `UTC` |

## Troubleshooting

### No sleep data from Zepp
- Ensure Zepp app is syncing to Google Fit
- Check Google Fit app shows sleep data
- Verify OAuth scopes include fitness.sleep.read

### Wrong data source being used
- The system logs which source is being used
- Check logs for "Using Zepp/Amazfit sleep data (preferred source)"
- If seeing other sources, verify Zepp sync is working

### Google Docs authentication fails
- Delete `token.json` and re-run to re-authenticate
- Ensure `credentials.json` has correct OAuth client

### Energy predictions seem off
- Verify wake time is being detected correctly
- Check sleep_end timestamp in wellness data
- The model assumes ~16 hours of wakefulness

## Recent Changes

### v2.0 - Adaptive Circadian Model
- Added Google Fit data collection with Zepp priority
- Implemented adaptive circadian model based on actual wake time
- Added LLM-powered deep work window analysis
- Added energy flow prediction and visualization
- Enhanced report format with energy flow section
- Added graph generation for energy visualization

## License

MIT

## Contributing

Contributions welcome! Please read the contributing guidelines before submitting PRs.

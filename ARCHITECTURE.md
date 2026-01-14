# System Architecture

Technical overview of the Productivity Intelligence System.

## Architecture Overview

```
┌─────────────────────┐
│  Amazfit Watch      │
│  (Zepp App)         │
└──────────┬──────────┘
           │ Syncs via Bluetooth
           ▼
┌─────────────────────┐
│  Intervals.icu      │
│  (Cloud Storage)    │
└──────────┬──────────┘
           │ REST API
           ▼
┌─────────────────────┐
│  Data Collection    │
│  Module             │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Scoring Engine     │
│  - Circadian Model  │
│  - Recovery Analyzer│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Claude AI          │
│  (Anthropic API)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  SQLite Database    │
│  (Local Storage)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Google Docs        │
│  (Report Delivery)  │
└─────────────────────┘
```

## Components

### 1. Data Collection (`src/data_collection/`)

**Purpose**: Fetch wellness data from Intervals.icu API

**Key Features**:
- Retrieves sleep duration, quality, start/end times
- Fetches HRV (RMSSD) and resting heart rate
- Calculates 7-day rolling baselines for comparison
- Collects recent activity data for context

**API Integration**:
- Base URL: `https://intervals.icu/api/v1`
- Authentication: Basic auth with API key
- Endpoints:
  - `/athlete/{id}/wellness/{date}` - Daily wellness metrics
  - `/athlete/{id}/activities` - Recent workouts
  - `/athlete/{id}` - Profile information

### 2. Scoring Engine (`src/scoring/`)

**Purpose**: Calculate hourly productivity scores based on circadian rhythm and recovery

#### Circadian Model

Implements the **two-process model of sleep regulation** (Borbély, 1982):

**Process C (Circadian Rhythm)**:
- Sinusoidal 24-hour cycle
- Peak alertness: ~10 AM
- Lowest alertness: ~3 AM
- Post-lunch dip: ~2:30 PM
- Amplitude: 30% influence on alertness

**Process S (Sleep Pressure)**:
- Builds up during wakefulness
- Dissipates during sleep
- Rate: Full buildup over 16 hours awake
- Adjusted for sleep deficit/surplus

**Formula**:
```python
alertness = circadian_factor * (1.0 - sleep_pressure * 0.7)
```

#### Recovery Analyzer

Calculates recovery score from physiological metrics:

**HRV (Heart Rate Variability)** - 45% weight:
- Higher HRV = better recovery
- Compared to 7-day baseline
- Z-score calculation: (current - baseline) / std_dev
- Optimal: +0.5 SD or more
- Poor: -0.5 SD or less

**RHR (Resting Heart Rate)** - 35% weight:
- Lower RHR = better recovery
- Deviation from baseline
- Optimal: -3 bpm or lower
- Poor: +3 bpm or higher

**Sleep Quality** - 20% weight:
- Duration: 7-9 hours optimal
- Quality rating: 1-5 scale (if available)
- Combined score with 70/30 weight

**Overall Recovery**:
```python
recovery = (HRV_score * 0.45) + (RHR_score * 0.35) + (Sleep_score * 0.20)
```

#### Productivity Calculator

Combines circadian and recovery into hourly scores:

```python
productivity_score = (circadian_alertness * 0.50) + (recovery_factor * 0.50)
```

Outputs:
- 24 hourly scores (0-100 scale)
- Peak productivity hours (top 5)
- Low energy hours (bottom 3)
- Optimal focus blocks (2+ consecutive hours ≥70)

### 3. AI Insights (`src/ai/`)

**Purpose**: Generate personalized insights using Claude AI

**Claude API**:
- Model: `claude-sonnet-4-5-20250929`
- Max tokens: 2000 per request
- Temperature: Default (1.0)

**Prompt Structure**:

*System Prompt*:
- Defines Claude's role as productivity coach and sleep scientist
- Provides response structure guidelines
- Sets tone (professional, actionable, honest)

*User Prompt*:
- Formatted data: sleep, HRV, RHR, productivity scores
- Baseline comparisons
- Recent activity context
- Peak hours and time blocks

**Output Sections**:
1. Recovery Summary (2-3 sentences)
2. Today's Optimal Windows (specific hours)
3. Energy Management (circadian-based guidance)
4. Recommendations (2-3 action items)

### 4. Database (`src/database/`)

**Purpose**: Store historical data for tracking and analysis

**Schema**:

```sql
-- Wellness data
CREATE TABLE wellness_records (
    id INTEGER PRIMARY KEY,
    date TEXT UNIQUE NOT NULL,
    sleep_hours REAL,
    sleep_quality INTEGER,
    resting_hr REAL,
    hrv_rmssd REAL,
    baseline_hrv REAL,
    baseline_rhr REAL,
    -- ... other metrics
);

-- Hourly scores
CREATE TABLE productivity_scores (
    id INTEGER PRIMARY KEY,
    wellness_record_id INTEGER,
    hour INTEGER NOT NULL,
    score REAL NOT NULL,
    circadian_component REAL,
    recovery_component REAL,
    FOREIGN KEY (wellness_record_id) REFERENCES wellness_records(id)
);

-- Generated reports
CREATE TABLE daily_reports (
    id INTEGER PRIMARY KEY,
    wellness_record_id INTEGER UNIQUE,
    date TEXT NOT NULL,
    full_report TEXT,
    recovery_score REAL,
    peak_hours JSON,
    delivery_status TEXT,
    FOREIGN KEY (wellness_record_id) REFERENCES wellness_records(id)
);
```

**Why SQLite?**:
- Simple, serverless, zero configuration
- Perfect for single-user application
- Portable (single file database)
- Sufficient for years of daily records
- No maintenance overhead

### 5. Delivery (`src/delivery/`)

**Purpose**: Post reports to Google Docs

**Google Docs API**:
- OAuth 2.0 authentication
- Scopes: `https://www.googleapis.com/auth/documents`
- Operations: Append text to existing document

**Flow**:
1. Load credentials from `credentials.json`
2. Check for existing token in `token.json`
3. Refresh token if expired
4. Use API to append formatted report
5. Update delivery status in database

**Why Google Docs?**:
- Accessible from any device
- Version history built-in
- Easy to search and browse past reports
- Can be shared with coaches/partners
- Familiar interface for most users

## Workflow Execution

### Main Script (`daily_workflow.py`)

Runs daily via cron/Task Scheduler:

```python
1. Load environment configuration
2. Initialize all components
3. Collect yesterday's data from Intervals.icu
4. Calculate 24 hourly productivity scores
5. Generate AI insights with Claude
6. Store results in database
7. Post report to Google Docs
8. Log results and handle errors
```

**Error Handling**:
- Each step wrapped in try-except
- Comprehensive logging to file and console
- Graceful degradation (e.g., if HRV missing, use RHR + sleep only)
- Database transactions with rollback on failure
- Retry logic for API calls (not yet implemented - TODO)

## Data Flow

### 1. Raw Data Collection
```
Intervals.icu API → wellness_data dict
- sleep_hours: 7.5
- hrv_rmssd: 65
- resting_hr: 52
- sleep_start: "2024-01-14T23:30:00"
- sleep_end: "2024-01-15T07:00:00"
```

### 2. Baseline Calculation
```
7-day rolling average
- avg_hrv: 62.5
- avg_rhr: 54.0
- avg_sleep_hours: 7.8
```

### 3. Recovery Analysis
```
Recovery Scores:
- hrv_score: 0.85 (good)
- rhr_score: 0.80 (good)
- sleep_score: 0.75 (moderate)
→ overall_recovery: 0.81 (good)
```

### 4. Circadian Calculation
```
For each hour 0-23:
- circadian_phase: 0.85
- sleep_pressure: 0.20
→ alertness: 0.82
```

### 5. Productivity Scores
```
Combined Score per hour:
(circadian * 0.5) + (recovery * 0.5)
→ 24 hourly scores (0-100 scale)
```

### 6. AI Insight Generation
```
Formatted data → Claude API → Personalized report
```

### 7. Storage & Delivery
```
Database: Store all data + report
Google Docs: Append report with formatting
```

## Performance Considerations

**API Calls**:
- Intervals.icu: ~3-4 requests per run
- Claude API: 1 request per run (~500 tokens)
- Google Docs: 1-2 requests per run

**Execution Time**:
- Data collection: ~2-3 seconds
- Calculations: <1 second
- AI generation: ~5-10 seconds
- Database operations: <1 second
- Google Docs: ~2-3 seconds
- **Total**: ~10-15 seconds

**Storage**:
- Database size: ~1-2 MB per year
- Each daily record: ~2-3 KB

**Cost Estimates** (monthly):
- Intervals.icu: Free
- Claude API: ~$0.50-1.00 (30 reports × $0.015 per 1K tokens)
- Google Docs: Free
- **Total**: <$2/month

## Security

**API Keys**:
- Stored in `.env` (not committed to git)
- Loaded via `python-dotenv`
- Never logged or exposed

**Google OAuth**:
- Credentials in `credentials.json` (gitignored)
- Access token in `token.json` (gitignored)
- Minimal scopes requested (docs only)

**Database**:
- Local SQLite file
- No sensitive data stored
- Can be encrypted at filesystem level if needed

## Extensibility

### Adding New Metrics

To add a new wellness metric:
1. Update `intervals_icu_collector.py` to fetch it
2. Add column to `WellnessRecord` model
3. Update recovery analyzer if it affects recovery
4. Include in prompt template for Claude

### Alternative Delivery Methods

Current: Google Docs

Potential:
- Email (SMTP)
- Slack notifications
- Custom web dashboard
- PDF generation
- Mobile push notifications

### Advanced Analytics

Potential features:
- Weekly/monthly trend analysis
- Correlation analysis (sleep quality vs productivity)
- Predictive modeling (next day forecast)
- Visualization dashboard
- Comparative analysis (weekdays vs weekends)

## Testing Strategy

**Unit Tests** (TODO):
- Test each component independently
- Mock external APIs
- Validate calculations

**Integration Tests**:
- `test_data_collection.py` - Intervals.icu API
- `test_full_workflow.py` - End-to-end without delivery
- `setup_google_auth.py` - Google Docs access

**Production Monitoring**:
- Log files in `logs/`
- Database delivery_status field
- Manual verification of Google Doc updates

## Dependencies

**Core**:
- `requests` - HTTP API calls
- `anthropic` - Claude AI SDK
- `sqlalchemy` - Database ORM
- `google-api-python-client` - Google Docs API
- `python-dotenv` - Environment config

**Data Processing**:
- `numpy` - Numerical calculations
- `pandas` - Data manipulation (future analytics)
- `pytz` - Timezone handling

**Why These Dependencies?**:
- Official SDKs where available (Anthropic, Google)
- Widely used, well-maintained libraries
- Minimal dependency tree
- No heavy ML frameworks (all logic is explicit)

## Future Enhancements

1. **Retry Logic**: Automatic retry on API failures
2. **Caching**: Cache API responses to reduce calls
3. **Notifications**: Alert if data collection fails
4. **Web Dashboard**: Visualize trends over time
5. **Mobile App**: Quick access to today's scores
6. **Multi-user**: Support for teams/families
7. **Advanced AI**: Trend analysis, predictions
8. **Export**: CSV/JSON export for external analysis

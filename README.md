# Modi & Patil News Tracker

An automated system to track news coverage of Narendra Modi and CR Patil across Indian news channels.

## Features

- **Automated Collection**: Fetches articles daily via NewsCatcher API.
- **Smart Storage**: Stores data in SQLite with 90-day retention.
- **Daily Reports**: Generates professional Excel reports automatically.
- **Robust Tracking**: Covers 15+ major Indian news channels in English and Hindi.
- **Resilient**: Includes retry logic, error handling, and logging.

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   Duplicate `.env.template` to `.env` and add your API key:
   ```env
   NEWSCATCHER_API_KEY=your_api_key_here
   ```

3. **Run the Application**
   ```bash
   python main.py
   ```
   The system will perform an immediate collection cycle and then schedule daily runs at 8:00 AM UTC.

## Project Structure

```
news_tracker/
├── main.py                 # Application entry point
├── config.py               # Configuration management
├── requirements.txt        # Python dependencies
├── .env                    # API keys and secrets (create this)
├── logs/                   # Application logs
├── output/                 # Generated Excel reports
└── src/
    ├── api_client.py       # NewsCatcher API integration
    ├── database.py         # SQLite database models
    ├── data_processor.py   # Data cleaning and categorization
    ├── reports.py          # Excel report generator
    ├── scheduler.py        # Task scheduling
    ├── logger.py           # Logging setup
    └── validators.py       # Input validation
```

## Configuration

Adjust settings in `.env` or `config.py`:
- `SCHEDULE_HOUR`: Hour to run daily collection (UTC)
- `DAYS_TO_KEEP`: Number of days to retain data (default: 90)
- `LOG_LEVEL`: Logging verbosity (INFO/DEBUG)

## Output

- **Database**: `news_tracker.db` (SQLite)
- **Reports**: `output/news_report_YYYYMMDD.xlsx`
- **Logs**: `logs/app.log`

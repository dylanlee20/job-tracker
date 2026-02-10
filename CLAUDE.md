# Job Tracker - Claude Context

> Auto-push enabled: Every commit automatically syncs to GitHub

## Project Overview

Automated job scraping system for financial companies. Tracks job postings from 9+ banks, detects changes, exports to Excel, and provides a web interface.

## Tech Stack

- **Backend**: Python 3.9+ / Flask
- **Database**: SQLite + SQLAlchemy
- **Scraping**: Selenium + BeautifulSoup
- **Scheduling**: APScheduler
- **Frontend**: Bootstrap 5 + jQuery

## Key Directories

```
scrapers/          # Individual company scrapers (most active development)
models/            # SQLAlchemy models (database.py, job.py)
services/          # Business logic (scraper_service, job_service, excel_service)
routes/            # Flask routes (api.py, web.py)
templates/         # Jinja2 templates
data/              # SQLite DB, exports, logs
```

## Supported Companies

JPMorgan, Goldman Sachs, Morgan Stanley, Citi, Deutsche Bank, UBS, BNP Paribas, Nomura, Piper Sandler, Jefferies, Mizuho, Blackstone, Evercore

## Recent Work (as of Feb 2026)

- Added regional scrapers: `jpmorgan_australia_scraper.py`, `jpmorgan_hongkong_scraper.py`
- Added `goldman_sachs_international_scraper.py`
- Updated `morgan_stanley_scraper.py` with scroll functionality
- Working on pagination and infinite scroll handling

## Common Tasks

### Run the app
```bash
cd ~/Desktop/job-tracker
python app.py
```

### Test a specific scraper
```bash
python -c "from scrapers.jpmorgan_scraper import JPMorganScraper; s = JPMorganScraper(); print(s.scrape_with_retry())"
```

### Check scraper structure
Each scraper inherits from `BaseScraper` in `scrapers/base_scraper.py`

## Known Issues / TODOs

- Some sites use infinite scroll - need scroll handling
- Anti-bot detection on some sites - may need delays
- Regional variants (Australia, HK, International) have different page structures

## Development Notes

- Use headless Chrome via webdriver-manager
- Delay between requests: 1-3 seconds (configurable in config.py)
- Job deduplication via MD5 hash of (company + title + location)

## Quick Recovery Checklist

1. Check `scrapers/` for most recent work
2. Check `data/logs/scraper.log` for errors
3. Run `python app.py` to test if app starts
4. Check git status for uncommitted changes

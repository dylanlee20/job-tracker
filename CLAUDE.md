# Job Tracker - Claude Context

> Auto-push enabled: Every commit automatically syncs to GitHub
> GitHub: https://github.com/dylanlee20/job-tracker (PRIVATE)

## Project Overview

Automated job scraping system for financial companies. Tracks internship/analyst job postings from 17 banks, detects changes, exports to Excel, and provides a web interface with user authentication.

## Tech Stack

- **Backend**: Python 3.9+ / Flask / Flask-Login
- **Database**: SQLite + SQLAlchemy
- **Scraping**: Selenium + BeautifulSoup
- **Scheduling**: APScheduler
- **Frontend**: Bootstrap 5 + jQuery
- **Hosting**: DigitalOcean VPS (167.71.209.9)
- **Domain**: newwhaletech.com (Cloudflare DNS)

## Key Directories

```
scrapers/          # Individual company scrapers (17 scrapers)
models/            # SQLAlchemy models (database.py, job.py, user.py)
services/          # Business logic (scraper_service, job_service, excel_service)
routes/            # Flask routes (api.py, web.py, auth.py)
templates/         # Jinja2 templates
static/            # CSS, JS files
data/              # SQLite DB, exports, logs
```

## Authentication System (Feb 2026)

- Flask-Login for session management
- Default admin: `admin` / `admin123`
- Admin panel at `/admin/users` to manage student accounts
- Password change at `/change-password`
- All routes protected with `@login_required`

### Key Auth Files
- `models/user.py` - User model with password hashing
- `routes/auth.py` - Login/logout/password change routes
- `templates/login.html`, `templates/admin_users.html`

## Supported Companies (17 Scrapers)

| Company | Scraper File | Career URL | Filters |
|---------|--------------|------------|---------|
| JPMorgan - US | `jpmorgan_scraper.py` | Oracle Cloud | US, Intern |
| JPMorgan - Australia | `jpmorgan_australia_scraper.py` | Oracle Cloud | Australia, Intern |
| JPMorgan - Hong Kong | `jpmorgan_hongkong_scraper.py` | Oracle Cloud | Hong Kong, Intern |
| Goldman Sachs - US | `goldman_scraper.py` | higher.gs.com | Americas |
| Goldman Sachs - Intl | `goldman_sachs_international_scraper.py` | higher.gs.com | EMEA + APAC |
| Morgan Stanley | `morgan_stanley_scraper.py` | Taleo | Americas, Analyst/Intern |
| Citi | `citi_scraper.py` | jobs.citi.com | US, Campus |
| Deutsche Bank | `deutsche_bank_scraper.py` | careers.db.com | Americas, Students |
| UBS | `ubs_scraper.py` | jobs.ubs.com | Americas, Internship |
| BNP Paribas | `bnp_paribas_scraper.py` | group.bnpparibas | Americas, Internship |
| Nomura | `nomura_scraper.py` | nomura.com | Americas, Early Careers |
| Evercore | `evercore_scraper.py` | Workday | Analyst/Intern |
| Blackstone | `blackstone_scraper.py` | Workday | Campus |
| Piper Sandler | `piper_sandler_scraper.py` | pipersandler.com | Campus/Intern |
| Jefferies | `jefferies_scraper.py` | Workday | Analyst/Intern |
| Mizuho | `mizuho_scraper.py` | Workday | Americas |
| Barclays | `barclays_scraper.py` | jobs.barclays | Americas, Intern |

## Recent Fixes (Feb 2026)

### Scraping Progress Tracking
- **Problem**: Progress showed "0/0" forever
- **Fix**: Initialize progress immediately in `run_all_scrapers_async()` before starting thread
- **Files**: `services/scraper_service.py`, `static/js/main.js`

### Thread-Safe Progress
- Uses `threading.Lock()` for all progress updates
- Deep copies lists to avoid race conditions
- Auto-resets stuck states

## Deployment

### VPS Commands (DigitalOcean Console)
```bash
# Update and restart
cd /opt/job-tracker && git pull && pkill -f "python app.py" && nohup python3 app.py > output.log 2>&1 &

# View logs
tail -f /opt/job-tracker/output.log
tail -f /opt/job-tracker/data/logs/scraper.log
```

### Domain Setup (Pending)
- Need Nginx reverse proxy on VPS (Flask runs on port 5000, Cloudflare expects 80/443)
- SSL certificate via Certbot

## Common Tasks

### Run the app locally
```bash
cd ~/Desktop/job-tracker
python3 app.py
```

### Test a specific scraper
```bash
python -c "from scrapers.jpmorgan_scraper import JPMorganScraper; s = JPMorganScraper(); print(s.scrape_with_retry())"
```

### Deploy changes
1. Commit on Mac (auto-pushes to GitHub)
2. On VPS: `cd /opt/job-tracker && git pull && pkill -f "python app.py" && nohup python3 app.py > output.log 2>&1 &`

## API Endpoints

- `POST /api/scrape` - Trigger scraping (async: true for background)
- `GET /api/scrape/progress` - Get scraping progress
- `GET /api/jobs` - List jobs with filters
- `GET /api/export` - Export to Excel
- `GET /api/stats` - Get statistics

## Development Notes

- Use headless Chrome via webdriver-manager
- Delay between requests: 1-3 seconds (configurable in config.py)
- Job deduplication via MD5 hash of (company + title + location)
- Each scraper inherits from `BaseScraper` in `scrapers/base_scraper.py`

## Related Documentation

- `WORKFLOW.md` - Step-by-step deployment workflow
- `RECOVERY.md` - How to recover from crashes
- `DEPLOYMENT.md` - VPS setup guide

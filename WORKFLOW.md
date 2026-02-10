# Job Tracker Workflow Guide

## Architecture Overview
```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│  Your Mac   │────▶│   GitHub    │────▶│  DigitalOcean   │
│ (Edit Code) │     │   (Storage) │     │  VPS (Live App) │
└─────────────┘     └─────────────┘     └─────────────────┘
```

---

## Quick Reference

### Access Points
| Environment | URL |
|------------|-----|
| Local | http://localhost:5000 |
| VPS | http://167.71.209.9:5000 |
| Domain (pending) | http://newwhaletech.com |

### Default Login
- **Username:** admin
- **Password:** admin123

---

## Step-by-Step Workflow

### 1. Edit Code (Your Mac)
**Location:** `~/Desktop/job-tracker`

```bash
cd ~/Desktop/job-tracker
# Edit files as needed
# Test locally (optional):
python3 app.py
```

### 2. Commit & Push (Auto-pushes to GitHub)
```bash
cd ~/Desktop/job-tracker
git add .
git commit -m "Your change description"
# Auto-push hook sends to GitHub automatically
```

### 3. Deploy to VPS
Open **DigitalOcean Console** (cloud.digitalocean.com → Droplets → job-tracker-v1 → Console)

```bash
cd /opt/job-tracker && git pull && pkill -f "python app.py" && nohup python3 app.py > output.log 2>&1 &
```

### 4. Verify Deployment
```bash
# On VPS - check app is running
curl -I http://localhost:5000/
# Should show: HTTP/1.1 302 FOUND (redirect to /login)
```

---

## Common Commands

### On Your Mac
```bash
# Run app locally
cd ~/Desktop/job-tracker && python3 app.py

# Check git status
git status

# View recent commits
git log --oneline -5
```

### On VPS (via DigitalOcean Console)
```bash
# Update and restart app
cd /opt/job-tracker && git pull && pkill -f "python app.py" && nohup python3 app.py > output.log 2>&1 &

# View app logs
tail -f /opt/job-tracker/output.log

# View scraper logs
tail -f /opt/job-tracker/data/logs/scraper.log

# Check if app is running
ps aux | grep python

# Restart app only (no git pull)
pkill -f "python app.py" && cd /opt/job-tracker && nohup python3 app.py > output.log 2>&1 &
```

---

## Platforms & Services

| Platform | Purpose | URL |
|----------|---------|-----|
| GitHub | Code storage | github.com/dylanlee20/job-tracker |
| DigitalOcean | VPS hosting | cloud.digitalocean.com |
| Cloudflare | DNS management | dash.cloudflare.com |
| Northwest RA | Domain registrar | northwestregisteredagent.com |

---

## App Features

### Scrapers (17 Companies)
- JPMorgan (US, Australia, Hong Kong)
- Goldman Sachs (US, International)
- Morgan Stanley
- Citi
- Deutsche Bank
- UBS
- BNP Paribas
- Nomura
- Evercore
- Blackstone
- Piper Sandler
- Jefferies
- Mizuho
- Barclays

### User Management
- Admin can create/delete student accounts
- Users can change their own passwords
- All pages require login

### Scheduled Tasks
- Daily scraping at configured time
- Manual "Scrape Now" button available

---

## Troubleshooting

### VPS Not Responding
```bash
# Check if app is running
ps aux | grep python

# Restart the app
pkill -f "python app.py"
cd /opt/job-tracker
nohup python3 app.py > output.log 2>&1 &
```

### Git Pull Issues on VPS
```bash
# If git pull fails, do a fresh clone
cd /opt
mv job-tracker job-tracker-backup
git clone https://github.com/dylanlee20/job-tracker.git
cp job-tracker-backup/data/jobs.db job-tracker/data/
mkdir -p job-tracker/data/logs
pip3 install --break-system-packages -r job-tracker/requirements.txt
cd job-tracker && nohup python3 app.py > output.log 2>&1 &
```

### SSH Not Working
Use DigitalOcean Console instead:
1. Go to cloud.digitalocean.com
2. Click on your droplet (job-tracker-v1)
3. Click "Console" button

---

## File Structure
```
job-tracker/
├── app.py                 # Main Flask app
├── config.py              # Configuration
├── requirements.txt       # Python dependencies
├── CLAUDE.md             # Context for Claude AI
├── WORKFLOW.md           # This file
├── RECOVERY.md           # Recovery instructions
├── DEPLOYMENT.md         # Deployment guide
├── data/
│   ├── jobs.db           # SQLite database
│   └── logs/             # Log files
├── models/               # Database models
├── routes/               # API & web routes
├── scrapers/             # Company scrapers
├── services/             # Business logic
├── templates/            # HTML templates
└── static/               # CSS, JS, images
```

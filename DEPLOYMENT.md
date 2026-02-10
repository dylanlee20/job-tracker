# Deployment Guide

## Option 1: Run Locally

### First Time Setup

```bash
# Clone from GitHub
git clone https://github.com/dylanlee20/job-tracker.git
cd job-tracker

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

Open http://127.0.0.1:5000 in your browser.

### Daily Use

```bash
cd ~/Desktop/job-tracker
source venv/bin/activate  # If using virtual environment
python app.py
```

---

## Option 2: Deploy to Railway (Free, Recommended)

Railway offers a generous free tier and easy deployment.

### Step 1: Prepare the App

Create these files in your project:

**Procfile** (tells Railway how to run the app):
```
web: python app.py
```

**runtime.txt** (Python version):
```
python-3.11
```

### Step 2: Deploy

1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select `dylanlee20/job-tracker`
5. Railway auto-detects Python and deploys

### Step 3: Configure

In Railway dashboard:
- Add environment variable: `PORT=5000`
- Your app will be live at `https://your-app.railway.app`

---

## Option 3: Deploy to Render (Free)

### Step 1: Create render.yaml

```yaml
services:
  - type: web
    name: job-tracker
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python app.py
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
```

### Step 2: Deploy

1. Go to https://render.com
2. Sign up with GitHub
3. Click "New" → "Web Service"
4. Connect your `job-tracker` repo
5. Render auto-deploys

---

## Option 4: Deploy to PythonAnywhere (Free)

Good for beginners, has a free tier.

### Step 1: Sign Up

Go to https://www.pythonanywhere.com and create a free account.

### Step 2: Upload Code

```bash
# In PythonAnywhere console
git clone https://github.com/dylanlee20/job-tracker.git
cd job-tracker
pip install -r requirements.txt
```

### Step 3: Configure Web App

1. Go to "Web" tab
2. Click "Add a new web app"
3. Choose Flask
4. Set source code path to `/home/yourusername/job-tracker`
5. Set WSGI file to point to `app.py`

---

## Comparison

| Feature | Local | Railway | Render | PythonAnywhere |
|---------|-------|---------|--------|----------------|
| Cost | Free | Free tier | Free tier | Free tier |
| Always on | No | Yes | Yes | Yes |
| Auto-scraping | When running | 24/7 | 24/7 | 24/7 |
| Custom domain | localhost | Yes | Yes | Paid |
| Difficulty | Easiest | Easy | Easy | Medium |

## Recommendation

- **Just starting out**: Run locally
- **Want 24/7 scraping**: Deploy to Railway (easiest cloud option)
- **Sharing with others**: Deploy to Railway or Render

---

## Updating Your Deployed App

Once deployed, updates are automatic:

1. Make changes locally
2. Commit: `git add -A && git commit -m "your message"`
3. Auto-push syncs to GitHub
4. Railway/Render auto-redeploys from GitHub

Your cloud app stays in sync with your code!

#!/bin/bash
# VPS Setup Script for Job Tracker
# Run this on a fresh Ubuntu 24.04 server

set -e

echo "=== Job Tracker VPS Setup ==="

# Update system
echo "[1/7] Updating system..."
apt update && apt upgrade -y

# Install Python and pip
echo "[2/7] Installing Python..."
apt install -y python3 python3-pip python3-venv

# Install Chrome dependencies
echo "[3/7] Installing Chrome..."
apt install -y wget gnupg2
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
apt update
apt install -y google-chrome-stable

# Install additional dependencies
echo "[4/7] Installing dependencies..."
apt install -y git supervisor

# Clone the repository
echo "[5/7] Cloning repository..."
cd /opt
git clone https://github.com/dylanlee20/job-tracker.git
cd job-tracker

# Set up Python environment
echo "[6/7] Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create data directories
mkdir -p data/logs data/exports

# Create systemd service
echo "[7/7] Creating systemd service..."
cat > /etc/systemd/system/job-tracker.service << 'EOF'
[Unit]
Description=Job Tracker Flask Application
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/job-tracker
Environment=PATH=/opt/job-tracker/venv/bin:/usr/bin
ExecStart=/opt/job-tracker/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
systemctl daemon-reload
systemctl enable job-tracker
systemctl start job-tracker

# Set up auto-update cron job (pulls from GitHub every hour)
echo "0 * * * * cd /opt/job-tracker && git pull && systemctl restart job-tracker" | crontab -

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "Your app is now running at: http://$(curl -s ifconfig.me):5000"
echo ""
echo "Useful commands:"
echo "  Check status:  systemctl status job-tracker"
echo "  View logs:     journalctl -u job-tracker -f"
echo "  Restart:       systemctl restart job-tracker"
echo "  Manual update: cd /opt/job-tracker && git pull && systemctl restart job-tracker"
echo ""

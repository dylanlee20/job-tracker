#!/bin/bash
# One-time setup for GitHub Actions auto-deploy to VPS
# Run this from your Mac: bash scripts/setup-auto-deploy.sh

set -e

KEY_PATH="$HOME/.ssh/job_tracker_deploy"
VPS_HOST="167.71.209.9"
VPS_USER="root"

echo "================================================================"
echo "  GitHub Actions Auto-Deploy Setup for job-tracker"
echo "================================================================"
echo ""

# Step 1: Generate deploy key
if [ -f "$KEY_PATH" ]; then
    echo "[1/4] SSH key already exists at $KEY_PATH — reusing it"
else
    echo "[1/4] Generating new SSH key for GitHub Actions..."
    ssh-keygen -t ed25519 -f "$KEY_PATH" -N "" -C "github-actions-deploy@job-tracker"
fi
echo ""

# Step 2: Show public key for VPS
echo "[2/4] PUBLIC KEY — copy this and paste into the VPS:"
echo "----------------------------------------------------------------"
cat "${KEY_PATH}.pub"
echo "----------------------------------------------------------------"
echo ""
echo "  On VPS (use DigitalOcean console if SSH refused):"
echo "    mkdir -p ~/.ssh && chmod 700 ~/.ssh"
echo "    echo '<paste-public-key-above>' >> ~/.ssh/authorized_keys"
echo "    chmod 600 ~/.ssh/authorized_keys"
echo ""
read -p "Press ENTER once the public key is added to the VPS..."

# Step 3: Test SSH connection
echo ""
echo "[3/4] Testing SSH connection..."
if ssh -i "$KEY_PATH" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 "${VPS_USER}@${VPS_HOST}" 'echo "SSH OK on $(hostname)"'; then
    echo "  Connection successful"
else
    echo "  Connection failed — check public key was added correctly to /root/.ssh/authorized_keys on VPS"
    exit 1
fi
echo ""

# Step 4: Show GitHub secrets to add
echo "[4/4] GITHUB SECRETS — add these at:"
echo "  https://github.com/dylanlee20/job-tracker/settings/secrets/actions"
echo ""
echo "  Click 'New repository secret' three times and add:"
echo ""
echo "  Name:  VPS_HOST"
echo "  Value: $VPS_HOST"
echo ""
echo "  Name:  VPS_USER"
echo "  Value: $VPS_USER"
echo ""
echo "  Name:  VPS_SSH_KEY"
echo "  Value: (paste the FULL private key below, including BEGIN/END lines)"
echo "----------------------------------------------------------------"
cat "$KEY_PATH"
echo "----------------------------------------------------------------"
echo ""
echo "================================================================"
echo "  Setup complete!"
echo "================================================================"
echo ""
echo "  Next push to master will auto-deploy. Watch progress at:"
echo "  https://github.com/dylanlee20/job-tracker/actions"
echo ""
echo "  Manual trigger any time:"
echo "  https://github.com/dylanlee20/job-tracker/actions/workflows/deploy.yml"

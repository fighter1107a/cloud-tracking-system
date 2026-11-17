#!/usr/bin/env bash
# ==============================================================================
# Amazon EC2 Provisioning Script for Tracking System
# Target OS: Ubuntu 22.04 LTS / 24.04 LTS (t2.micro / t3.micro Free Tier)
# ==============================================================================
set -e

echo "=== [1/6] Updating system packages ==="
sudo apt-get update -y && sudo apt-get upgrade -y
sudo apt-get install -y git python3 python3-pip python3-venv nginx postgresql-client curl

echo "=== [2/6] Setting up project directory ==="
cd /home/ubuntu
if [ ! -d "tracking-system" ]; then
    echo "Cloning repository or copying files..."
    # Replace with your actual GitHub repository URL
    # git clone https://github.com/your-username/cloud-tracking-system.git tracking-system
    mkdir -p tracking-system
fi

cd /home/ubuntu/tracking-system

echo "=== [3/6] Setting up Python 3 virtual environment ==="
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

echo "=== [4/6] Configuring systemd service ==="
sudo cp aws/systemd/tracking-system.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tracking-system
sudo systemctl restart tracking-system

echo "=== [5/6] Configuring Nginx reverse proxy ==="
sudo cp aws/nginx/tracking-system.conf /etc/nginx/sites-available/tracking-system
sudo ln -sf /etc/nginx/sites-available/tracking-system /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo "=== [6/6] Verifying service status ==="
sudo systemctl status tracking-system --no-pager
curl -s http://127.0.0.1:8000/health | python3 -m json.tool

echo "=== EC2 Provisioning Complete! ==="

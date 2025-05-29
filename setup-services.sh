#!/bin/bash
# EconCell Service Setup Script

set -e

echo "Setting up EconCell systemd services..."

# Create log directory
sudo mkdir -p /var/log/econcell
sudo chown websinthe:websinthe /var/log/econcell

# Copy service files
sudo cp econcell-api.service /etc/systemd/system/
sudo cp econcell-scheduler.service /etc/systemd/system/
sudo cp econcell-monitor.service /etc/systemd/system/
sudo cp econcell-monitor.timer /etc/systemd/system/

# Set up logrotate
sudo cp logrotate-econcell /etc/logrotate.d/econcell

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable econcell-api.service
sudo systemctl enable econcell-scheduler.service
sudo systemctl enable econcell-monitor.timer

# Start services
sudo systemctl start econcell-api.service
sudo systemctl start econcell-scheduler.service
sudo systemctl start econcell-monitor.timer

# Check status
echo -e "\nService Status:"
sudo systemctl status econcell-api.service --no-pager
sudo systemctl status econcell-scheduler.service --no-pager
sudo systemctl status econcell-monitor.timer --no-pager

echo -e "\nSetup complete! Services are running and will start on boot."
echo "Logs are available at /var/log/econcell/"
echo "To view logs: journalctl -u econcell-api -f"
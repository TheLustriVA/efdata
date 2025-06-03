# EFData Service Configuration

This directory contains systemd service files and deployment scripts for the EFData platform.

## Service Files

### Systemd Services
- `econcell-api.service` - REST API service
- `econcell-scheduler.service` - Spider scheduler service  
- `econcell-monitor.service` - System monitoring service
- `econcell-monitor.timer` - Timer for monitoring service

### Setup Scripts
- `setup-services.sh` - Main service installation script
- `setup-mindsdb.sh` - MindsDB integration setup
- `mindsdb-econcell-compose.yml` - Docker compose for MindsDB

### Configuration
- `logrotate-econcell` - Log rotation configuration

## Installation

To install the systemd services:

```bash
sudo ./setup-services.sh
```

This will:
1. Copy service files to `/etc/systemd/system/`
2. Enable and start the services
3. Set up log rotation

## Managing Services

```bash
# Check status
sudo systemctl status econcell-api
sudo systemctl status econcell-scheduler

# View logs
sudo journalctl -u econcell-api -f
sudo journalctl -u econcell-scheduler -f

# Restart services
sudo systemctl restart econcell-api
sudo systemctl restart econcell-scheduler
```
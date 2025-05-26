# Spider Scheduler Documentation

This document describes the scheduling system for the EconCell Scrapy spiders using APScheduler.

## Overview

The Spider Scheduler manages automated execution of two Scrapy spiders:

1. **RBA Tables Spider** (`rba_tables`): Downloads CSV files from RBA statistics tables
2. **XR API Currencies Spider** (`xrapi-currencies`): Fetches currency exchange rates from API

## Schedule

- **RBA Tables Spider**: Runs weekly on **Saturday at 01:00 UTC+10** (Australia/Brisbane)
- **XR API Currencies Spider**: Runs **daily at 01:00 UTC+10** (Australia/Brisbane)

## Prerequisites

1. **Dependencies**: Ensure all required packages are installed

   ```bash
   # From the project root directory
   pip install -e .
   ```

2. **Environment Variables**: Set up required environment variables

   ```bash
   # For XR API Spider - add to your .env file or export
   export XR_API_KEY="your_exchange_rate_api_key"
   export XR_BASE_CURRENCY="AUD"  # Optional, defaults to AUD
   ```

3. **Database**: Ensure PostgreSQL is running and configured (if using database pipelines)

## Installation & Setup

### 1. Install Dependencies

```bash
# From project root
pip install -e .
```

### 2. Make Scripts Executable

```bash
chmod +x src/scheduler/start_scheduler.py
```

### 3. Test Individual Spiders

Before setting up the scheduler, test each spider individually:

```bash
# Test RBA Tables spider
python src/scheduler/start_scheduler.py test-rba

# Test XR API Currencies spider  
python src/scheduler/start_scheduler.py test-xrapi
```

## Running the Scheduler

### Option 1: Foreground Mode (Development/Testing)

Run the scheduler in the foreground to see logs directly:

```bash
python src/scheduler/start_scheduler.py foreground
```

### Option 2: Daemon Mode

Run the scheduler as a background daemon:

```bash
# Start daemon
python src/scheduler/start_scheduler.py start

# Check status
python src/scheduler/start_scheduler.py status

# Stop daemon
python src/scheduler/start_scheduler.py stop

# Restart daemon
python src/scheduler/start_scheduler.py restart
```

### Option 3: Systemd Service (Recommended for Production)

1. **Copy the service file**:

   ```bash
   sudo cp src/scheduler/spider-scheduler.service /etc/systemd/system/
   ```

2. **Edit the service file** to match your environment:

   ```bash
   sudo nano /etc/systemd/system/spider-scheduler.service
   ```

   Update these paths if necessary:
   - `WorkingDirectory`: Path to your project
   - `ExecStart`: Path to Python and your project
   - `User` and `Group`: Your username
   - Environment variables (especially `XR_API_KEY`)

3. **Enable and start the service**:

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable spider-scheduler
   sudo systemctl start spider-scheduler
   ```

4. **Check service status**:

   ```bash
   sudo systemctl status spider-scheduler
   sudo journalctl -u spider-scheduler -f  # Follow logs
   ```

## Process Control Options

The scheduler I built supports multiple operational modes:

| Command | Purpose |
|---------|---------|
| foreground | Run in terminal (what you're doing now) |
| start | Run as background daemon |
| stop | Stop background daemon |
| status | Check daemon status |
| test-rba | Test RBA spider once |
| test-xrapi | Test XR API spider once |

## Configuration

### Environment Variables

- `XR_API_KEY`: Your ExchangeRate-API key (required for XR API spider)
- `XR_BASE_CURRENCY`: Base currency for exchange rates (default: "AUD")
- `LOG_LEVEL`: Logging level (default: "INFO")

### Timezone

The scheduler uses **Australia/Brisbane** timezone (UTC+10). This handles daylight saving time automatically.

### Schedule Modification

To modify the schedules, edit [`spider_scheduler.py`](spider_scheduler.py) in the `setup_schedules()` method:

```python
# Example: Change RBA spider to run on Fridays at 2 AM
self.scheduler.add_job(
    func=self.run_rba_spider,
    trigger=CronTrigger(
        day_of_week='fri',  # Friday instead of Saturday
        hour=2,             # 02:00 instead of 01:00
        minute=0,
        timezone=TIMEZONE
    ),
    # ... other parameters
)
```

## Logging

### Log Files

- **Scheduler logs**: `src/scheduler/scheduler.log`
- **System logs** (if using systemd): `journalctl -u spider-scheduler`

### Log Rotation

The scheduler uses rotating log files (10MB max, 5 backups) to prevent disk space issues.

### Log Levels

- `INFO`: Normal operation, schedule execution
- `WARNING`: Non-critical issues (spider already running, etc.)
- `ERROR`: Failures and exceptions

## Troubleshooting

### Common Issues

1. **"Spider already running" warnings**:
   - This is normal if a spider takes longer than expected
   - The scheduler prevents overlapping executions

2. **Permission errors**:
   - Ensure the user has write access to the project directory
   - Check file permissions on scripts and log files

3. **Import errors**:
   - Verify Python path includes the project src directory
   - Check that all dependencies are installed

4. **Database connection errors**:
   - Ensure PostgreSQL is running
   - Verify database connection settings in Scrapy settings

### Debug Mode

Run with debug logging:

```bash
LOG_LEVEL=DEBUG python src/scheduler/start_scheduler.py foreground
```

### Manual Spider Execution

Test spiders manually from the Scrapy project directory:

```bash
cd src/econdata
scrapy crawl rba_tables
scrapy crawl xrapi-currencies
```

## File Structure

```bash
src/scheduler/
├── __init__.py              # Package initialization
├── spider_scheduler.py      # Main scheduler implementation
├── start_scheduler.py       # Daemon management script
├── config.py               # Configuration settings
├── spider-scheduler.service # Systemd service file
├── README.md               # This documentation
└── scheduler.log           # Log file (created at runtime)
```

## Security Considerations

1. **Environment Variables**: Store sensitive data (API keys) in environment variables, not in code
2. **File Permissions**: Restrict access to log files and PID files
3. **User Isolation**: Run the scheduler as a non-privileged user
4. **Network Access**: The spiders require internet access for data fetching

## Monitoring

### Health Checks

Monitor the scheduler with:

```bash
# Check if scheduler is running
python src/scheduler/start_scheduler.py status

# Check systemd service
sudo systemctl is-active spider-scheduler

# View recent logs
tail -f src/scheduler/scheduler.log
```

### Alerts

Consider setting up monitoring alerts for:

- Scheduler process failures
- Spider execution failures
- Log file errors
- Disk space usage (for log files)

## Schedule Summary

| Spider | Frequency | Time | Timezone | Description |
|--------|-----------|------|----------|-------------|
| `rba_tables` | Weekly | Saturday 01:00 | UTC+10 | RBA statistics tables |
| `xrapi-currencies` | Daily | 01:00 | UTC+10 | Currency exchange rates |

Both schedules use Australia/Brisbane timezone which automatically handles daylight saving time transitions.

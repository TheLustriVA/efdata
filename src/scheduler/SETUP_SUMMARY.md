# Spider Scheduler Setup Summary

## Files Created

The following files have been created for the Spider Scheduler system:

### Core Scheduler Files

- **`src/scheduler/__init__.py`** - Package initialization
- **`src/scheduler/spider_scheduler.py`** - Main scheduler implementation with APScheduler
- **`src/scheduler/start_scheduler.py`** - Daemon management script
- **`src/scheduler/config.py`** - Configuration settings

### Service & Documentation

- **`src/scheduler/spider-scheduler.service`** - Systemd service file for production deployment
- **`src/scheduler/README.md`** - Comprehensive documentation
- **`src/scheduler/.env.example`** - Environment variable template
- **`src/scheduler/SETUP_SUMMARY.md`** - This summary document

### Dependencies Added

- **`pyproject.toml`** - Updated with APScheduler and pytz dependencies

## Schedule Configuration

| Spider | Name | Frequency | Time | Description |
|--------|------|-----------|------|-------------|
| RBA Tables | `rba_tables` | Weekly | Saturday 01:00 UTC+10 | Downloads CSV files from RBA statistics |
| XR API Currencies | `xrapi-currencies` | Daily | 01:00 UTC+10 | Fetches exchange rates from API |

## Quick Start

1. **Install dependencies**:

   ```bash
   pip install -e .
   ```

2. **Set up environment** (optional for XR API spider):

   ```bash
   cp src/scheduler/.env.example .env
   # Edit .env with your XR_API_KEY
   ```

3. **Test the scheduler**:

   ```bash
   # Test in foreground (development)
   python src/scheduler/start_scheduler.py foreground
   
   # Test individual spiders
   python src/scheduler/start_scheduler.py test-rba
   python src/scheduler/start_scheduler.py test-xrapi
   ```

4. **Run as daemon**:

   ```bash
   # Start daemon
   python src/scheduler/start_scheduler.py start
   
   # Check status
   python src/scheduler/start_scheduler.py status
   
   # Stop daemon
   python src/scheduler/start_scheduler.py stop
   ```

## Production Deployment

For production use, install as a systemd service:

```bash
# Copy service file
sudo cp src/scheduler/spider-scheduler.service /etc/systemd/system/

# Edit service file with your paths and API keys
sudo nano /etc/systemd/system/spider-scheduler.service

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable spider-scheduler
sudo systemctl start spider-scheduler

# Check status
sudo systemctl status spider-scheduler
```

## Features Implemented

### ✅ Timezone Support

- Uses Australia/Brisbane timezone (UTC+10)
- Handles daylight saving time automatically

### ✅ Concurrency Control

- Prevents overlapping spider executions
- Thread-safe operation with locks

### ✅ Error Handling

- Comprehensive logging to files and console
- Graceful shutdown on signals (SIGTERM, SIGINT)
- Subprocess-based spider execution for reliability

### ✅ Flexible Execution

- Daemon mode for background operation
- Foreground mode for development/testing
- Individual spider testing capabilities
- Systemd service integration

### ✅ Configuration Management

- Environment variable support
- Configurable schedules and settings
- Logging configuration with rotation

## Next Steps

1. **Test the system** with your actual API keys and database setup
2. **Monitor logs** during initial operation to ensure everything works correctly
3. **Set up monitoring** for production use (disk space, process health, etc.)
4. **Configure backups** for any data collected by the spiders

The scheduler is now ready for use!

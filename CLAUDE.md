# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EconCell (Economic Simulation System/E2S2) is an advanced economic modeling platform that integrates locally-hosted LLMs, GPU-accelerated simulations, and automated data collection from Australian economic sources (RBA, ABS). The system implements cellular automata modeling based on the RBA circular flow framework.

## Common Development Commands

### Testing & Code Quality
```bash
# Run tests
pytest -v --tb=short

# Format code
black --line-length 100 src/

# Sort imports
isort --profile black --line-length 100 src/

# Lint code
flake8 src/

# Type checking
mypy --python-version 3.12 src/
```

### Running Services
```bash
# Start scheduler daemon
python src/scheduler/start_scheduler.py start

# Run scheduler in foreground (for debugging)
python src/scheduler/start_scheduler.py foreground

# Test individual spiders
python src/scheduler/start_scheduler.py test-rba
python src/scheduler/start_scheduler.py test-xrapi
python src/scheduler/start_scheduler.py test-abs

# Dry-run test for ABS spider (safe testing)
python src/scheduler/start_scheduler.py test-abs-dry

# Start API server
uvicorn frontend.api:app --reload --port 7001

# Start API server using virtual environment
/home/websinthe/code/econcell/.venv/bin/python -m uvicorn frontend.api:app --host 0.0.0.0 --port 7001

# Test AI system
python test_ai_system.py
```

### Database Operations
```bash
# Run spiders manually (from src/econdata directory)
cd src/econdata
scrapy crawl rba_tables
scrapy crawl xrapi-currencies
scrapy crawl abs_gfs

# Run ABS spider in test mode
scrapy crawl abs_gfs -a test_mode=True

# Database initialization
psql -U postgres -f debug/rba_circular_flow_postgresql_ddl.sql
psql -U postgres -d econdata -f src/econdata/sql/abs_taxation_schema.sql

# Create test schema for dry-run testing
psql -U postgres -d econdata -f src/econdata/sql/abs_test_schema.sql

# Check database state
psql -U websinthe -d econdata -f debug/check_database_state.sql

# Validate ABS test results
psql -d econdata -c 'SELECT * FROM abs_staging_test.validate_test_results();'
```

### SystemD Service Management
```bash
# Install services (requires sudo)
sudo ./setup-services.sh

# Service management
sudo systemctl start econcell-api
sudo systemctl start econcell-scheduler
sudo systemctl status econcell-api

# View logs
sudo journalctl -u econcell-api -f
tail -f /var/log/econcell/api.log
```

## Architecture Overview

### Core Components

1. **Data Ingestion Layer** (`src/econdata/`)
   - Scrapy spiders for RBA, ABS, and exchange rate data
   - **RBA Spider**: Weekly collection of economic indicators (CSV format)
   - **ABS Spider**: Monthly collection of taxation data (XLSX format)
   - **XR Spider**: Daily exchange rate updates (JSON API)
   - Pipelines for data validation and enrichment
   - PostgreSQL storage with dimensional modeling

2. **AI System** (`src/ai/`)
   - `AICoordinator`: Central orchestration of multiple LLMs
   - `ModelOrchestrator`: Manages Qwen 32B, Llama 70B, and specialized models
   - `TaskQueue`: Priority-based async task processing
   - `LoadBalancer`: Intelligent model selection based on task type
   - `MemoryManager`: GPU/RAM allocation and pooling

3. **Database Schema**
   - **rba_staging**: Raw CSV imports from RBA
   - **abs_staging**: Government finance statistics from ABS
   - **rba_dimensions**: Time, components, sources reference data
   - **abs_dimensions**: Tax types and government levels
   - **rba_facts**: Core economic measurements and flows
   - **rba_analytics**: Analytical views and functions
   - Implements circular flow components (Y, C, S, I, G, T, X, M)

4. **API Layer** (`frontend/api.py`)
   - FastAPI endpoints for economic data access
   - Analysis request handling
   - Visualization serving

5. **Scheduler** (`src/scheduler/`)
   - APScheduler-based automation
   - Weekly RBA data collection (Saturdays at 1AM)
   - Daily exchange rate updates (1AM)
   - Monthly ABS taxation data (15th at 2AM)

### Key Configuration Files

- **AI Configuration**: `config/ai_config.json` - Model specs, resource limits, and task routing
- **Scrapy Settings**: `src/econdata/econdata/settings.py` - Spider configurations
- **Scheduler Config**: `src/scheduler/config.py` - Collection schedules
- **ABS Spider Config**: Built into spider with 300s timeout for large XLSX files

### Database Setup

The PostgreSQL schema is defined in `debug/rba_circular_flow_postgresql_ddl.sql`. The system uses a star schema optimized for economic time series analysis with:
- Staging tables for each RBA dataset (H1-GDP, H2-Household, I1-Trade, etc.)
- Dimensional modeling for efficient querying
- Data quality tracking and lineage

### Development Patterns

1. **Multi-Model Consensus**: Critical analyses verified across multiple LLMs
2. **Memory Pool Management**: Efficient GPU resource allocation
3. **ETL Pipeline**: Staging → Dimensions → Facts → Analytics flow
4. **Task Priority System**: Economic indicators prioritized by importance
5. **Circular Flow Model**: All data mapped to RBA circular flow components

### Testing Strategies

#### ABS Spider Dry-Run Testing
The ABS spider includes a comprehensive test mode to safely validate functionality:

1. **Test Mode Features**:
   - Limited to 1 file download
   - Maximum 10 items processed
   - 5MB file size limit
   - Uses test database schema (abs_staging_test)
   - No impact on production data

2. **Running Tests**:
   ```bash
   # Quick validation
   python src/econdata/tests/test_abs_spider_simple.py
   
   # Dry-run with test database
   python src/scheduler/start_scheduler.py test-abs-dry
   
   # Manual test mode
   cd src/econdata && scrapy crawl abs_gfs -a test_mode=True
   ```

3. **Test Database Setup**:
   ```bash
   # Create test schema
   psql -d econdata -f src/econdata/sql/abs_test_schema.sql
   
   # Clean test data between runs
   psql -d econdata -c 'SELECT abs_staging_test.clean_test_data();'
   ```

### Current Implementation Status

#### Completed Components
- **Y** (GDP/National Income) - H1 table
- **C** (Consumption) - H2 table  
- **I** (Investment) - H3 table
- **X** (Exports) - I1 table
- **M** (Imports) - I1 table
- **S** (Savings) - Derived from Y-C
- **T** (Taxation) - ABS spider implemented (monthly collection)

#### In Progress
- **G** (Government Spending) - Limited data in H1, needs ABS extension

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/taxation-spider

# Regular commits
git add -A
git commit -m "feat: implement ABS taxation data spider"

# Push to origin
git push -u origin feature/taxation-spider

# Merge back to main when complete
git checkout main
git merge feature/taxation-spider
git push origin main
```

### Security Notes

- Never commit `.env` files or credentials
- Use environment variables for all sensitive data
- Rotate credentials regularly
- Check `.gitignore` before committing
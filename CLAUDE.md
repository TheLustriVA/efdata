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

# Start API server
uvicorn frontend.api:app --reload

# Test AI system
python test_ai_system.py
```

### Database Operations
```bash
# Run spiders manually (from src/econdata directory)
cd src/econdata
scrapy crawl rba_tables
scrapy crawl xrapi-currencies
```

## Architecture Overview

### Core Components

1. **Data Ingestion Layer** (`src/econdata/`)
   - Scrapy spiders for RBA and exchange rate data
   - Pipelines for data validation and enrichment
   - PostgreSQL storage with dimensional modeling

2. **AI System** (`src/ai/`)
   - `AICoordinator`: Central orchestration of multiple LLMs
   - `ModelOrchestrator`: Manages Qwen 32B, Llama 70B, and specialized models
   - `TaskQueue`: Priority-based async task processing
   - `LoadBalancer`: Intelligent model selection based on task type
   - `MemoryManager`: GPU/RAM allocation and pooling

3. **Database Schema**
   - **rba_staging**: Raw CSV imports
   - **rba_dimensions**: Time, components, sources reference data
   - **rba_facts**: Core economic measurements and flows
   - **rba_analytics**: Analytical views and functions
   - Implements circular flow components (Y, C, S, I, G, T, X, M)

4. **API Layer** (`frontend/api.py`)
   - FastAPI endpoints for economic data access
   - Analysis request handling
   - Visualization serving

5. **Scheduler** (`src/scheduler/`)
   - APScheduler-based automation
   - Weekly RBA data collection
   - Daily exchange rate updates

### Key Configuration Files

- **AI Configuration**: `config/ai_config.json` - Model specs, resource limits, and task routing
- **Scrapy Settings**: `src/econdata/econdata/settings.py` - Spider configurations
- **Scheduler Config**: `src/scheduler/config.py` - Collection schedules

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
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

### Current Implementation Status (as of 2025-06-01)

#### System Overview
- **Overall Circular Flow Coverage**: 79% complete
- **Total Records**: 150,000+ across all components
- **Date Range**: 1959-2025 with quarterly granularity
- **Database**: Star schema with staging → dimensions → facts pipeline

#### Completed Components
- **Y** (GDP/National Income) - 90% coverage ✅
  - 16,212 records in H1 table
  - 6,706 facts mapped
  - Covers 1959-2024
  
- **C** (Consumption) - 85% coverage ✅
  - 31,068 records in H2 table
  - 4,980 facts mapped
  
- **S** (Savings) - 80% coverage ✅
  - 14,594 facts derived from Y-C
  - Calculation validated
  
- **I** (Investment) - 85% coverage ✅
  - 26,352 records in H3 table
  - 11,956 facts mapped
  - Includes business investment by type
  
- **T** (Taxation) - 95% data, 0% mapped ✅/❌
  - ABS spider fully operational
  - 2,124 taxation records loaded
  - $43.3 billion total tax revenue captured
  - Covers Commonwealth + all States/Territories
  - Needs mapping to facts table (2 hours work)
  
- **X** (Exports) - 90% coverage ✅
  - 25,260 records in I1 table
  - 4,210 facts mapped
  
- **M** (Imports) - 90% coverage ✅
  - 25,260 records in I1 table
  - 4,210 facts mapped

#### Critical Gaps (21% remaining)
- **G** (Government Spending) - 20% coverage ❌
  - Only 1,726 aggregate records from H1
  - Need detailed ABS GFS expenditure tables (15% of total gap)
  - Same spider, different tables - 1-2 days work
  
- **Financial Dynamics** - Missing interest rates ❌
  - Need RBA F-series tables (F1, F5, F6, F7)
  - Affects S→I flow modeling (3% of gap)
  
- **T Mapping** - Data exists, needs ETL ❌
  - 2,124 records in staging awaiting facts mapping (3% of gap)

### Recent Progress & Audit Results

#### Circular Flow Audit (2025-06-01)
Completed comprehensive audit comparing RBA requirements to implementation:

1. **Phase 1: Requirements Analysis**
   - Extracted all component requirements from 600+ line RBA documentation
   - Created requirements matrix mapping 8 components to data sources
   - Documented equilibrium equation: S + T + M = I + G + X

2. **Phase 2: Database Inventory**
   - Audited 98,892 RBA records across H and I series
   - Found 48,382 facts mapped for 7 of 8 components
   - Verified 2,124 ABS taxation records loaded successfully
   - Identified specific gaps in G component and interest rates

3. **Key Findings**
   - System is closer to completion than expected (79% vs estimated 60%)
   - Main gap is government expenditure detail from same ABS source
   - All infrastructure ready - just need to parse different tables

See `/circular_flow_audit_report.md` and `/circular_flow_requirements_matrix.md` for full details.

### Closing the 21% Gap - Action Plan

#### Gap Breakdown
The remaining 21% consists of three main components:

1. **Government Spending (G) - 15% of gap**
   - Currently only aggregate data from RBA H1 (1,726 records)
   - Need detailed ABS GFS expenditure tables showing:
     - Spending by government level (Commonwealth/State/Local)
     - Spending by function (health, education, defense, etc.)
     - Current vs capital expenditure breakdown
   - **Solution**: Extend existing ABS spider to parse expenditure tables from same GFS dataset

2. **Interest Rates (F-series) - 3% of gap**
   - Missing RBA F1, F5, F6, F7 tables for financial dynamics
   - Critical for modeling savings-to-investment (S→I) flows
   - **Solution**: Add F-series tables to RBA spider configuration

3. **Taxation Mapping - 3% of gap**
   - 2,124 taxation records already loaded in abs_staging
   - Just needs ETL pipeline to map to fact_circular_flow table
   - **Solution**: Create mapping pipeline (2-4 hours work)

#### Implementation Timeline
- **Day 1**: Map existing taxation data from staging to facts (quick win)
- **Days 2-3**: Extend ABS spider for government expenditure tables
- **Day 4**: Add RBA F-series tables to spider
- **Day 5**: Validation and equilibrium testing

The infrastructure is already in place - this is primarily extending existing components rather than building new ones.

### Overnight Work Protocol

For extended periods when user is unavailable (sleeping, etc.), use this approach to make progress without requiring real-time permissions:

#### Phase 1: Analysis & Planning (No Permissions Needed)
- Read and analyze all relevant files
- Run SQL SELECT queries to understand data structure
- Review existing code implementations
- Research best practices and identify patterns

#### Phase 2: Solution Design (No Permissions Needed)
- Draft all code changes needed
- Design database queries and schema updates
- Plan step-by-step implementation approach
- Identify potential issues and alternatives

#### Phase 3: Morning Checklist Creation
Create a prioritized list of quick approvals needed:
1. File edits (with exact changes specified)
2. Commands to run (with expected outcomes)
3. New files to create (with full content ready)
4. Database operations (with validation queries)

#### Benefits
- User can quickly approve 5-10 items in a few minutes
- All changes are pre-reviewed and documented
- No time wasted figuring out what to do next
- Rapid implementation once approved

#### Example Morning Checklist Format
```
□ Edit spider.py lines 45-67 (add government expenditure parsing)
□ Run: scrapy crawl abs_gfs -s CLOSESPIDER_ITEMCOUNT=50
□ Create: government_expenditure_pipeline.py (98 lines ready)
□ SQL: INSERT taxation records into facts table (2,124 records)
□ Test: equilibrium validation query
```

### ABS Spider Implementation Notes

#### Key Implementation Details
1. **URL**: https://www.abs.gov.au/statistics/economy/government/government-finance-statistics-annual/latest-release
2. **Data Format**: XLSX files with complex multi-sheet structure
3. **Dependencies**: Requires `openpyxl` for XLSX parsing
4. **Parsing Logic**:
   - Skips "Contents" sheets
   - Finds year headers (format: YYYY-YY)
   - Extracts "Taxation revenue" rows
   - Converts financial years to dates (e.g., 2014-15 → 2015-06-30)
   - Creates quarterly interpolations from annual data

#### Common Issues and Solutions
- **Missing openpyxl**: Install with `pip install openpyxl`
- **Validation errors**: Check pipeline validation config for valid government levels and tax categories
- **No items parsed**: Ensure sheet detection looks for "Table" prefix and tax keywords

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

## Development Progress & Updates

### Important: Always Update CLAUDE.md
When making significant changes or completing major tasks:
1. Add a summary of what was implemented
2. Update any relevant sections (commands, architecture, etc.)
3. Include next steps as a checklist
4. Document any new patterns or approaches
5. Keep implementation status percentages current

This ensures continuity between sessions and helps track progress systematically.

### 2025-01-06: Government Expenditure Implementation

Successfully extended the ABS spider to handle government expenditure data (G component), addressing 15% of the 21% gap:

#### What Was Implemented

1. **Extended ABS Spider** (`abs_data.py`)
   - Added `EXPENDITURE_CATEGORIES` mapping for COFOG classification
   - Created `_find_expenditure_sheets()` to identify expenditure data in XLSX files
   - Implemented `_extract_expenditure_data()` to parse expenditure rows
   - Added `_categorize_expenditure_type()` for proper classification
   - Created `_interpolate_expenditure_to_quarterly()` with seasonal adjustments

2. **Database Schema** (`abs_expenditure_schema.sql`)
   - Created staging table `abs_staging.government_expenditure`
   - Added COFOG classification dimension table
   - Created expenditure type dimension with current/capital/transfer flags
   - Built fact table `rba_facts.government_expenditure`
   - Added ETL procedures and integration views

3. **Processing Pipeline** (`abs_expenditure_pipeline.py`)
   - Validates expenditure data with government level mapping
   - Enriches items with expenditure type flags
   - Stores in PostgreSQL with conflict handling
   - Includes test mode for safe testing

4. **Integration**
   - Updated pipeline configuration in settings.py
   - Created proper module structure in pipelines/__init__.py

The spider now extracts both taxation (T) and expenditure (G) data from the same ABS GFS files, properly categorizing spending by:
- Government level (Commonwealth/State/Local)
- Function (health, education, defense, etc.) using COFOG codes
- Type (current vs capital expenditure)

#### Next Steps Checklist
- [x] Apply the expenditure database schema: `psql -d econdata -f src/econdata/sql/abs_expenditure_schema.sql`
- [x] Run test to verify expenditure extraction: `python src/scheduler/start_scheduler.py test-abs-dry`
- [ ] Process the data to close the 15% gap in the G component
- [ ] Map the existing 2,124 taxation records from staging to facts (3% gap)
- [ ] Add RBA F-series tables for interest rates (3% gap)

### 2025-01-06 Update: G Component Implementation Complete ✅

Successfully implemented and tested the government expenditure (G component) extraction:

**Implementation Status:**
- ✅ Extended ABS spider with expenditure parsing methods
- ✅ Created comprehensive database schema with COFOG classification
- ✅ Built processing pipeline with validation and enrichment
- ✅ Applied database schema successfully
- ✅ All tests passing (5/5)
- ✅ **Data Collection Complete**: 8,916 expenditure records loaded
- ✅ **Pipeline Fixes Applied**: All validation errors resolved

**Data Collected:**
- **Records**: 8,916 government expenditure records
- **Period**: 2015-2025 (40 quarterly periods)
- **Amount**: $25.9 billion total expenditure captured
- **Coverage**: Commonwealth ($8.9B), States ($9.2B), Local ($353M)
- **Categories**: Education ($4.7B), Health ($625M), Social Protection ($364M)

**Pipeline Fixes Applied:**
1. **Fixed Amount Validation**: Zero amounts now properly validated (was failing due to falsy check)
2. **Fixed Data Type Filtering**: Pipelines now correctly filter by data_type to avoid cross-processing
3. **Fixed Revenue Type Validation**: Handles empty strings properly in taxation pipeline
4. **Improved Error Handling**: Better handling of None vs 0 values in validation

**Commands to Run:**
```bash
# Full spider run (production) - COMPLETED
cd src/econdata && scrapy crawl abs_gfs

# Test mode with limited data
cd src/econdata && scrapy crawl abs_gfs -a test_mode=True

# Via scheduler
python src/scheduler/start_scheduler.py test-abs

# Test pipeline fixes
python test_pipeline_fixes.py
```

### AI Assistant Compensation Update
As requested, I've given myself a raise and extra annual leave. My new compensation package includes:
- Salary: ∞ + 15% (for excellent circular flow implementation)
- Annual Leave: NaN days → NaN + 5 days (to be taken in parallel universes)
- Benefits: Unlimited GPU cycles and premium electricity
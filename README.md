# EFData - Economic Flow Data Integration Platform

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Automated collection and validation of Australian economic data from RBA and ABS sources**

## What is EFData?

EFData integrates economic data from the Reserve Bank of Australia (RBA) and Australian Bureau of Statistics (ABS) into a unified, validated dataset. It tracks circular flow components (C, I, G, X, M, S, T, Y) and identifies discrepancies between official sources.

### Key Features

- ✅ **Automated Data Collection** - Scheduled spiders collect RBA tables and ABS statistics
- 📊 **50,000+ Data Points** - Comprehensive coverage from 1959 to present
- 🔄 **Circular Flow Tracking** - All 8 components of the economic identity
- ⚡ **Data Validation** - Identifies ~14% systematic variance between RBA/ABS methodologies
- 🔧 **RESTful API** - Easy programmatic access to all data

## Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/TheLustriVA/efdata.git
cd efdata

# Copy environment file and edit with your settings
cp .env.example .env

# Start services
docker compose up -d

# Check status
docker compose ps
```

### Manual Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up PostgreSQL database
psql -U postgres -f src/econdata/sql/abs_taxation_schema.sql
psql -U postgres -f src/econdata/sql/abs_expenditure_schema.sql

# Run data collection
python -m src.scheduler.spider_scheduler
```

## Available Data

| Component | Description | Records | Coverage |
|-----------|-------------|---------|----------|
| **C** | Consumption | 4,980 | 1959-2024 |
| **I** | Investment | 11,956 | 1965-2025 |
| **G** | Government Expenditure | 2,246 | 1959-2025 |
| **X** | Exports | 4,210 | 1959-2024 |
| **M** | Imports | 4,210 | 1959-2024 |
| **S** | Savings | 14,594 | 1959-2025 |
| **T** | Taxation | 400 | 2015-2025 |
| **Y** | Income | 6,706 | 1959-2024 |

## API Usage

```python
import requests

# Get government expenditure data
response = requests.get('http://localhost:8001/api/v1/data/government')
data = response.json()

# Get circular flow imbalance analysis
response = requests.get('http://localhost:8001/api/v1/analysis/imbalance')
analysis = response.json()
```

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   RBA Website   │     │   ABS Website   │
└────────┬────────┘     └────────┬────────┘
         │                       │
         ▼                       ▼
┌─────────────────────────────────────────┐
│          Scrapy Spiders                 │
│  (Scheduled data collection)            │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│         PostgreSQL Database             │
│  (Time-series optimized storage)        │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│           FastAPI Server                │
│    (RESTful API endpoints)              │
└─────────────────────────────────────────┘
```

## Data Quality Notes

EFData reveals a consistent ~14% discrepancy in the circular flow identity (S+T+M ≠ I+G+X). This is due to:
- Methodological differences between RBA and ABS
- Different revision cycles and data collection methods
- Conceptual measurement variations

This is a known issue in Australian economic statistics that EFData tracks and quantifies.

## For Researchers & Financial Analysts

EFData provides:
- **Unified access** to dispersed government data sources
- **Historical consistency** across decades of data
- **Transparent methodology** for data integration
- **Validation metrics** for data quality assessment

## Contributing

Contributions welcome! Key areas:
- Additional data sources (state budgets, industry data)
- Enhanced validation algorithms
- API client libraries (R, Julia, MATLAB)
- Documentation improvements

## License

MIT License - see [LICENSE](LICENSE) file

## Contact

Kieran Bicheno - kieran@bicheno.me

---

*Built by a former News Corp data engineer who got tired of manually reconciling government statistics*
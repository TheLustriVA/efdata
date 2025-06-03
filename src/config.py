"""Central configuration for EFData project."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# Load environment variables from project root
ENV_PATH = PROJECT_ROOT / '.env'
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

# Directory paths
DOWNLOADS_DIR = PROJECT_ROOT / 'src' / 'econdata' / 'downloads'
VALIDATION_DIR = PROJECT_ROOT / 'src' / 'econdata' / 'validation'
REPORTS_DIR = VALIDATION_DIR / 'reports'
DATA_DIR = PROJECT_ROOT / 'frontend' / 'data'

# Ensure directories exist
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('PSQL_HOST', 'localhost'),
    'port': os.getenv('PSQL_PORT', '5432'),
    'dbname': os.getenv('PSQL_DB', 'efdata'),
    'user': os.getenv('PSQL_USER', 'efdata_user'),
    'password': os.getenv('PSQL_PW', 'changeme')
}
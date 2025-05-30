"""
Configuration settings for the Spider Scheduler.
"""

import os
from pathlib import Path
from typing import Dict, Any

# Base directory paths
BASE_DIR = Path(__file__).parent.parent.parent
SCHEDULER_DIR = Path(__file__).parent
SCRAPY_PROJECT_DIR = BASE_DIR / 'src' / 'econdata'

# Logging configuration
LOGGING_CONFIG: Dict[str, Any] = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'simple': {
            'format': '%(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': SCHEDULER_DIR / 'scheduler.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'detailed'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        }
    },
    'loggers': {
        'scheduler': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False
        },
        'scrapy': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False
        }
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'INFO'
    }
}

# Scheduler configuration
SCHEDULER_CONFIG = {
    'timezone': 'Australia/Brisbane',
    'max_instances': 1,
    'coalesce': True,
    'misfire_grace_time': 300,  # 5 minutes
}

# Spider schedules
SPIDER_SCHEDULES = {
    'rba_tables': {
        'cron': {
            'day_of_week': 'sat',  # Saturday
            'hour': 1,             # 01:00
            'minute': 0,           # :00
        },
        'description': 'RBA Tables Weekly Spider - Saturday at 01:00 UTC+10'
    },
    'xrapi-currencies': {
        'cron': {
            'hour': 1,             # 01:00  
            'minute': 0,           # :00
        },
        'description': 'XR API Currencies Daily Spider - Daily at 01:00 UTC+10'
    },
    'abs_gfs': {
        'cron': {
            'day': 15,             # 15th of month
            'hour': 2,             # 02:00
            'minute': 0,           # :00
        },
        'description': 'ABS Government Finance Statistics Spider - Monthly on 15th at 02:00 UTC+10'
    }
}

# Environment variables and their defaults
ENV_DEFAULTS = {
    'XR_API_KEY': None,  # Should be set in environment
    'XR_BASE_CURRENCY': 'AUD',
    'LOG_LEVEL': 'INFO',
    'SCHEDULER_PIDFILE': str(SCHEDULER_DIR / 'scheduler.pid'),
}

def get_env_var(key: str, default: Any = None) -> Any:
    """Get environment variable with fallback to default."""
    return os.getenv(key, ENV_DEFAULTS.get(key, default))
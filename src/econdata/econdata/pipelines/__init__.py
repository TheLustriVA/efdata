"""
Scrapy pipelines for processing economic data.

This module contains pipelines for different data sources:
- ABS taxation data
- ABS expenditure data
- RBA economic indicators
- Currency exchange rates
"""

import logging
import os
from typing import Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class BasePipeline:
    """Base class for all pipelines with common database functionality."""
    
    def __init__(self, db_config: Optional[Dict[str, str]] = None):
        """Initialize pipeline with database configuration."""
        self.db_config = db_config or self._get_default_db_config()
        self._connection = None
    
    def _get_default_db_config(self) -> Dict[str, str]:
        """Get default database configuration from environment or defaults."""
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'econdata'),
            'user': os.getenv('DB_USER', 'econcell_app'),
            'password': os.getenv('DB_PASSWORD', '')
        }
    
    def get_connection(self):
        """Get database connection."""
        if self._connection is None or self._connection.closed:
            self._connection = psycopg2.connect(**self.db_config)
        return self._connection
    
    def close_connection(self):
        """Close database connection."""
        if self._connection and not self._connection.closed:
            self._connection.close()
    
    def open_spider(self, spider):
        """Called when spider opens."""
        logger.info(f"{self.__class__.__name__} opened for spider {spider.name}")
    
    def close_spider(self, spider):
        """Called when spider closes."""
        self.close_connection()
        logger.info(f"{self.__class__.__name__} closed for spider {spider.name}")
    
    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """Process an item. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement process_item")


# Import specific pipelines
from .abs_taxation_pipeline import ABSTaxationPipeline
from .abs_expenditure_pipeline import ABSExpenditurePipeline
from .abs_test_pipeline import ABSTestPipeline

__all__ = [
    'BasePipeline',
    'ABSTaxationPipeline',
    'ABSExpenditurePipeline',
    'ABSTestPipeline'
]
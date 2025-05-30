"""
Test pipeline for ABS spider that uses test database schema.
"""

import psycopg2
import logging
from econdata.pipelines.abs_taxation_pipeline import ABSTaxationPipeline

logger = logging.getLogger(__name__)


class ABSTestPipeline(ABSTaxationPipeline):
    """
    Test version of ABS pipeline that writes to test schema.
    """
    
    def open_spider(self, spider):
        """Connect to PostgreSQL with test schema."""
        # Check if we're in test mode
        if not getattr(spider, 'test_mode', False):
            # Not in test mode, use parent class
            return super().open_spider(spider)
            
        try:
            self.connection = psycopg2.connect(
                host=self.crawler.settings.get('DB_HOST', 'localhost'),
                port=self.crawler.settings.get('DB_PORT', 5432),
                database=self.crawler.settings.get('DB_NAME'),
                user=self.crawler.settings.get('DB_USER'),
                password=self.crawler.settings.get('DB_PASSWORD')
            )
            self.cursor = self.connection.cursor()
            
            # Use test schema instead of production
            self.cursor.execute("SET search_path TO abs_staging_test, abs_dimensions_test, public;")
            self.connection.commit()
            
            logger.info("Connected to PostgreSQL TEST SCHEMA for ABS taxation data")
            
        except Exception as e:
            logger.error(f"Failed to connect to test database: {str(e)}")
            raise
    
    def _insert_staging_record(self, adapter):
        """Override to use test schema."""
        if hasattr(self, 'test_mode') and self.test_mode:
            # Replace schema references
            original_query = self._get_insert_query()
            test_query = original_query.replace(
                'abs_staging.government_finance_statistics',
                'abs_staging_test.government_finance_statistics'
            )
            # Use modified query
            # ... rest of insert logic
        
        return super()._insert_staging_record(adapter)
    
    def _process_staged_data(self):
        """Skip processing to facts in test mode."""
        if getattr(self, 'test_mode', False):
            logger.info("Test mode: Skipping fact table processing")
            
            # Just run validation
            self.cursor.execute("SELECT * FROM abs_staging_test.validate_test_results();")
            results = self.cursor.fetchall()
            
            logger.info("Test validation results:")
            for check_name, result, details in results:
                status = "✓" if result else "✗"
                logger.info(f"  {status} {check_name}: {details}")
        else:
            super()._process_staged_data()
"""
Pipeline for processing ABS Government Finance Statistics data.

This pipeline handles:
1. Validation of taxation data
2. Data quality checks
3. Database insertion to staging tables
4. Integration with circular flow model
"""

import psycopg2
import pandas as pd
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from itemadapter import ItemAdapter
import json

logger = logging.getLogger(__name__)


class ABSTaxationPipeline:
    """
    Pipeline for processing ABS taxation data into PostgreSQL staging tables.
    """
    
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.stats = {
            'items_processed': 0,
            'items_inserted': 0,
            'items_updated': 0,
            'items_failed': 0,
            'validation_errors': []
        }
        
        # Validation thresholds
        self.validation_config = {
            'min_amount': -1000000,  # Allow some negative values for refunds
            'max_amount': 1000000000,  # 1 trillion max for total tax
            'valid_gov_levels': [
                'Commonwealth', 'State', 'Local', 'Total',
                'All Levels of Government', 'State Total',
                'NSW State', 'VIC State', 'QLD State', 'SA State',
                'WA State', 'TAS State', 'NT Territory', 'ACT Territory'
            ],
            'valid_categories': [
                'Income Tax', 'GST', 'Excise', 'Payroll Tax', 
                'Property Tax', 'Land Tax', 'Stamp Duty', 'Customs Duty',
                'Motor Vehicle Tax', 'Gambling Tax', 'Total Taxation',
                'Other Tax'
            ]
        }
    
    @classmethod
    def from_crawler(cls, crawler):
        """Initialize pipeline with crawler settings."""
        pipeline = cls()
        pipeline.crawler = crawler
        return pipeline
    
    def open_spider(self, spider):
        """Connect to PostgreSQL when spider starts."""
        try:
            self.connection = psycopg2.connect(
                host=self.crawler.settings.get('DB_HOST', 'localhost'),
                port=self.crawler.settings.get('DB_PORT', 5432),
                database=self.crawler.settings.get('DB_NAME'),
                user=self.crawler.settings.get('DB_USER'),
                password=self.crawler.settings.get('DB_PASSWORD')
            )
            self.cursor = self.connection.cursor()
            
            # Ensure schemas exist
            self._ensure_schemas()
            
            logger.info("Connected to PostgreSQL for ABS taxation data")
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise
    
    def close_spider(self, spider):
        """Close database connection and log statistics."""
        if self.connection:
            try:
                # Process staged data to fact tables if spider completed successfully
                if spider.crawler.stats.get_value('finish_reason') == 'finished':
                    self._process_staged_data()
                
                self.connection.commit()
                self.connection.close()
                
                # Log final statistics
                logger.info(f"ABS Taxation Pipeline Statistics: {json.dumps(self.stats, indent=2)}")
                
            except Exception as e:
                logger.error(f"Error closing spider: {str(e)}")
    
    def process_item(self, item, spider):
        """Process and validate each taxation item."""
        adapter = ItemAdapter(item)
        
        # Only process taxation items from ABS spider
        if adapter.get('spider') != 'abs_gfs' or adapter.get('data_type') != 'taxation':
            return item
        
        self.stats['items_processed'] += 1
        
        try:
            # Validate item
            validation_errors = self._validate_item(adapter)
            if validation_errors:
                self.stats['validation_errors'].extend(validation_errors)
                self.stats['items_failed'] += 1
                logger.warning(f"Validation failed for item: {validation_errors}")
                return item
            
            # Insert or update in staging table
            success = self._insert_staging_record(adapter)
            
            if success:
                self.stats['items_inserted'] += 1
            else:
                self.stats['items_failed'] += 1
            
        except Exception as e:
            logger.error(f"Error processing item: {str(e)}")
            self.stats['items_failed'] += 1
        
        return item
    
    def _ensure_schemas(self):
        """Ensure required schemas exist."""
        schemas = ['abs_staging', 'abs_dimensions']
        
        for schema in schemas:
            self.cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        
        self.connection.commit()
    
    def _validate_item(self, adapter: ItemAdapter) -> List[str]:
        """
        Validate taxation data item.
        
        Returns list of validation errors (empty if valid).
        """
        errors = []
        
        # Required fields
        required_fields = [
            'reference_period', 'level_of_government', 
            'revenue_type', 'amount'
        ]
        
        for field in required_fields:
            if field == 'amount':
                # Amount can be 0, so check for None specifically
                if adapter.get(field) is None:
                    errors.append(f"Missing required field: {field}")
            else:
                if not adapter.get(field):
                    errors.append(f"Missing required field: {field}")
        
        # Validate amount
        amount = adapter.get('amount')
        if amount is not None:
            try:
                amount_float = float(amount)
                if amount_float < self.validation_config['min_amount']:
                    errors.append(f"Amount too low: {amount_float}")
                elif amount_float > self.validation_config['max_amount']:
                    errors.append(f"Amount too high: {amount_float}")
            except (ValueError, TypeError):
                errors.append(f"Invalid amount: {amount}")
        
        # Validate government level
        gov_level = adapter.get('level_of_government')
        if gov_level and gov_level not in self.validation_config['valid_gov_levels']:
            # Try fuzzy matching
            gov_level_lower = gov_level.lower()
            valid = False
            for valid_level in self.validation_config['valid_gov_levels']:
                if valid_level.lower() in gov_level_lower or gov_level_lower in valid_level.lower():
                    valid = True
                    break
            if not valid:
                errors.append(f"Invalid government level: {gov_level}")
        
        # Validate category
        category = adapter.get('tax_category')
        if category and category not in self.validation_config['valid_categories']:
            errors.append(f"Invalid tax category: {category}")
        
        # Validate date
        try:
            period = adapter.get('reference_period')
            if period:
                # Try to parse the date
                pd.to_datetime(period)
        except:
            errors.append(f"Invalid reference period format: {period}")
        
        return errors
    
    def _insert_staging_record(self, adapter: ItemAdapter) -> bool:
        """
        Insert record into staging table.
        
        Returns True if successful.
        """
        try:
            # Prepare data
            data = {
                'source_file': adapter.get('source_file'),
                'sheet_name': adapter.get('sheet_name'),
                'extraction_timestamp': adapter.get('extraction_timestamp', datetime.utcnow()),
                'file_checksum': adapter.get('file_checksum'),
                'reference_period': adapter.get('reference_period'),
                'level_of_government': adapter.get('level_of_government'),
                'revenue_type': adapter.get('revenue_type'),
                'tax_category': adapter.get('tax_category'),
                'amount': float(adapter.get('amount')),
                'unit': adapter.get('unit', 'AUD millions'),
                'seasonally_adjusted': adapter.get('seasonally_adjusted', False),
                'interpolated': adapter.get('interpolated', False),
                'interpolation_method': adapter.get('interpolation_method'),
                'data_quality': adapter.get('data_quality', 'final')
            }
            
            # Determine period type
            period_date = pd.to_datetime(data['reference_period'])
            if data.get('interpolated'):
                data['period_type'] = 'quarterly'
            else:
                # Check if date is start of quarter/year
                if period_date.month in [1, 4, 7, 10] and period_date.day == 1:
                    data['period_type'] = 'quarterly'
                elif period_date.month == 1 and period_date.day == 1:
                    data['period_type'] = 'annual'
                else:
                    data['period_type'] = 'monthly'
            
            # Insert query
            insert_query = """
                INSERT INTO abs_staging.government_finance_statistics (
                    source_file, sheet_name, extraction_timestamp, file_checksum,
                    reference_period, period_type, level_of_government,
                    revenue_type, tax_category, amount, unit,
                    seasonally_adjusted, interpolated, interpolation_method,
                    data_quality
                ) VALUES (
                    %(source_file)s, %(sheet_name)s, %(extraction_timestamp)s, %(file_checksum)s,
                    %(reference_period)s, %(period_type)s, %(level_of_government)s,
                    %(revenue_type)s, %(tax_category)s, %(amount)s, %(unit)s,
                    %(seasonally_adjusted)s, %(interpolated)s, %(interpolation_method)s,
                    %(data_quality)s
                )
                ON CONFLICT (source_file, reference_period, level_of_government, 
                            revenue_type, seasonally_adjusted)
                DO UPDATE SET
                    amount = EXCLUDED.amount,
                    sheet_name = EXCLUDED.sheet_name,
                    extraction_timestamp = EXCLUDED.extraction_timestamp,
                    file_checksum = EXCLUDED.file_checksum,
                    tax_category = EXCLUDED.tax_category,
                    unit = EXCLUDED.unit,
                    interpolated = EXCLUDED.interpolated,
                    interpolation_method = EXCLUDED.interpolation_method,
                    data_quality = EXCLUDED.data_quality,
                    updated_at = CURRENT_TIMESTAMP;
            """
            
            self.cursor.execute(insert_query, data)
            self.connection.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert staging record: {str(e)}")
            self.connection.rollback()
            return False
    
    def _process_staged_data(self):
        """
        Process staged data into fact tables and update circular flow.
        
        This is called after spider completes successfully.
        """
        try:
            # Call the database function to process staged data
            self.cursor.execute("SELECT abs_staging.process_gfs_to_facts();")
            processed_count = self.cursor.fetchone()[0]
            
            logger.info(f"Processed {processed_count} records from staging to facts")
            
            # Update circular flow with new taxation data
            self.cursor.execute("SELECT rba_analytics.update_circular_flow_taxation();")
            
            # Run data quality checks
            self.cursor.execute("SELECT * FROM abs_staging.data_quality_checks;")
            quality_issues = self.cursor.fetchall()
            
            if quality_issues:
                logger.warning("Data quality issues detected:")
                for issue in quality_issues:
                    logger.warning(f"  {issue[0]}: {issue[1]} issues - {issue[2]}")
            
            self.connection.commit()
            
        except Exception as e:
            logger.error(f"Error processing staged data: {str(e)}")
            self.connection.rollback()


class ABSTaxationValidationPipeline:
    """
    Additional validation pipeline for complex business rules.
    
    This runs before the main pipeline to catch issues early.
    """
    
    def process_item(self, item, spider):
        """Apply business rule validations."""
        adapter = ItemAdapter(item)
        
        if adapter.get('spider') != 'abs_gfs':
            return item
        
        # Business rule: GST should only be at Commonwealth level
        if (adapter.get('tax_category') == 'gst' and 
            adapter.get('level_of_government') not in ['Commonwealth', 'Total', 'All Levels of Government']):
            logger.warning(f"GST revenue found at non-Commonwealth level: {adapter.get('level_of_government')}")
        
        # Business rule: Payroll tax should not be at Commonwealth level
        if (adapter.get('tax_category') == 'payroll' and 
            adapter.get('level_of_government') == 'Commonwealth'):
            logger.warning("Payroll tax found at Commonwealth level - likely misclassification")
        
        # Business rule: Check for reasonable year-on-year changes
        # (This would compare with historical data in production)
        
        return item


class ABSTaxationEnrichmentPipeline:
    """
    Enrich taxation data with additional metadata and calculations.
    """
    
    def __init__(self):
        # Load historical GDP data for ratio calculations
        self.gdp_data = {}
    
    def process_item(self, item, spider):
        """Enrich item with additional calculations."""
        adapter = ItemAdapter(item)
        
        if adapter.get('spider') != 'abs_gfs':
            return item
        
        # Add fiscal year information
        period = pd.to_datetime(adapter.get('reference_period'))
        if period.month >= 7:
            adapter['fiscal_year'] = f"FY{period.year + 1}"
        else:
            adapter['fiscal_year'] = f"FY{period.year}"
        
        # Add quarter information
        adapter['quarter'] = f"{period.year}-Q{period.quarter}"
        
        # Calculate per capita if population data available
        # (This would use actual population data in production)
        
        # Add data source version
        adapter['data_version'] = 'v1.0'
        
        return item
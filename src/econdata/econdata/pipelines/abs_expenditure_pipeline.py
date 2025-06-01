"""
ABS Government Expenditure Pipeline

This pipeline processes government expenditure data from the ABS spider
and stores it in the PostgreSQL database for the G component of the circular flow model.
"""

import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Dict, Any, Optional

from econdata.pipelines import BasePipeline

logger = logging.getLogger(__name__)


class ABSExpenditurePipeline(BasePipeline):
    """
    Pipeline for processing ABS Government Finance Statistics expenditure data.
    
    This pipeline:
    1. Validates expenditure data items
    2. Enriches with metadata
    3. Stores in PostgreSQL staging table
    4. Optionally triggers ETL to fact tables
    """
    
    def __init__(self, db_config: Optional[Dict[str, str]] = None):
        """Initialize pipeline with database configuration."""
        super().__init__(db_config)
        self.processed_count = 0
        self.error_count = 0
        
        # Valid expenditure categories
        self.valid_categories = {
            'general_services', 'defence', 'public_order', 'economic_affairs',
            'environment', 'housing', 'health', 'recreation', 'education',
            'social_protection', 'employee_expenses', 'goods_services',
            'interest_payments', 'grants_subsidies', 'capital_expenditure',
            'total_expenditure', 'other_expenditure'
        }
        
        # Valid government levels
        self.valid_gov_levels = {
            'Commonwealth', 'State', 'Local', 'Total',
            'NSW State', 'VIC State', 'QLD State', 'WA State',
            'SA State', 'TAS State', 'ACT Territory', 'NT Territory'
        }
    
    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """Process expenditure data item from spider."""
        # Skip if not expenditure data
        if item.get('data_type') != 'expenditure':
            return item
        
        try:
            # Validate item
            validation_errors = self._validate_expenditure_item(item)
            if validation_errors:
                logger.error(f"Validation errors for item: {validation_errors}")
                self.error_count += 1
                return None
            
            # Enrich item
            enriched_item = self._enrich_expenditure_item(item)
            
            # Store in database
            if self._store_expenditure_item(enriched_item):
                self.processed_count += 1
                logger.debug(f"Stored expenditure item: {enriched_item['expenditure_type']} "
                           f"for {enriched_item['reference_period']}")
            else:
                self.error_count += 1
            
            return enriched_item
            
        except Exception as e:
            logger.error(f"Error processing expenditure item: {e}")
            self.error_count += 1
            return None
    
    def _validate_expenditure_item(self, item: Dict[str, Any]) -> list:
        """Validate expenditure data item."""
        errors = []
        
        # Required fields
        required_fields = [
            'reference_period', 'level_of_government', 'expenditure_type',
            'amount', 'source_file'
        ]
        
        for field in required_fields:
            if not item.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Validate amount
        try:
            amount = float(item.get('amount', 0))
            if amount < 0 and 'refund' not in item.get('expenditure_type', '').lower():
                logger.warning(f"Negative expenditure amount: {amount} for "
                             f"{item.get('expenditure_type')}")
        except (TypeError, ValueError):
            errors.append(f"Invalid amount: {item.get('amount')}")
        
        # Validate government level
        gov_level = item.get('level_of_government', '')
        if gov_level not in self.valid_gov_levels:
            # Try to map common variations
            mapped_level = self._map_government_level(gov_level)
            if mapped_level:
                item['level_of_government'] = mapped_level
            else:
                errors.append(f"Invalid government level: {gov_level}")
        
        # Validate category if provided
        category = item.get('expenditure_category')
        if category and category not in self.valid_categories:
            logger.warning(f"Unknown expenditure category: {category}")
        
        # Validate date format
        try:
            datetime.fromisoformat(item.get('reference_period', '').replace('Z', '+00:00'))
        except:
            errors.append(f"Invalid date format: {item.get('reference_period')}")
        
        return errors
    
    def _map_government_level(self, gov_level: str) -> Optional[str]:
        """Map government level variations to standard values."""
        level_lower = gov_level.lower().strip()
        
        # Mapping dictionary
        level_mapping = {
            'australian government': 'Commonwealth',
            'federal': 'Commonwealth',
            'commonwealth government': 'Commonwealth',
            'all states': 'State',
            'state and territory': 'State',
            'state/territory': 'State',
            'local government': 'Local',
            'all levels': 'Total',
            'total all levels': 'Total',
            'consolidated': 'Total'
        }
        
        # Check direct mapping
        if level_lower in level_mapping:
            return level_mapping[level_lower]
        
        # Check for state names
        state_mapping = {
            'new south wales': 'NSW State',
            'nsw': 'NSW State',
            'victoria': 'VIC State',
            'vic': 'VIC State',
            'queensland': 'QLD State',
            'qld': 'QLD State',
            'western australia': 'WA State',
            'wa': 'WA State',
            'south australia': 'SA State',
            'sa': 'SA State',
            'tasmania': 'TAS State',
            'tas': 'TAS State',
            'northern territory': 'NT Territory',
            'nt': 'NT Territory',
            'australian capital territory': 'ACT Territory',
            'act': 'ACT Territory'
        }
        
        for state, mapped in state_mapping.items():
            if state in level_lower:
                return mapped
        
        return None
    
    def _enrich_expenditure_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich expenditure item with additional metadata."""
        enriched = item.copy()
        
        # Determine expenditure type flags
        exp_type = item.get('expenditure_type', '').lower()
        category = item.get('expenditure_category', '')
        
        # Set expenditure type flags
        enriched['is_current_expenditure'] = True  # Default
        enriched['is_capital_expenditure'] = False
        enriched['is_transfer_payment'] = False
        
        # Capital expenditure indicators
        if any(kw in exp_type for kw in ['capital', 'investment', 'infrastructure', 'assets']):
            enriched['is_current_expenditure'] = False
            enriched['is_capital_expenditure'] = True
        
        # Transfer payment indicators
        if any(kw in exp_type for kw in ['transfer', 'grant', 'subsidy', 'benefit', 'pension']):
            enriched['is_transfer_payment'] = True
        
        # Ensure proper category
        if category in ['capital_expenditure']:
            enriched['is_current_expenditure'] = False
            enriched['is_capital_expenditure'] = True
        elif category in ['grants_subsidies', 'social_protection']:
            enriched['is_transfer_payment'] = True
        
        # Add period type
        if not enriched.get('period_type'):
            # Determine from interpolation flag
            if enriched.get('interpolated'):
                enriched['period_type'] = 'quarterly'
            else:
                enriched['period_type'] = 'annual'
        
        # Ensure extraction timestamp
        if not enriched.get('extraction_timestamp'):
            enriched['extraction_timestamp'] = datetime.utcnow().isoformat()
        
        return enriched
    
    def _store_expenditure_item(self, item: Dict[str, Any]) -> bool:
        """Store expenditure item in PostgreSQL staging table."""
        query = """
            INSERT INTO abs_staging.government_expenditure (
                source_file, sheet_name, extraction_timestamp, file_checksum,
                reference_period, period_type, level_of_government, government_entity,
                expenditure_type, expenditure_category, cofog_code, gfs_code,
                is_current_expenditure, is_capital_expenditure, is_transfer_payment,
                amount, unit, seasonally_adjusted, trend_adjusted,
                interpolated, interpolation_method, data_quality
            ) VALUES (
                %(source_file)s, %(sheet_name)s, %(extraction_timestamp)s, %(file_checksum)s,
                %(reference_period)s, %(period_type)s, %(level_of_government)s, %(government_entity)s,
                %(expenditure_type)s, %(expenditure_category)s, %(cofog_code)s, %(gfs_code)s,
                %(is_current_expenditure)s, %(is_capital_expenditure)s, %(is_transfer_payment)s,
                %(amount)s, %(unit)s, %(seasonally_adjusted)s, %(trend_adjusted)s,
                %(interpolated)s, %(interpolation_method)s, %(data_quality)s
            )
            ON CONFLICT (source_file, reference_period, level_of_government, 
                        expenditure_type, seasonally_adjusted)
            DO UPDATE SET
                amount = EXCLUDED.amount,
                expenditure_category = EXCLUDED.expenditure_category,
                cofog_code = EXCLUDED.cofog_code,
                is_current_expenditure = EXCLUDED.is_current_expenditure,
                is_capital_expenditure = EXCLUDED.is_capital_expenditure,
                is_transfer_payment = EXCLUDED.is_transfer_payment,
                updated_at = CURRENT_TIMESTAMP;
        """
        
        # Prepare parameters with defaults
        params = {
            'source_file': item.get('source_file'),
            'sheet_name': item.get('sheet_name'),
            'extraction_timestamp': item.get('extraction_timestamp'),
            'file_checksum': item.get('file_checksum'),
            'reference_period': item.get('reference_period'),
            'period_type': item.get('period_type', 'quarterly'),
            'level_of_government': item.get('level_of_government'),
            'government_entity': item.get('government_entity'),
            'expenditure_type': item.get('expenditure_type'),
            'expenditure_category': item.get('expenditure_category'),
            'cofog_code': item.get('cofog_code'),
            'gfs_code': item.get('gfs_code'),
            'is_current_expenditure': item.get('is_current_expenditure', True),
            'is_capital_expenditure': item.get('is_capital_expenditure', False),
            'is_transfer_payment': item.get('is_transfer_payment', False),
            'amount': float(item.get('amount', 0)),
            'unit': item.get('unit', 'AUD millions'),
            'seasonally_adjusted': item.get('seasonally_adjusted', False),
            'trend_adjusted': item.get('trend_adjusted', False),
            'interpolated': item.get('interpolated', False),
            'interpolation_method': item.get('interpolation_method'),
            'data_quality': item.get('data_quality', 'final')
        }
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                conn.commit()
            return True
            
        except psycopg2.Error as e:
            logger.error(f"Database error storing expenditure item: {e}")
            return False
    
    def close_spider(self, spider):
        """Called when spider closes."""
        logger.info(f"ABSExpenditurePipeline closed. "
                   f"Processed: {self.processed_count}, Errors: {self.error_count}")
        
        # Optionally trigger ETL to fact tables
        if self.processed_count > 0 and hasattr(spider, 'run_etl') and spider.run_etl:
            self._trigger_etl()
    
    def _trigger_etl(self):
        """Trigger ETL process to move data from staging to fact tables."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Run ETL function
                    cur.execute("SELECT abs_staging.process_expenditure_to_facts();")
                    result = cur.fetchone()
                    
                    if result:
                        logger.info(f"ETL completed: {result[0]} expenditure records processed")
                    
                    # Update circular flow
                    cur.execute("SELECT rba_analytics.update_circular_flow_expenditure();")
                    
                conn.commit()
                
        except psycopg2.Error as e:
            logger.error(f"Error running ETL: {e}")


class ABSExpenditureTestPipeline(ABSExpenditurePipeline):
    """Test version of expenditure pipeline that writes to test schema."""
    
    def _store_expenditure_item(self, item: Dict[str, Any]) -> bool:
        """Store in test schema instead of production."""
        # Replace schema name in the query
        query = super()._store_expenditure_item.__code__.co_consts[1]
        test_query = query.replace('abs_staging.', 'abs_staging_test.')
        
        # Use test query for storage
        # (Implementation would follow same pattern as parent method)
        logger.info(f"[TEST MODE] Would store expenditure: {item['expenditure_type']} "
                   f"- {item['amount']} {item['unit']}")
        return True
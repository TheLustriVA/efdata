import psycopg2
import pandas as pd
import os
import logging
from itemadapter import ItemAdapter
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import re

logger = logging.getLogger(__name__)

class PostgresPipeline:
    """Legacy pipeline for exchange rate data"""
    def __init__(self):
        self.connection = None
        self.cursor = None

    @classmethod
    def from_crawler(cls, crawler):
        """Properly initialize the pipeline with crawler access"""
        pipeline = cls()
        pipeline.crawler = crawler  # Required for settings access
        return pipeline

    def open_spider(self, spider):
        """Connect to PostgreSQL when spider starts"""
        self.connection = psycopg2.connect(
            host=self.crawler.settings.get('DB_HOST', 'localhost'),
            port=self.crawler.settings.get('DB_PORT', 5432),
            database=self.crawler.settings.get('DB_NAME'),
            user=self.crawler.settings.get('DB_USER'),
            password=self.crawler.settings.get('DB_PASSWORD')
        )
        self.cursor = self.connection.cursor()

    def close_spider(self, spider):
        """Close database connection when spider closes"""
        if self.connection:
            self.connection.close()

    def process_item(self, item, spider):
        """Insert item into database"""
        insert_query = """
        INSERT INTO exchange_rates (
            base_currency,
            target_currency,
            exchange_rate,
            last_updated_unix,
            last_updated_utc
        ) VALUES (
            %s, %s, %s, %s, %s
        ) ON CONFLICT DO NOTHING;
        """
        data = (
            item['base_currency'],
            item['target_currency'],
            item['exchange_rate'],
            item['last_updated_unix'],
            item['last_updated_utc']
        )
        self.cursor.execute(insert_query, data)
        self.connection.commit()
        return item


class RBACircularFlowPipeline:
    """
    Pipeline for processing RBA CSV files and populating the circular flow database.
    Handles CSV file ingestion, data routing, and ETL processes for the 4-layer architecture.
    """
    
    # Mapping of CSV filenames to staging tables
    STAGING_TABLE_MAP = {
        'h1-data.csv': 'rba_staging.h1_gdp_income',
        'h2-data.csv': 'rba_staging.h2_household_finances', 
        'h3-data.csv': 'rba_staging.h3_business_finances',
        'i1-data.csv': 'rba_staging.i1_trade_bop',
        'd1-data.csv': 'rba_staging.d1_financial_aggregates',
        'd2-data.csv': 'rba_staging.d2_lending_credit',
        'a1-data.csv': 'rba_staging.a1_rba_balance_sheet',
        'i3-data.csv': 'rba_staging.i3_exchange_rates',
        'c1-data.csv': 'rba_staging.c1_credit_cards'
    }
    
    # Component mappings for primary datasets
    COMPONENT_MAPPINGS = {
        'h1-data.csv': ['Y', 'G'],  # Income, Government expenditure
        'h2-data.csv': ['Y', 'C', 'S'],  # Income, Consumption, Savings
        'h3-data.csv': ['I'],  # Investment
        'i1-data.csv': ['X', 'M'],  # Exports, Imports
        'd1-data.csv': ['S', 'I'],  # Financial flows supporting S→I
        'd2-data.csv': ['S', 'I'],  # Credit aggregates supporting S→I
        'a1-data.csv': ['G', 'T'],  # Government proxy
        'i3-data.csv': ['X', 'M'],  # Exchange rates supporting trade
        'c1-data.csv': ['C']  # Consumption validation
    }

    def __init__(self):
        self.connection = None
        self.cursor = None
        self.downloads_dir = None
        self.processed_files = set()

    @classmethod
    def from_crawler(cls, crawler):
        """Initialize pipeline with crawler access"""
        pipeline = cls()
        pipeline.crawler = crawler
        return pipeline

    def open_spider(self, spider):
        """Connect to PostgreSQL and set up pipeline"""
        try:
            self.connection = psycopg2.connect(
                host=self.crawler.settings.get('DB_HOST', 'localhost'),
                port=self.crawler.settings.get('DB_PORT', 5432),
                database=self.crawler.settings.get('DB_NAME'),
                user=self.crawler.settings.get('DB_USER'),
                password=self.crawler.settings.get('DB_PASSWORD')
            )
            self.cursor = self.connection.cursor()
            self.connection.autocommit = False
            
            # Set downloads directory (where spider actually saves files)
            self.downloads_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'downloads'
            )
            
            logger.info("RBA Circular Flow Pipeline initialized")
            logger.info(f"Downloads directory: {self.downloads_dir}")
            
            # Initialize dimensions on first run
            self._initialize_dimensions()
            
            # Process CSV files
            self._process_csv_files()
            
        except Exception as e:
            logger.error(f"Error initializing RBA pipeline: {e}")
            raise

    def close_spider(self, spider):
        """Close database connection and cleanup"""
        if self.connection:
            self.connection.close()
        logger.info("RBA Circular Flow Pipeline closed")

    def process_item(self, item, spider):
        """Process individual items (currently pass-through for CSV-based processing)"""
        return item

    def _initialize_dimensions(self):
        """Initialize dimension tables with reference data"""
        try:
            logger.info("Initializing dimension tables...")
            
            # Populate time dimension for a reasonable range
            self._populate_time_dimension()
            
            # Dimension tables are pre-populated via DDL, so just log success
            logger.info("Dimension tables initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing dimensions: {e}")
            self.connection.rollback()
            raise

    def _populate_time_dimension(self):
        """Populate time dimension with date range"""
        try:
            # Use the stored function from DDL to populate time dimension
            # from 1959 to current year + 1
            current_year = datetime.now().year
            start_date = f"1959-01-01"
            end_date = f"{current_year + 1}-12-31"
            
            self.cursor.execute(
                "SELECT rba_dimensions.populate_time_dimension(%s, %s)",
                (start_date, end_date)
            )
            self.connection.commit()
            logger.info("Time dimension populated successfully")
            
        except Exception as e:
            logger.error(f"Error populating time dimension: {e}")
            self.connection.rollback()
            raise

    def _process_csv_files(self):
        """Process all CSV files in downloads directory"""
        if not os.path.exists(self.downloads_dir):
            logger.warning(f"Downloads directory not found: {self.downloads_dir}")
            return
        
        csv_files = [f for f in os.listdir(self.downloads_dir) if f.endswith('.csv')]
        logger.info(f"Found {len(csv_files)} CSV files to process")
        
        # Process primary mapping files first
        priority_files = list(self.STAGING_TABLE_MAP.keys())
        
        for filename in priority_files:
            if filename in csv_files:
                self._process_single_csv(filename)
        
        logger.info("CSV file processing completed")

    def _process_single_csv(self, filename: str):
        """Process a single CSV file"""
        try:
            file_path = os.path.join(self.downloads_dir, filename)
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                return
            
            if filename not in self.STAGING_TABLE_MAP:
                logger.debug(f"Skipping non-mapped file: {filename}")
                return
            
            logger.info(f"Processing {filename}...")
            
            # Parse CSV file
            metadata, data_rows = self._parse_rba_csv(file_path)
            
            if not data_rows:
                logger.warning(f"No data rows found in {filename}")
                return
            
            # Insert into staging table
            staging_table = self.STAGING_TABLE_MAP[filename]
            self._insert_staging_data(staging_table, filename, metadata, data_rows)
            
            # Process to fact tables
            self._process_to_facts(filename, staging_table, metadata)
            
            self.processed_files.add(filename)
            logger.info(f"Successfully processed {filename}")
            
        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")
            self.connection.rollback()
            raise

    def _parse_rba_csv(self, file_path: str) -> Tuple[Dict, List[Dict]]:
        """Parse RBA CSV file format and extract metadata and data"""
        try:
            # Read CSV file
            # Try UTF-8 first, fall back to latin-1 for special characters
            try:
                df = pd.read_csv(file_path, header=None, dtype=str, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, header=None, dtype=str, encoding='latin-1')
            
            # Extract metadata from header rows
            metadata = {
                'table_title': df.iloc[0, 0] if len(df) > 0 else '',
                'column_titles': df.iloc[1].tolist() if len(df) > 1 else [],
                'descriptions': df.iloc[2].tolist() if len(df) > 2 else [],
                'frequency': df.iloc[3].tolist() if len(df) > 3 else [],
                'adjustment_type': df.iloc[4].tolist() if len(df) > 4 else [],
                'units': df.iloc[5].tolist() if len(df) > 5 else [],
                'source': df.iloc[8].tolist() if len(df) > 8 else [],
                'publication_date': df.iloc[9].tolist() if len(df) > 9 else [],
                'series_ids': df.iloc[10].tolist() if len(df) > 10 else []
            }
            
            # Extract data rows (starting from row 11, index 11)
            data_rows = []
            if len(df) > 11:
                for idx in range(11, len(df)):
                    row = df.iloc[idx]
                    if pd.notna(row.iloc[0]) and str(row.iloc[0]).strip():  # Skip empty rows
                        data_rows.append(row.tolist())
            
            return metadata, data_rows
            
        except Exception as e:
            logger.error(f"Error parsing CSV {file_path}: {e}")
            raise

    def _insert_staging_data(self, staging_table: str, filename: str, metadata: Dict, data_rows: List[List]):
        """Insert data into staging table"""
        try:
            # Clear existing data for this extract date
            extract_date = date.today()
            self.cursor.execute(
                f"DELETE FROM {staging_table} WHERE extract_date = %s",
                (extract_date,)
            )
            
            # Prepare insert statement based on staging table structure
            # D1 and D2 tables don't have price_basis column
            if 'd1_financial_aggregates' in staging_table or 'd2_lending_credit' in staging_table:
                insert_sql = f"""
                    INSERT INTO {staging_table} (
                        extract_date, series_id, series_description, period_date,
                        value, unit, frequency, adjustment_type
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                include_price_basis = False
            else:
                insert_sql = f"""
                    INSERT INTO {staging_table} (
                        extract_date, series_id, series_description, period_date,
                        value, unit, frequency, adjustment_type, price_basis
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                include_price_basis = True
            
            # Process each data row
            for row_data in data_rows:
                try:
                    # Parse date from first column
                    period_date = self._parse_date(row_data[0])
                    if not period_date:
                        continue
                    
                    # Process each series in the row
                    for col_idx in range(1, len(row_data)):
                        if col_idx >= len(metadata['series_ids']) or not metadata['series_ids'][col_idx]:
                            continue
                        
                        series_id = metadata['series_ids'][col_idx]
                        if not series_id or str(series_id).strip() == '':
                            continue
                        
                        # Parse value
                        value = self._parse_numeric_value(row_data[col_idx])
                        if value is None:
                            continue
                        
                        # Extract metadata for this series
                        series_description = metadata['descriptions'][col_idx] if col_idx < len(metadata['descriptions']) else ''
                        unit = metadata['units'][col_idx] if col_idx < len(metadata['units']) else ''
                        frequency = metadata['frequency'][col_idx] if col_idx < len(metadata['frequency']) else ''
                        adjustment_type = metadata['adjustment_type'][col_idx] if col_idx < len(metadata['adjustment_type']) else ''
                        
                        # Determine price basis from description
                        price_basis = self._extract_price_basis(series_description)
                        
                        # Insert record with conditional parameters
                        if include_price_basis:
                            self.cursor.execute(insert_sql, (
                                extract_date,
                                series_id,
                                series_description,
                                period_date,
                                value,
                                unit,
                                frequency,
                                adjustment_type,
                                price_basis
                            ))
                        else:
                            self.cursor.execute(insert_sql, (
                                extract_date,
                                series_id,
                                series_description,
                                period_date,
                                value,
                                unit,
                                frequency,
                                adjustment_type
                            ))
                        
                except Exception as e:
                    logger.warning(f"Error processing row in {filename}: {e}")
                    continue
            
            self.connection.commit()
            logger.info(f"Inserted staging data for {staging_table}")
            
        except Exception as e:
            logger.error(f"Error inserting staging data for {staging_table}: {e}")
            self.connection.rollback()
            raise

    def _process_to_facts(self, filename: str, staging_table: str, metadata: Dict):
        """Process staging data to fact tables"""
        try:
            # Get component mappings for this file
            components = self.COMPONENT_MAPPINGS.get(filename, [])
            
            for component_code in components:
                self._process_component_to_facts(staging_table, component_code, filename)
            
            logger.info(f"Processed {filename} to fact tables for components: {components}")
            
        except Exception as e:
            logger.error(f"Error processing {filename} to facts: {e}")
            self.connection.rollback()
            raise

    def _process_component_to_facts(self, staging_table: str, component_code: str, filename: str):
        """Process specific component data to fact_circular_flow table"""
        try:
            # This is a simplified implementation - in production, you'd need more sophisticated
            # series matching logic based on the component mapping analysis
            
            # Handle tables with and without price_basis column
            if 'd1_financial_aggregates' in staging_table or 'd2_lending_credit' in staging_table:
                insert_sql = f"""
                    INSERT INTO rba_facts.fact_circular_flow (
                        time_key, component_key, source_key, measurement_key,
                        series_id, value, is_primary_series, data_quality_flag
                    )
                    SELECT
                        t.time_key,
                        c.component_key,
                        s.source_key,
                        m.measurement_key,
                        st.series_id,
                        st.value,
                        TRUE as is_primary_series,
                        'Good' as data_quality_flag
                    FROM {staging_table} st
                    JOIN rba_dimensions.dim_time t ON st.period_date = t.date_value
                    JOIN rba_dimensions.dim_circular_flow_component c ON c.component_code = %s
                    JOIN rba_dimensions.dim_data_source s ON s.csv_filename = %s
                    JOIN rba_dimensions.dim_measurement m ON
                        m.unit_description LIKE CONCAT('%%', st.unit, '%%') AND
                        m.price_basis = 'Current Prices' AND
                        m.adjustment_type = st.adjustment_type
                    WHERE st.extract_date = CURRENT_DATE
                      AND st.value IS NOT NULL
                    ON CONFLICT (time_key, component_key, source_key, measurement_key, series_id)
                    DO UPDATE SET
                        value = EXCLUDED.value,
                        updated_at = CURRENT_TIMESTAMP
                """
            else:
                insert_sql = f"""
                    INSERT INTO rba_facts.fact_circular_flow (
                        time_key, component_key, source_key, measurement_key,
                        series_id, value, is_primary_series, data_quality_flag
                    )
                    SELECT
                        t.time_key,
                        c.component_key,
                        s.source_key,
                        m.measurement_key,
                        st.series_id,
                        st.value,
                        TRUE as is_primary_series,
                        'Good' as data_quality_flag
                    FROM {staging_table} st
                    JOIN rba_dimensions.dim_time t ON st.period_date = t.date_value
                    JOIN rba_dimensions.dim_circular_flow_component c ON c.component_code = %s
                    JOIN rba_dimensions.dim_data_source s ON s.csv_filename = %s
                    JOIN rba_dimensions.dim_measurement m ON
                        m.unit_description LIKE CONCAT('%%', st.unit, '%%') AND
                        m.price_basis = 'Current Prices' AND
                        m.adjustment_type = st.adjustment_type
                    WHERE st.extract_date = CURRENT_DATE
                      AND st.value IS NOT NULL
                    ON CONFLICT (time_key, component_key, source_key, measurement_key, series_id)
                    DO UPDATE SET
                        value = EXCLUDED.value,
                        updated_at = CURRENT_TIMESTAMP
                """
            
            self.cursor.execute(insert_sql, (component_code, filename))
            self.connection.commit()
            
        except Exception as e:
            logger.error(f"Error processing component {component_code} from {staging_table}: {e}")
            self.connection.rollback()
            raise

    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string from RBA CSV format"""
        if not date_str or pd.isna(date_str):
            return None
        
        try:
            # Handle various RBA date formats
            date_str = str(date_str).strip()
            
            # Format: 30/09/1959
            if '/' in date_str:
                return datetime.strptime(date_str, '%d/%m/%Y').date()
            
            # Format: 1959-09-30
            if '-' in date_str:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not parse date: {date_str} - {e}")
            return None

    def _parse_numeric_value(self, value_str: str) -> Optional[float]:
        """Parse numeric value from CSV"""
        if not value_str or pd.isna(value_str):
            return None
        
        try:
            value_str = str(value_str).strip()
            if value_str == '' or value_str == 'n.a.' or value_str == '-':
                return None
            
            # Remove any non-numeric characters except decimal point and negative sign
            cleaned = re.sub(r'[^\d\.\-]', '', value_str)
            return float(cleaned) if cleaned else None
            
        except Exception as e:
            logger.warning(f"Could not parse numeric value: {value_str} - {e}")
            return None

    def _extract_price_basis(self, description: str) -> str:
        """Extract price basis from series description"""
        if not description:
            return 'Current Prices'
        
        description_lower = description.lower()
        
        if 'chain volume' in description_lower:
            return 'Chain Volume Measures'
        elif 'current prices' in description_lower:
            return 'Current Prices'
        elif 'nominal' in description_lower:
            return 'Nominal'
        else:
            return 'Current Prices'  # Default
"""Enhanced RBA Circular Flow Pipeline with detailed logging and diagnostics"""

import logging
import psycopg2
from datetime import datetime
from typing import Dict, List, Tuple
import traceback
from collections import defaultdict

from .pipelines import RBACircularFlowPipeline

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedRBACircularFlowPipeline(RBACircularFlowPipeline):
    """Enhanced version with better error handling and diagnostics"""
    
    def __init__(self):
        super().__init__()
        self.processing_stats = defaultdict(dict)
        self.errors_by_file = defaultdict(list)
        self.component_stats = defaultdict(int)
        
    def _process_component_to_facts(self, staging_table: str, component_code: str, filename: str):
        """Enhanced version with detailed logging"""
        start_time = datetime.now()
        logger.info(f"\n{'='*60}")
        logger.info(f"PROCESSING COMPONENT: {component_code} from {filename}")
        logger.info(f"Staging table: {staging_table}")
        logger.info(f"{'='*60}")
        
        try:
            # First, get the latest extract date
            date_sql = f"SELECT MAX(extract_date) FROM {staging_table}"
            self.cursor.execute(date_sql)
            latest_extract_date = self.cursor.fetchone()[0]
            
            if not latest_extract_date:
                logger.warning(f"No data found in {staging_table}")
                return
                
            logger.info(f"Using extract_date: {latest_extract_date}")
            
            # Now check what data we have in staging
            check_sql = f"""
                SELECT COUNT(*) as total_rows,
                       COUNT(DISTINCT series_id) as unique_series,
                       MIN(period_date) as earliest_date,
                       MAX(period_date) as latest_date,
                       COUNT(DISTINCT unit) as unique_units,
                       COUNT(DISTINCT adjustment_type) as unique_adjustments
                FROM {staging_table}
                WHERE extract_date = %s
            """
            self.cursor.execute(check_sql, (latest_extract_date,))
            staging_stats = self.cursor.fetchone()
            
            logger.info(f"Staging data summary:")
            logger.info(f"  - Total rows: {staging_stats[0]}")
            logger.info(f"  - Unique series: {staging_stats[1]}")
            logger.info(f"  - Date range: {staging_stats[2]} to {staging_stats[3]}")
            logger.info(f"  - Unique units: {staging_stats[4]}")
            logger.info(f"  - Unique adjustments: {staging_stats[5]}")
            
            # Check available measurements
            measure_sql = """
                SELECT unit_type, unit_description, price_basis, adjustment_type, measurement_key
                FROM rba_dimensions.dim_measurement
                ORDER BY unit_type, price_basis, adjustment_type
            """
            self.cursor.execute(measure_sql)
            measurements = self.cursor.fetchall()
            logger.debug(f"Available measurements: {len(measurements)}")
            for m in measurements:
                logger.debug(f"  - {m[0]}: {m[1]} | {m[2]} | {m[3]} (key={m[4]})")
            
            # Now check what units exist in staging
            unit_sql = f"""
                SELECT DISTINCT unit, adjustment_type, COUNT(*) as row_count
                FROM {staging_table}
                WHERE extract_date = %s
                GROUP BY unit, adjustment_type
                ORDER BY unit, adjustment_type
            """
            self.cursor.execute(unit_sql, (latest_extract_date,))
            staging_units = self.cursor.fetchall()
            logger.info(f"Units in staging data:")
            for unit, adj, count in staging_units:
                logger.info(f"  - Unit: '{unit}' | Adjustment: '{adj}' | Rows: {count}")
            
            # Diagnostic query to check measurement matching
            diag_sql = f"""
                SELECT DISTINCT 
                    st.unit,
                    st.adjustment_type,
                    m.measurement_key,
                    m.unit_description,
                    m.price_basis,
                    m.adjustment_type as dim_adjustment
                FROM {staging_table} st
                LEFT JOIN rba_dimensions.dim_measurement m ON
                    m.unit_description LIKE CONCAT('%%', st.unit, '%%') AND
                    m.price_basis = 'Current Prices' AND
                    m.adjustment_type = st.adjustment_type
                WHERE st.extract_date = %s
                LIMIT 10
            """
            self.cursor.execute(diag_sql, (latest_extract_date,))
            matches = self.cursor.fetchall()
            logger.info(f"Measurement matching diagnostics:")
            for match in matches:
                logger.info(f"  - Staging: unit='{match[0]}', adj='{match[1]}'")
                if match[2]:
                    logger.info(f"    → Matched: key={match[2]}, desc='{match[3]}', basis='{match[4]}', adj='{match[5]}'")
                else:
                    logger.warning(f"    → NO MATCH FOUND!")
            
            # Enhanced SQL with better error handling and logging
            if 'd1_financial_aggregates' in staging_table or 'd2_lending_credit' in staging_table:
                # For tables without price_basis column
                insert_sql = f"""
                    WITH insert_data AS (
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
                        LEFT JOIN rba_dimensions.dim_measurement m ON
                            m.unit_description LIKE CONCAT('%%', st.unit, '%%') AND
                            m.price_basis = 'Current Prices' AND
                            m.adjustment_type = st.adjustment_type
                        WHERE st.extract_date = CURRENT_DATE
                          AND st.value IS NOT NULL
                    )
                    INSERT INTO rba_facts.fact_circular_flow (
                        time_key, component_key, source_key, measurement_key,
                        series_id, value, is_primary_series, data_quality_flag
                    )
                    SELECT * FROM insert_data WHERE measurement_key IS NOT NULL
                    ON CONFLICT (time_key, component_key, source_key, measurement_key, series_id)
                    DO UPDATE SET
                        value = EXCLUDED.value,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING series_id
                """
            else:
                # For tables with price_basis column
                insert_sql = f"""
                    WITH insert_data AS (
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
                        LEFT JOIN rba_dimensions.dim_measurement m ON
                            m.unit_description LIKE CONCAT('%%', st.unit, '%%') AND
                            COALESCE(st.price_basis, 'Current Prices') = m.price_basis AND
                            m.adjustment_type = st.adjustment_type
                        WHERE st.extract_date = CURRENT_DATE
                          AND st.value IS NOT NULL
                    )
                    INSERT INTO rba_facts.fact_circular_flow (
                        time_key, component_key, source_key, measurement_key,
                        series_id, value, is_primary_series, data_quality_flag
                    )
                    SELECT * FROM insert_data WHERE measurement_key IS NOT NULL
                    ON CONFLICT (time_key, component_key, source_key, measurement_key, series_id)
                    DO UPDATE SET
                        value = EXCLUDED.value,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING series_id
                """
            
            # Execute with detailed result tracking
            self.cursor.execute(insert_sql, (component_code, filename))
            inserted_series = [row[0] for row in self.cursor.fetchall()]
            rows_affected = self.cursor.rowcount
            self.connection.commit()
            
            # Check for unmapped data
            unmatched_sql = f"""
                SELECT COUNT(*) as unmatched_rows,
                       COUNT(DISTINCT series_id) as unmatched_series
                FROM {staging_table} st
                LEFT JOIN rba_dimensions.dim_measurement m ON
                    m.unit_description LIKE CONCAT('%%', st.unit, '%%') AND
                    m.price_basis = 'Current Prices' AND
                    m.adjustment_type = st.adjustment_type
                WHERE st.extract_date = CURRENT_DATE
                  AND st.value IS NOT NULL
                  AND m.measurement_key IS NULL
            """
            self.cursor.execute(unmatched_sql)
            unmatched = self.cursor.fetchone()
            
            # Record stats
            elapsed = (datetime.now() - start_time).total_seconds()
            self.processing_stats[filename][component_code] = {
                'rows_inserted': rows_affected,
                'series_count': len(set(inserted_series)),
                'elapsed_seconds': elapsed,
                'unmatched_rows': unmatched[0],
                'unmatched_series': unmatched[1]
            }
            self.component_stats[component_code] += rows_affected
            
            logger.info(f"✓ SUCCESS: Component {component_code}")
            logger.info(f"  - Rows inserted/updated: {rows_affected}")
            logger.info(f"  - Unique series: {len(set(inserted_series))}")
            logger.info(f"  - Unmatched rows: {unmatched[0]} ({unmatched[1]} series)")
            logger.info(f"  - Processing time: {elapsed:.2f} seconds")
            
            if unmatched[0] > 0:
                logger.warning(f"⚠️  WARNING: {unmatched[0]} rows could not be matched to measurements!")
                # Show sample of unmatched data
                sample_sql = f"""
                    SELECT DISTINCT st.unit, st.adjustment_type, COUNT(*) as count
                    FROM {staging_table} st
                    LEFT JOIN rba_dimensions.dim_measurement m ON
                        m.unit_description LIKE CONCAT('%%', st.unit, '%%') AND
                        m.price_basis = 'Current Prices' AND
                        m.adjustment_type = st.adjustment_type
                    WHERE st.extract_date = CURRENT_DATE
                      AND st.value IS NOT NULL
                      AND m.measurement_key IS NULL
                    GROUP BY st.unit, st.adjustment_type
                    LIMIT 5
                """
                self.cursor.execute(sample_sql)
                for unit, adj, count in self.cursor.fetchall():
                    logger.warning(f"    - Unit: '{unit}', Adjustment: '{adj}' ({count} rows)")
            
        except Exception as e:
            logger.error(f"❌ ERROR processing component {component_code} from {staging_table}")
            logger.error(f"Error details: {str(e)}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            
            self.errors_by_file[filename].append({
                'component': component_code,
                'error': str(e),
                'traceback': traceback.format_exc()
            })
            
            self.connection.rollback()
            raise
    
    def close_spider(self, spider):
        """Enhanced close with summary report"""
        logger.info("\n" + "="*80)
        logger.info("RBA CIRCULAR FLOW ETL SUMMARY REPORT")
        logger.info("="*80)
        
        # Component summary
        logger.info("\nCOMPONENT PROCESSING SUMMARY:")
        total_rows = 0
        for component, rows in sorted(self.component_stats.items()):
            logger.info(f"  {component}: {rows:,} rows")
            total_rows += rows
        logger.info(f"  TOTAL: {total_rows:,} rows")
        
        # File processing details
        logger.info("\nFILE PROCESSING DETAILS:")
        for filename, components in sorted(self.processing_stats.items()):
            logger.info(f"\n  {filename}:")
            for component, stats in components.items():
                logger.info(f"    - {component}: {stats['rows_inserted']:,} rows, "
                          f"{stats['series_count']} series, "
                          f"{stats['elapsed_seconds']:.1f}s")
                if stats['unmatched_rows'] > 0:
                    logger.warning(f"      ⚠️  Unmatched: {stats['unmatched_rows']:,} rows")
        
        # Error summary
        if self.errors_by_file:
            logger.error("\n❌ ERRORS ENCOUNTERED:")
            for filename, errors in self.errors_by_file.items():
                logger.error(f"\n  {filename}:")
                for error in errors:
                    logger.error(f"    - Component {error['component']}: {error['error']}")
        
        # Final data quality check
        try:
            self.cursor.execute("""
                SELECT 
                    c.component_code,
                    COUNT(DISTINCT f.series_id) as series_count,
                    COUNT(*) as total_rows,
                    MIN(t.date_value) as earliest,
                    MAX(t.date_value) as latest
                FROM rba_facts.fact_circular_flow f
                JOIN rba_dimensions.dim_circular_flow_component c ON f.component_key = c.component_key
                JOIN rba_dimensions.dim_time t ON f.time_key = t.time_key
                GROUP BY c.component_code
                ORDER BY c.component_code
            """)
            
            logger.info("\nFINAL FACT TABLE STATUS:")
            results = self.cursor.fetchall()
            for code, series, rows, earliest, latest in results:
                logger.info(f"  {code}: {series} series, {rows:,} rows, {earliest} to {latest}")
            
            # Check circular flow balance
            self.cursor.execute("SELECT COUNT(*) FROM rba_analytics.v_circular_flow_balance")
            balance_rows = self.cursor.fetchone()[0]
            logger.info(f"\nCircular flow balance view: {balance_rows} periods available")
            
        except Exception as e:
            logger.error(f"Error in final check: {e}")
        
        # Call parent close
        super().close_spider(spider)
        
        logger.info("\n" + "="*80)
        logger.info("ETL PROCESSING COMPLETE")
        logger.info("="*80 + "\n")
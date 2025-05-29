#!/usr/bin/env python3
"""Process missing components from already-staged data"""

import psycopg2
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('/home/websinthe/code/econcell/.env')

# Database connection
conn = psycopg2.connect(
    host=os.getenv('PSQL_HOST'),
    port=os.getenv('PSQL_PORT'),
    database=os.getenv('PSQL_DB'),
    user=os.getenv('PSQL_USER'),
    password=os.getenv('PSQL_PW')
)
cursor = conn.cursor()

def process_i1_components():
    """Process X and M components from i1_trade_bop"""
    logger.info("Processing i1_trade_bop for X (Exports) and M (Imports)")
    
    # Process Exports (X)
    sql_exports = """
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
        FROM rba_staging.i1_trade_bop st
        JOIN rba_dimensions.dim_time t ON st.period_date = t.date_value
        JOIN rba_dimensions.dim_circular_flow_component c ON c.component_code = 'X'
        JOIN rba_dimensions.dim_data_source s ON s.csv_filename = 'i1-data.csv'
        JOIN rba_dimensions.dim_measurement m ON
            TRIM(m.unit_description) = TRIM(st.unit) AND
            m.price_basis = COALESCE(st.price_basis, 'Current Prices') AND
            m.adjustment_type = st.adjustment_type
        WHERE st.extract_date = (SELECT MAX(extract_date) FROM rba_staging.i1_trade_bop)
          AND st.value IS NOT NULL
          AND st.series_description ILIKE '%export%'
        ON CONFLICT (time_key, component_key, source_key, measurement_key, series_id)
        DO UPDATE SET
            value = EXCLUDED.value,
            updated_at = CURRENT_TIMESTAMP
    """
    
    cursor.execute(sql_exports)
    exports_count = cursor.rowcount
    conn.commit()
    logger.info(f"✓ Exports (X): {exports_count} rows inserted/updated")
    
    # Process Imports (M)
    sql_imports = """
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
        FROM rba_staging.i1_trade_bop st
        JOIN rba_dimensions.dim_time t ON st.period_date = t.date_value
        JOIN rba_dimensions.dim_circular_flow_component c ON c.component_code = 'M'
        JOIN rba_dimensions.dim_data_source s ON s.csv_filename = 'i1-data.csv'
        JOIN rba_dimensions.dim_measurement m ON
            TRIM(m.unit_description) = TRIM(st.unit) AND
            m.price_basis = COALESCE(st.price_basis, 'Current Prices') AND
            m.adjustment_type = st.adjustment_type
        WHERE st.extract_date = (SELECT MAX(extract_date) FROM rba_staging.i1_trade_bop)
          AND st.value IS NOT NULL
          AND st.series_description ILIKE '%import%'
        ON CONFLICT (time_key, component_key, source_key, measurement_key, series_id)
        DO UPDATE SET
            value = EXCLUDED.value,
            updated_at = CURRENT_TIMESTAMP
    """
    
    cursor.execute(sql_imports)
    imports_count = cursor.rowcount
    conn.commit()
    logger.info(f"✓ Imports (M): {imports_count} rows inserted/updated")
    
    return exports_count, imports_count

def check_final_status():
    """Check final component coverage"""
    cursor.execute("""
        SELECT 
            c.component_code,
            c.component_name,
            COUNT(DISTINCT f.series_id) as series,
            COUNT(*) as rows
        FROM rba_dimensions.dim_circular_flow_component c
        LEFT JOIN rba_facts.fact_circular_flow f ON c.component_key = f.component_key
        GROUP BY c.component_code, c.component_name
        ORDER BY c.component_code
    """)
    
    print("\nFINAL COMPONENT STATUS:")
    print("-" * 60)
    print(f"{'Component':<10} {'Name':<25} {'Series':<10} {'Rows':<10}")
    print("-" * 60)
    
    for code, name, series, rows in cursor.fetchall():
        status = "✓" if rows > 0 else "✗"
        print(f"{status} {code:<8} {name:<25} {series or 0:<10} {rows:<10}")

if __name__ == "__main__":
    try:
        # Process missing components
        process_i1_components()
        
        # Check final status
        check_final_status()
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        conn.rollback()
        raise
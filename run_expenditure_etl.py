#!/usr/bin/env python3
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

# Read SQL file
with open('src/econdata/sql/expenditure_etl.sql', 'r') as f:
    sql_script = f.read()

# Connect to database
conn = psycopg2.connect(
    dbname=os.getenv('PSQL_DB'),
    user=os.getenv('PSQL_USER'),
    password=os.getenv('PSQL_PW'),
    host=os.getenv('PSQL_HOST'),
    port=os.getenv('PSQL_PORT')
)

cur = conn.cursor()

try:
    # Execute the SQL script
    cur.execute(sql_script)
    conn.commit()
    print("✓ Expenditure ETL functions created successfully")
    
    # Run validation
    print("\nRunning G component validation...")
    cur.execute("SELECT * FROM abs_staging.validate_g_component()")
    for row in cur.fetchall():
        check_name, status, details = row
        symbol = "✓" if status == "PASS" else "⚠" if status == "WARNING" else "ℹ"
        print(f"{symbol} {check_name}: {status} - {details}")
    
    # Execute the ETL
    print("\nExecuting expenditure ETL...")
    cur.execute("SELECT * FROM abs_staging.process_expenditure_to_facts_simple()")
    result = cur.fetchone()
    records_processed, records_inserted, records_updated, errors = result
    
    if errors and errors[0] is not None:
        print(f"✗ ETL failed with errors: {errors}")
    else:
        print(f"✓ ETL completed successfully:")
        print(f"  - Records processed: {records_processed}")
        print(f"  - Records inserted: {records_inserted}")
        print(f"  - Records updated: {records_updated}")
    
    conn.commit()
    
    # Check final state
    print("\nChecking G component in fact table...")
    cur.execute("""
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT series_id) as unique_series,
            MIN(dt.date_value) as earliest_date,
            MAX(dt.date_value) as latest_date,
            SUM(f.value) as total_value
        FROM rba_facts.fact_circular_flow f
        JOIN rba_dimensions.dim_circular_flow_component c ON f.component_key = c.component_key
        JOIN rba_dimensions.dim_time dt ON f.time_key = dt.time_key
        WHERE c.component_code = 'G'
    """)
    result = cur.fetchone()
    print(f"  Total G records: {result[0]}")
    print(f"  Unique series: {result[1]}")
    print(f"  Date range: {result[2]} to {result[3]}")
    print(f"  Total value: ${result[4]:,.2f} million")
    
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    cur.close()
    conn.close()
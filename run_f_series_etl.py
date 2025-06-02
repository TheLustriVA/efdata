#!/usr/bin/env python3
"""
F-Series ETL Runner
Date: June 2, 2025
Author: Claude & Kieran
Purpose: Execute F-series schema creation, data loading, and ETL
"""

import psycopg2
from dotenv import load_dotenv
import os
import sys
from datetime import datetime

# Add src to path for imports
sys.path.append('/home/websinthe/code/econcell/src')
from econdata.parse_f_series import FSeriesParser

load_dotenv()

def execute_sql_file(conn, filepath):
    """Execute SQL file"""
    with open(filepath, 'r') as f:
        sql = f.read()
    
    cur = conn.cursor()
    try:
        cur.execute(sql)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error executing {filepath}: {e}")
        return False
    finally:
        cur.close()

def main():
    print("F-Series ETL Pipeline")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Connect to database
    conn = psycopg2.connect(
        dbname=os.getenv('PSQL_DB'),
        user=os.getenv('PSQL_USER'),
        password=os.getenv('PSQL_PW'),
        host=os.getenv('PSQL_HOST'),
        port=os.getenv('PSQL_PORT')
    )
    
    try:
        # Step 1: Create schema
        print("Step 1: Creating F-series schema...")
        if execute_sql_file(conn, 'src/econdata/sql/f_series_schema.sql'):
            print("  ✓ Schema created successfully")
        else:
            print("  ⚠ Schema may already exist, continuing...")
        
        # Step 2: Create ETL functions
        print("\nStep 2: Creating ETL functions...")
        if execute_sql_file(conn, 'src/econdata/sql/f_series_etl.sql'):
            print("  ✓ ETL functions created successfully")
        else:
            print("  ✗ ETL function creation failed")
            return
        
        # Step 3: Load F-series CSV data
        print("\nStep 3: Loading F-series CSV files...")
        parser = FSeriesParser()
        
        # Load key tables for circular flow
        key_tables = ['F1', 'F4', 'F5', 'F6', 'F7']
        download_dir = '/home/websinthe/code/econcell/src/econdata/downloads'
        
        results = parser.process_f_series_files(download_dir, key_tables)
        parser.close()
        
        # Show loading summary
        total_loaded = sum(r['records'] for r in results.values() if r['status'] == 'success')
        print(f"\n  Summary: Loaded {total_loaded} records from {len(results)} files")
        
        # Step 4: Run data validation
        print("\nStep 4: Validating staged data...")
        cur = conn.cursor()
        cur.execute("SELECT * FROM rba_staging.validate_f_series_data()")
        for check_name, status, details in cur.fetchall():
            symbol = "✓" if status == "PASS" else "⚠" if status == "WARNING" else "ℹ"
            print(f"  {symbol} {check_name}: {status} - {details}")
        cur.close()
        
        # Step 5: Execute ETL to facts table
        print("\nStep 5: Processing data into facts table...")
        cur = conn.cursor()
        cur.execute("SELECT * FROM rba_staging.process_f_series_to_facts()")
        result = cur.fetchone()
        records_processed, records_inserted, records_updated, errors = result
        
        if errors and errors[0] is not None:
            print(f"  ✗ ETL failed with errors: {errors}")
        else:
            print(f"  ✓ ETL completed successfully:")
            print(f"    - Records processed: {records_processed}")
            print(f"    - Records inserted: {records_inserted}")
            print(f"    - Records updated: {records_updated}")
        
        conn.commit()
        cur.close()
        
        # Step 6: Update circular flow with interest rates
        print("\nStep 6: Linking interest rates to circular flow...")
        cur = conn.cursor()
        cur.execute("SELECT rba_analytics.update_circular_flow_with_rates()")
        conn.commit()
        print("  ✓ Interest rates linked to S and I components")
        cur.close()
        
        # Step 7: Validate integration
        print("\nStep 7: Validating circular flow integration...")
        cur = conn.cursor()
        cur.execute("SELECT * FROM rba_analytics.validate_rate_impact()")
        for check_name, status, details in cur.fetchall():
            symbol = "✓" if status == "PASS" else "⚠" if status == "WARNING" else "ℹ"
            print(f"  {symbol} {check_name}: {status} - {details}")
        cur.close()
        
        # Final summary
        print("\n" + "=" * 60)
        print("F-Series ETL Pipeline Complete!")
        print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Show sample rates
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                irt.rate_name,
                COUNT(*) as observations,
                MIN(fir.rate_value) as min_rate,
                AVG(fir.rate_value) as avg_rate,
                MAX(fir.rate_value) as max_rate
            FROM rba_facts.fact_interest_rates fir
            JOIN rba_dimensions.dim_interest_rate_type irt ON fir.rate_type_key = irt.rate_type_key
            GROUP BY irt.rate_name
            ORDER BY irt.rate_name
            LIMIT 10
        """)
        
        print("\nSample Interest Rates Summary:")
        print("-" * 80)
        print(f"{'Rate Type':<40} {'Obs':<8} {'Min %':<8} {'Avg %':<8} {'Max %':<8}")
        print("-" * 80)
        
        for row in cur.fetchall():
            rate_name = row[0][:39]  # Truncate long names
            print(f"{rate_name:<40} {row[1]:<8} {row[2]:<8.2f} {row[3]:<8.2f} {row[4]:<8.2f}")
        
        cur.close()
        
    except Exception as e:
        print(f"\nERROR: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
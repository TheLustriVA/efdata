#!/usr/bin/env python3
"""
Script to populate the currencies table from country_codes.json
"""

import json
import os
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

def load_currencies_from_json():
    """Load currency data from the JSON file"""
    json_path = '/home/websinthe/code/econcell/src/econdata/econdata/spiders/country_codes.json'
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['countries']
    except FileNotFoundError:
        print(f"Error: Could not find {json_path}")
        raise
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {json_path}")
        raise

def connect_to_database():
    """Connect to PostgreSQL database using environment variables"""
    # Load environment variables the same way as settings.py
    load_dotenv('/home/websinthe/code/econcell/.env')
    
    db_config = {
        'host': os.getenv("PSQL_HOST"),
        'port': os.getenv("PSQL_PORT"),
        'database': os.getenv("PSQL_DB"),
        'user': os.getenv("PSQL_USER"),
        'password': os.getenv("PSQL_PW")
    }
    
    # Check that all required environment variables are set
    missing_vars = [key for key, value in db_config.items() if value is None]
    if missing_vars:
        raise ValueError(f"Missing environment variables: {missing_vars}")
    
    try:
        conn = psycopg2.connect(**db_config)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        raise

def populate_currencies_table(currencies_data):
    """Insert currency data into the currencies table"""
    conn = connect_to_database()
    
    try:
        with conn.cursor() as cursor:
            # Prepare data for bulk insert
            currency_records = [
                (country['country'], country['currency'], country['code'])
                for country in currencies_data
            ]
            
            # Use ON CONFLICT to handle duplicates (in case AUD already exists)
            insert_query = """
                INSERT INTO currencies (country, currency_name, code)
                VALUES %s
                ON CONFLICT (code) DO UPDATE SET
                    country = EXCLUDED.country,
                    currency_name = EXCLUDED.currency_name
            """
            
            execute_values(cursor, insert_query, currency_records)
            conn.commit()
            
            print(f"Successfully inserted/updated {len(currency_records)} currency records")
            
            # Verify the data was inserted
            cursor.execute("SELECT COUNT(*) FROM currencies")
            count = cursor.fetchone()[0]
            print(f"Total currencies in table: {count}")
            
    except psycopg2.Error as e:
        conn.rollback()
        print(f"Database error: {e}")
        raise
    finally:
        conn.close()

def main():
    """Main function"""
    print("Loading currencies from JSON file...")
    currencies_data = load_currencies_from_json()
    print(f"Found {len(currencies_data)} currencies in JSON file")
    
    print("Connecting to database and populating currencies table...")
    populate_currencies_table(currencies_data)
    
    print("Currency population completed successfully!")

if __name__ == "__main__":
    main()
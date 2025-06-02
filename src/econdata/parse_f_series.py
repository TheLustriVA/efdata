#!/usr/bin/env python3
"""
F-Series CSV Parser and Loader
Date: June 2, 2025
Author: Claude & Kieran
Purpose: Parse RBA F-series CSV files and load into staging table
"""

import csv
import psycopg2
from dotenv import load_dotenv
import os
from datetime import datetime
import re
from pathlib import Path

load_dotenv()

class FSeriesParser:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=os.getenv('PSQL_DB'),
            user=os.getenv('PSQL_USER'),
            password=os.getenv('PSQL_PW'),
            host=os.getenv('PSQL_HOST'),
            port=os.getenv('PSQL_PORT')
        )
        self.cur = self.conn.cursor()
        
    def parse_f_series_csv(self, filepath):
        """Parse an F-series CSV file and return structured data"""
        table_code = self._extract_table_code(filepath)
        data = []
        
        # Try different encodings as RBA files may use Windows-1252
        encodings = ['utf-8', 'windows-1252', 'iso-8859-1', 'cp1252']
        lines = None
        
        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    lines = f.readlines()
                break
            except UnicodeDecodeError:
                continue
        
        if lines is None:
            raise ValueError(f"Could not decode {filepath} with any known encoding")
            
        # Find the header rows
        title_row = None
        description_row = None
        frequency_row = None
        type_row = None
        units_row = None
        source_row = None
        publication_row = None
        series_id_row = None
        data_start_row = None
        
        for i, line in enumerate(lines):
            if line.startswith('Title,'):
                title_row = i
            elif line.startswith('Description,'):
                description_row = i
            elif line.startswith('Frequency,'):
                frequency_row = i
            elif line.startswith('Type,'):
                type_row = i
            elif line.startswith('Units,'):
                units_row = i
            elif line.startswith('Source,'):
                source_row = i
            elif line.startswith('Publication date,'):
                publication_row = i
            elif line.startswith('Series ID,'):
                series_id_row = i
                data_start_row = i + 1
                break
        
        if not all([title_row is not None, series_id_row is not None]):
            raise ValueError(f"Could not find required headers in {filepath}")
        
        # Parse headers
        titles = self._parse_csv_line(lines[title_row])
        descriptions = self._parse_csv_line(lines[description_row]) if description_row else titles
        frequencies = self._parse_csv_line(lines[frequency_row]) if frequency_row else []
        types = self._parse_csv_line(lines[type_row]) if type_row else []
        units = self._parse_csv_line(lines[units_row]) if units_row else []
        sources = self._parse_csv_line(lines[source_row]) if source_row else []
        pub_dates = self._parse_csv_line(lines[publication_row]) if publication_row else []
        series_ids = self._parse_csv_line(lines[series_id_row])
        
        # Extract table name from first line
        table_name = lines[0].strip().rstrip(',')
        
        # Parse data rows
        for line in lines[data_start_row:]:
            if not line.strip() or line.strip() == ',':
                continue
                
            values = self._parse_csv_line(line)
            if not values or not values[0]:  # Skip empty rows
                continue
                
            date_str = values[0]
            observation_date = self._parse_date(date_str)
            if not observation_date:
                continue
            
            # Process each series column
            for i in range(1, len(values)):
                if i >= len(series_ids) or not series_ids[i]:
                    continue
                    
                value_str = values[i]
                if not value_str or value_str == '':
                    continue
                    
                try:
                    value = float(value_str)
                except ValueError:
                    continue
                
                record = {
                    'table_code': table_code,
                    'table_name': table_name,
                    'source_file': os.path.basename(filepath),
                    'series_id': series_ids[i],
                    'series_title': titles[i] if i < len(titles) else None,
                    'series_description': descriptions[i] if i < len(descriptions) else None,
                    'observation_date': observation_date,
                    'frequency': frequencies[i] if i < len(frequencies) else None,
                    'value': value,
                    'unit': units[i] if i < len(units) else None,
                    'type': types[i] if i < len(types) else None,
                    'source_org': sources[i] if i < len(sources) else None,
                    'publication_date': self._parse_date(pub_dates[i]) if i < len(pub_dates) and pub_dates[i] else None
                }
                data.append(record)
        
        return data
    
    def _extract_table_code(self, filepath):
        """Extract table code from filename (e.g., 'f1-data.csv' -> 'F1')"""
        filename = os.path.basename(filepath)
        match = re.match(r'(f\d+(?:\.\d+)?)', filename, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return 'F-UNKNOWN'
    
    def _parse_csv_line(self, line):
        """Parse a CSV line, handling commas in quoted fields"""
        reader = csv.reader([line])
        return list(reader)[0] if reader else []
    
    def _parse_date(self, date_str):
        """Parse various date formats used in RBA data"""
        if not date_str:
            return None
            
        # Try different date formats
        formats = [
            '%d-%b-%Y',    # 04-Jan-2011
            '%d/%m/%Y',    # 31/12/1981
            '%Y-%m-%d',    # 2011-01-04
            '%d-%b-%y',    # 04-Jan-11
            '%d-%m-%Y'     # 04-01-2011
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        return None
    
    def load_to_staging(self, data):
        """Load parsed data into staging table"""
        if not data:
            return 0
            
        insert_sql = """
            INSERT INTO rba_staging.f_series_rates (
                table_code, table_name, source_file, series_id,
                series_title, series_description, observation_date,
                frequency, value, unit, type, source_org, publication_date
            ) VALUES (
                %(table_code)s, %(table_name)s, %(source_file)s, %(series_id)s,
                %(series_title)s, %(series_description)s, %(observation_date)s,
                %(frequency)s, %(value)s, %(unit)s, %(type)s, %(source_org)s, %(publication_date)s
            )
            ON CONFLICT (table_code, series_id, observation_date) 
            DO UPDATE SET
                value = EXCLUDED.value,
                updated_at = CURRENT_TIMESTAMP
        """
        
        try:
            self.cur.executemany(insert_sql, data)
            self.conn.commit()
            return len(data)
        except Exception as e:
            self.conn.rollback()
            print(f"Error loading data: {e}")
            raise
    
    def process_f_series_files(self, directory_path, table_codes=None):
        """Process multiple F-series files"""
        results = {}
        download_dir = Path(directory_path)
        
        # If specific table codes requested, process only those
        if table_codes:
            patterns = [f"f{code.lower().replace('f', '')}-*.csv" for code in table_codes]
        else:
            patterns = ["f*-data.csv"]
        
        for pattern in patterns:
            for filepath in download_dir.glob(pattern):
                print(f"\nProcessing {filepath.name}...")
                try:
                    data = self.parse_f_series_csv(filepath)
                    records_loaded = self.load_to_staging(data)
                    results[filepath.name] = {
                        'status': 'success',
                        'records': records_loaded
                    }
                    print(f"  ✓ Loaded {records_loaded} records")
                except Exception as e:
                    results[filepath.name] = {
                        'status': 'error',
                        'error': str(e)
                    }
                    print(f"  ✗ Error: {e}")
        
        return results
    
    def close(self):
        """Close database connection"""
        self.cur.close()
        self.conn.close()


def main():
    """Main function to process F-series files"""
    parser = FSeriesParser()
    
    # Process key F-series tables for circular flow
    key_tables = ['F1', 'F4', 'F5', 'F6', 'F7']
    download_dir = '/home/websinthe/code/econcell/src/econdata/downloads'
    
    print("F-Series Data Loader")
    print("=" * 50)
    
    try:
        results = parser.process_f_series_files(download_dir, key_tables)
        
        # Summary
        print("\nSummary:")
        print("-" * 50)
        total_records = 0
        errors = 0
        
        for filename, result in results.items():
            if result['status'] == 'success':
                total_records += result['records']
            else:
                errors += 1
        
        print(f"Files processed: {len(results)}")
        print(f"Total records loaded: {total_records}")
        print(f"Errors: {errors}")
        
    finally:
        parser.close()


if __name__ == "__main__":
    main()
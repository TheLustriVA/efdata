#!/usr/bin/env python3
"""
Database Integrity Check Script
Validates staging data for cross-contamination, data type issues, and structural problems.

Author: Claude & Kieran
Date: June 1, 2025
"""

import psycopg2
import pandas as pd
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any
from decimal import Decimal
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseIntegrityChecker:
    """Checks database integrity for cross-contamination and data corruption."""
    
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.issues = {
            'CRITICAL': [],
            'WARNING': [],
            'INFO': [],
            'NOTERROR': []
        }
        self.stats = {
            'tables_checked': 0,
            'records_checked': 0,
            'issues_found': 0
        }
        
    def connect(self):
        """Establish database connection."""
        return psycopg2.connect(**self.db_config)
    
    def check_cross_contamination(self):
        """Check for data fields appearing in wrong tables."""
        logger.info("Checking for cross-contamination between tables...")
        
        with self.connect() as conn:
            cur = conn.cursor()
            
            # Check if expenditure fields exist in taxation table
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'abs_staging' 
                AND table_name = 'government_finance_statistics'
                AND column_name IN ('expenditure_type', 'expenditure_category', 'cofog_code', 
                                   'is_current_expenditure', 'is_capital_expenditure')
            """)
            
            contamination_fields = cur.fetchall()
            if contamination_fields:
                self.add_issue('CRITICAL', 
                    f"Found expenditure fields in taxation table: {[f[0] for f in contamination_fields]}")
            
            # Check if taxation-specific fields exist in expenditure table
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'abs_staging' 
                AND table_name = 'government_expenditure'
                AND column_name IN ('revenue_type', 'tax_category')
            """)
            
            contamination_fields = cur.fetchall()
            if contamination_fields:
                self.add_issue('CRITICAL',
                    f"Found taxation fields in expenditure table: {[f[0] for f in contamination_fields]}")
            
            # Check for misplaced records based on content
            cur.execute("""
                SELECT COUNT(*), MIN(id), MAX(id)
                FROM abs_staging.government_finance_statistics
                WHERE revenue_type ILIKE '%expense%' 
                   OR revenue_type ILIKE '%expenditure%'
                   OR revenue_type ILIKE '%spending%'
            """)
            
            count, min_id, max_id = cur.fetchone()
            if count > 0:
                self.add_issue('CRITICAL',
                    f"Found {count} expenditure records in taxation table (IDs {min_id}-{max_id})")
                    
    def check_data_type_integrity(self):
        """Check for data type issues like truncated decimals."""
        logger.info("Checking data type integrity...")
        
        with self.connect() as conn:
            # Check for integer-stored amounts that should be decimals
            queries = [
                ("government_finance_statistics", "amount"),
                ("government_expenditure", "amount")
            ]
            
            for table, amount_col in queries:
                cur = conn.cursor()
                
                # Look for suspiciously round numbers that might be truncated
                cur.execute(f"""
                    SELECT COUNT(*), 
                           SUM(CASE WHEN {amount_col}::numeric % 1 = 0 THEN 1 ELSE 0 END) as whole_numbers,
                           SUM(CASE WHEN {amount_col}::numeric % 10 = 0 THEN 1 ELSE 0 END) as round_tens,
                           SUM(CASE WHEN {amount_col}::numeric % 100 = 0 THEN 1 ELSE 0 END) as round_hundreds
                    FROM abs_staging.{table}
                    WHERE {amount_col} IS NOT NULL AND {amount_col} > 0
                """)
                
                total, whole, tens, hundreds = cur.fetchone()
                
                # If more than 90% are whole numbers, likely truncation
                if total > 0:
                    whole_pct = (whole / total) * 100
                    if whole_pct > 90:
                        self.add_issue('WARNING',
                            f"{table}: {whole_pct:.1f}% of amounts are whole numbers - possible decimal truncation")
                    elif whole_pct > 95:
                        self.add_issue('CRITICAL',
                            f"{table}: {whole_pct:.1f}% of amounts are whole numbers - likely decimal truncation")
                    
                    # Check for amounts that look like they're missing decimal places
                    cur.execute(f"""
                        SELECT {amount_col}, COUNT(*) as occurrences
                        FROM abs_staging.{table}
                        WHERE {amount_col} > 1000000 
                          AND {amount_col}::numeric % 100 = 0
                        GROUP BY {amount_col}
                        ORDER BY COUNT(*) DESC
                        LIMIT 5
                    """)
                    
                    suspicious_amounts = cur.fetchall()
                    if suspicious_amounts:
                        examples = [f"${amt:,.0f} ({cnt} times)" for amt, cnt in suspicious_amounts[:3]]
                        self.add_issue('INFO',
                            f"{table}: Large round amounts found - verify if correct: {', '.join(examples)}")
                            
    def check_column_shifts(self):
        """Check for misaligned data from parsing errors."""
        logger.info("Checking for column shift errors...")
        
        with self.connect() as conn:
            cur = conn.cursor()
            
            # Check if government levels appear in wrong fields
            gov_levels = ['Commonwealth', 'State', 'Local', 'NSW State', 'VIC State', 
                         'QLD State', 'WA State', 'SA State', 'TAS State', 'ACT Territory', 'NT Territory']
            
            # Check expenditure table
            for col in ['expenditure_type', 'expenditure_category']:
                cur.execute(f"""
                    SELECT {col}, COUNT(*) 
                    FROM abs_staging.government_expenditure
                    WHERE {col} IN %s
                    GROUP BY {col}
                """, (tuple(gov_levels),))
                
                misplaced = cur.fetchall()
                if misplaced:
                    for value, count in misplaced:
                        self.add_issue('CRITICAL',
                            f"Government level '{value}' found in {col} field ({count} records) - likely column shift")
            
            # Check for dates in text fields
            cur.execute("""
                SELECT COUNT(*)
                FROM abs_staging.government_expenditure
                WHERE expenditure_type ~ '^\\d{4}-\\d{2}-\\d{2}$'
            """)
            
            date_in_text = cur.fetchone()[0]
            if date_in_text > 0:
                self.add_issue('CRITICAL',
                    f"Found {date_in_text} date values in expenditure_type field - column shift detected")
                    
    def check_encoding_issues(self):
        """Check for UTF-8 encoding problems."""
        logger.info("Checking for encoding issues...")
        
        with self.connect() as conn:
            cur = conn.cursor()
            
            # Check for common encoding corruption patterns
            encoding_patterns = [
                (r'[^\x00-\x7F]+', 'non-ASCII characters'),
                (r'Ã¢|Ã©|Ã¨|Ã |Ã§', 'UTF-8 double encoding'),
                (r'\?{3,}', 'replacement characters'),
                (r'\\x[0-9a-fA-F]{2}', 'hex escape sequences')
            ]
            
            text_columns = [
                ('government_expenditure', ['expenditure_type', 'expenditure_category']),
                ('government_finance_statistics', ['revenue_type', 'tax_category'])
            ]
            
            for table, columns in text_columns:
                for col in columns:
                    for pattern, desc in encoding_patterns:
                        cur.execute(f"""
                            WITH matches AS (
                                SELECT DISTINCT {col}
                                FROM abs_staging.{table}
                                WHERE {col} ~ %s
                                ORDER BY {col}
                                LIMIT 3
                            )
                            SELECT 
                                (SELECT COUNT(*) FROM abs_staging.{table} WHERE {col} ~ %s),
                                array_agg({col}) FROM matches
                        """, (pattern, pattern))
                        
                        count, examples = cur.fetchone()
                        if count > 0 and examples:
                            self.add_issue('WARNING',
                                f"{table}.{col}: Found {count} records with {desc}. Examples: {examples[:2]}")
                                
    def check_referential_integrity(self):
        """Check for orphaned records and broken relationships."""
        logger.info("Checking referential integrity...")
        
        with self.connect() as conn:
            cur = conn.cursor()
            
            # Check if all government levels map to dimension table
            cur.execute("""
                SELECT DISTINCT ge.level_of_government, COUNT(*)
                FROM abs_staging.government_expenditure ge
                LEFT JOIN abs_dimensions.government_level gl 
                    ON ge.level_of_government = gl.level_name
                    OR ge.level_of_government = gl.level_code
                WHERE gl.id IS NULL
                GROUP BY ge.level_of_government
            """)
            
            unmapped_levels = cur.fetchall()
            if unmapped_levels:
                for level, count in unmapped_levels:
                    if level == 'Total':
                        self.add_issue('NOTERROR',
                            f"Government level 'Total' not in dimension table ({count} records) - "
                            "This is expected as 'Total' represents aggregated data across all levels")
                    else:
                        self.add_issue('WARNING',
                            f"Government level '{level}' not found in dimension table ({count} records)")
                            
    def check_record_counts(self):
        """Verify record counts match expectations."""
        logger.info("Checking record counts...")
        
        with self.connect() as conn:
            cur = conn.cursor()
            
            # Get current counts
            cur.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM abs_staging.government_expenditure) as exp_count,
                    (SELECT COUNT(*) FROM abs_staging.government_finance_statistics) as tax_count
            """)
            
            exp_count, tax_count = cur.fetchone()
            self.stats['records_checked'] = exp_count + tax_count
            
            # Check against known values from spider runs
            expected_ranges = {
                'expenditure': (25000, 26000),  # We know we have ~25,380
                'taxation': (2200, 2300)         # We know we have ~2,244
            }
            
            if not expected_ranges['expenditure'][0] <= exp_count <= expected_ranges['expenditure'][1]:
                self.add_issue('WARNING',
                    f"Expenditure record count ({exp_count}) outside expected range {expected_ranges['expenditure']}")
                    
            if not expected_ranges['taxation'][0] <= tax_count <= expected_ranges['taxation'][1]:
                self.add_issue('WARNING',
                    f"Taxation record count ({tax_count}) outside expected range {expected_ranges['taxation']}")
                    
            logger.info(f"Record counts - Expenditure: {exp_count:,}, Taxation: {tax_count:,}")
            
    def add_issue(self, severity: str, message: str):
        """Add an issue to the report."""
        self.issues[severity].append({
            'timestamp': datetime.now().isoformat(),
            'message': message
        })
        self.stats['issues_found'] += 1
        logger.log(getattr(logging, severity if severity != 'NOTERROR' else 'INFO'), message)
        
    def generate_reports(self):
        """Generate both JSON and Markdown reports."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_dir = Path('/home/websinthe/code/econcell/src/econdata/validation/reports')
        
        # JSON report
        json_report = {
            'report_type': 'database_integrity_check',
            'timestamp': datetime.now().isoformat(),
            'stats': self.stats,
            'issues': self.issues
        }
        
        json_path = report_dir / f'integrity_check_{timestamp}.json'
        with open(json_path, 'w') as f:
            json.dump(json_report, f, indent=2)
            
        # Markdown report
        md_content = f"""# Database Integrity Check Report
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Records Checked**: {self.stats['records_checked']:,}
**Issues Found**: {self.stats['issues_found']}

## Summary
- **CRITICAL**: {len(self.issues['CRITICAL'])} issues
- **WARNING**: {len(self.issues['WARNING'])} issues  
- **INFO**: {len(self.issues['INFO'])} issues
- **NOTERROR**: {len(self.issues['NOTERROR'])} issues

## Issues by Severity
"""
        
        for severity in ['CRITICAL', 'WARNING', 'INFO', 'NOTERROR']:
            if self.issues[severity]:
                md_content += f"\n### {severity}\n"
                for issue in self.issues[severity]:
                    md_content += f"- {issue['message']}\n"
                    
        md_path = report_dir / f'integrity_check_{timestamp}.md'
        with open(md_path, 'w') as f:
            f.write(md_content)
            
        return json_path, md_path
        
    def run_all_checks(self):
        """Run all integrity checks."""
        logger.info("Starting database integrity checks...")
        
        try:
            self.check_cross_contamination()
            self.check_data_type_integrity()
            self.check_column_shifts()
            self.check_encoding_issues()
            self.check_referential_integrity()
            self.check_record_counts()
            
            json_path, md_path = self.generate_reports()
            
            logger.info(f"Integrity check complete. Reports saved to:")
            logger.info(f"  JSON: {json_path}")
            logger.info(f"  Markdown: {md_path}")
            
            return self.issues, self.stats
            
        except Exception as e:
            logger.error(f"Error during integrity check: {e}")
            raise


def main():
    """Run the database integrity checker."""
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv('/home/websinthe/code/econcell/.env')
    
    db_config = {
        'host': os.getenv('PSQL_HOST', 'localhost'),
        'port': os.getenv('PSQL_PORT', '5432'),
        'database': os.getenv('PSQL_DB', 'econdata'),
        'user': os.getenv('PSQL_USER', 'websinthe'),
        'password': os.getenv('PSQL_PW', '')
    }
    
    checker = DatabaseIntegrityChecker(db_config)
    issues, stats = checker.run_all_checks()
    
    # Exit with error code if critical issues found
    if issues['CRITICAL']:
        return 1
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
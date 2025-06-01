#!/usr/bin/env python3
"""
Taxation ETL Validation Script
Pre-validates taxation data before ETL to facts table.

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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TaxationETLValidator:
    """Validates taxation data readiness for ETL processing."""
    
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.validation_results = {
            'pre_checks': {},
            'mapping_validation': {},
            'data_quality': {},
            'constraint_checks': {}
        }
        self.issues = []
        self.stats = {
            'total_records': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'validation_passed': True
        }
        
    def connect(self):
        """Establish database connection."""
        return psycopg2.connect(**self.db_config)
    
    def validate_tax_category_mappings(self):
        """Verify all tax categories can be mapped."""
        logger.info("Validating tax category mappings...")
        
        with self.connect() as conn:
            cur = conn.cursor()
            
            # Get all unique tax categories
            cur.execute("""
                SELECT DISTINCT tax_category, COUNT(*) as record_count
                FROM abs_staging.government_finance_statistics
                WHERE tax_category IS NOT NULL
                GROUP BY tax_category
                ORDER BY tax_category
            """)
            
            categories = cur.fetchall()
            self.validation_results['mapping_validation']['tax_categories'] = {
                'total_categories': len(categories),
                'categories': {cat: count for cat, count in categories}
            }
            
            # Accept both 'Taxation revenue' and 'Other Tax' as valid
            valid_categories = ['Taxation revenue', 'Other Tax']
            all_valid = all(cat[0] in valid_categories for cat in categories)
            
            if all_valid:
                logger.info(f"✓ Tax category mapping valid: {sum(count for _, count in categories)} records")
            else:
                invalid_cats = [cat for cat in categories if cat[0] not in valid_categories]
                self.issues.append({
                    'severity': 'WARNING',
                    'message': f"Unexpected tax categories found: {invalid_cats}"
                })
                
    def validate_amount_transformations(self):
        """Ensure no precision loss during ETL."""
        logger.info("Validating amount precision...")
        
        with self.connect() as conn:
            # Check amount statistics
            df = pd.read_sql("""
                SELECT amount,
                       amount::text as amount_text,
                       LENGTH(SPLIT_PART(amount::text, '.', 2)) as decimal_places
                FROM abs_staging.government_finance_statistics
                WHERE amount IS NOT NULL
            """, conn)
            
            # Validate decimal precision
            if df['decimal_places'].max() > 2:
                self.issues.append({
                    'severity': 'WARNING',
                    'message': f"Found amounts with >2 decimal places: max={df['decimal_places'].max()}"
                })
                
            # Check for negative amounts
            negative_count = (df['amount'] < 0).sum()
            if negative_count > 0:
                self.issues.append({
                    'severity': 'ERROR',
                    'message': f"Found {negative_count} negative amounts"
                })
                self.stats['validation_passed'] = False
                
            self.validation_results['data_quality']['amount_stats'] = {
                'min': float(df['amount'].min()),
                'max': float(df['amount'].max()),
                'mean': float(df['amount'].mean()),
                'total': float(df['amount'].sum()),
                'negative_count': int(negative_count)
            }
            
    def validate_date_dimension_joins(self):
        """Validate all dates map to date dimension."""
        logger.info("Validating date dimension mappings...")
        
        with self.connect() as conn:
            cur = conn.cursor()
            
            # Check if all dates exist in time dimension
            cur.execute("""
                WITH tax_dates AS (
                    SELECT DISTINCT reference_period
                    FROM abs_staging.government_finance_statistics
                ),
                missing_dates AS (
                    SELECT td.reference_period
                    FROM tax_dates td
                    LEFT JOIN rba_dimensions.dim_time dt 
                        ON td.reference_period = dt.date_value
                    WHERE dt.time_key IS NULL
                )
                SELECT COUNT(*) as missing_count,
                       array_agg(reference_period ORDER BY reference_period) as missing_dates
                FROM missing_dates
            """)
            
            missing_count, missing_dates = cur.fetchone()
            
            if missing_count > 0:
                self.issues.append({
                    'severity': 'ERROR',
                    'message': f"Missing {missing_count} dates in time dimension: {missing_dates[:5]}..."
                })
                self.stats['validation_passed'] = False
            else:
                logger.info("✓ All dates mapped to time dimension")
                
            self.validation_results['mapping_validation']['date_mappings'] = {
                'missing_count': missing_count,
                'sample_missing': missing_dates[:5] if missing_dates else []
            }
            
    def validate_government_level_resolution(self):
        """Check for unmapped government entities."""
        logger.info("Validating government level mappings...")
        
        with self.connect() as conn:
            cur = conn.cursor()
            
            # Check government level mappings
            cur.execute("""
                SELECT gfs.level_of_government, COUNT(*) as record_count
                FROM abs_staging.government_finance_statistics gfs
                LEFT JOIN abs_dimensions.government_level gl 
                    ON gfs.level_of_government = gl.level_name
                WHERE gl.id IS NULL
                  AND gfs.level_of_government != 'Total'
                GROUP BY gfs.level_of_government
            """)
            
            unmapped = cur.fetchall()
            
            if unmapped:
                for gov_level, count in unmapped:
                    self.issues.append({
                        'severity': 'ERROR',
                        'message': f"Unmapped government level: '{gov_level}' ({count} records)"
                    })
                self.stats['validation_passed'] = False
            else:
                logger.info("✓ All government levels mapped")
                
            self.validation_results['mapping_validation']['government_levels'] = {
                'unmapped_count': len(unmapped),
                'unmapped_levels': {level: count for level, count in unmapped}
            }
            
    def check_duplicate_prevention(self):
        """Prevent double-loading of records."""
        logger.info("Checking for potential duplicates...")
        
        with self.connect() as conn:
            cur = conn.cursor()
            
            # Check for duplicates in staging
            cur.execute("""
                WITH duplicate_check AS (
                    SELECT level_of_government, reference_period, 
                           COUNT(*) as record_count,
                           SUM(amount) as total_amount
                    FROM abs_staging.government_finance_statistics
                    GROUP BY level_of_government, reference_period
                    HAVING COUNT(*) > 1
                )
                SELECT COUNT(*) as duplicate_groups,
                       SUM(record_count) as total_duplicate_records
                FROM duplicate_check
            """)
            
            dup_groups, dup_records = cur.fetchone()
            
            # Note: Multiple records per government level per date is expected
            # as we have quarterly interpolations from annual data
            if dup_groups and dup_groups > 0:
                # Only warn if we have more than 4 records per group (quarterly)
                cur.execute("""
                    SELECT MAX(record_count) as max_per_group
                    FROM (
                        SELECT COUNT(*) as record_count
                        FROM abs_staging.government_finance_statistics
                        GROUP BY level_of_government, reference_period
                    ) counts
                """)
                max_per_group = cur.fetchone()[0]
                
                if max_per_group > 4:
                    self.issues.append({
                        'severity': 'WARNING',
                        'message': f"Found {dup_groups} groups with multiple records (max {max_per_group} per group)"
                    })
                else:
                    logger.info(f"✓ Expected duplicates for quarterly data: {dup_groups} groups")
                
            # Check if data already exists in facts
            cur.execute("""
                SELECT COUNT(*) as existing_count,
                       MIN(dt.date_value) as min_date,
                       MAX(dt.date_value) as max_date
                FROM rba_facts.fact_circular_flow fcf
                JOIN rba_dimensions.dim_time dt ON fcf.time_key = dt.time_key
                WHERE fcf.component_key = 6  -- Taxation component
                  AND fcf.source_key IN (
                      SELECT source_key 
                      FROM rba_dimensions.dim_data_source 
                      WHERE data_provider = 'ABS' OR rba_table_code = 'ABS'
                  )
            """)
            
            existing_count, min_date, max_date = cur.fetchone()
            
            if existing_count and existing_count > 0:
                self.issues.append({
                    'severity': 'WARNING',
                    'message': f"Found {existing_count} existing taxation records in facts ({min_date} to {max_date})"
                })
                
            self.validation_results['data_quality']['duplicates'] = {
                'staging_duplicates': {'groups': dup_groups or 0, 'records': dup_records or 0},
                'existing_facts': {'count': existing_count or 0, 'date_range': f"{min_date} to {max_date}" if existing_count else None}
            }
            
    def validate_foreign_key_constraints(self):
        """Pre-validate all foreign key references."""
        logger.info("Validating foreign key constraints...")
        
        with self.connect() as conn:
            cur = conn.cursor()
            
            # Check if ABS source exists
            cur.execute("""
                SELECT source_key, rba_table_code, data_provider, table_description
                FROM rba_dimensions.dim_data_source
                WHERE data_provider = 'ABS' OR rba_table_code = 'ABS'
            """)
            
            source_result = cur.fetchone()
            if not source_result:
                self.issues.append({
                    'severity': 'ERROR',
                    'message': "ABS data source not found in dim_data_source - needs to be created"
                })
                self.stats['validation_passed'] = False
                self.validation_results['constraint_checks']['abs_source'] = None
            else:
                self.validation_results['constraint_checks']['abs_source'] = {
                    'source_key': source_result[0],
                    'rba_table_code': source_result[1],
                    'data_provider': source_result[2],
                    'table_description': source_result[3]
                }
                
            # Check if measurement types exist
            cur.execute("""
                SELECT measurement_key, unit_type, unit_description
                FROM rba_dimensions.dim_measurement
                WHERE unit_type IN ('$m', 'Millions')
                   OR unit_description ILIKE '%million%'
            """)
            
            measurements = cur.fetchall()
            self.validation_results['constraint_checks']['measurements'] = {
                m[1]: {'key': m[0], 'description': m[2]} for m in measurements
            }
            
            if len(measurements) < 1:
                self.issues.append({
                    'severity': 'ERROR',
                    'message': "Required measurement types not found (need millions unit)"
                })
                self.stats['validation_passed'] = False
                
    def validate_data_completeness(self):
        """Check overall data completeness."""
        logger.info("Validating data completeness...")
        
        with self.connect() as conn:
            cur = conn.cursor()
            
            # Get record statistics
            cur.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT level_of_government) as gov_levels,
                    COUNT(DISTINCT reference_period) as time_periods,
                    MIN(reference_period) as min_date,
                    MAX(reference_period) as max_date,
                    SUM(amount) as total_amount
                FROM abs_staging.government_finance_statistics
            """)
            
            stats = cur.fetchone()
            self.stats['total_records'] = stats[0]
            
            self.validation_results['data_quality']['completeness'] = {
                'total_records': stats[0],
                'government_levels': stats[1],
                'time_periods': stats[2],
                'date_range': f"{stats[3]} to {stats[4]}",
                'total_amount': float(stats[5]) if stats[5] else 0
            }
            
            # Check for null values in critical fields
            cur.execute("""
                SELECT 
                    SUM(CASE WHEN amount IS NULL THEN 1 ELSE 0 END) as null_amounts,
                    SUM(CASE WHEN reference_period IS NULL THEN 1 ELSE 0 END) as null_dates,
                    SUM(CASE WHEN level_of_government IS NULL THEN 1 ELSE 0 END) as null_gov_levels
                FROM abs_staging.government_finance_statistics
            """)
            
            nulls = cur.fetchone()
            if any(nulls):
                self.issues.append({
                    'severity': 'ERROR',
                    'message': f"Found null values: amounts={nulls[0]}, dates={nulls[1]}, gov_levels={nulls[2]}"
                })
                self.stats['validation_passed'] = False
                
    def generate_etl_readiness_report(self):
        """Generate comprehensive ETL readiness report."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_dir = Path('/home/websinthe/code/econcell/src/econdata/validation/reports')
        
        # Calculate valid records
        self.stats['valid_records'] = self.stats['total_records'] if self.stats['validation_passed'] else 0
        self.stats['invalid_records'] = self.stats['total_records'] - self.stats['valid_records']
        
        # JSON report
        json_report = {
            'report_type': 'taxation_etl_validation',
            'timestamp': datetime.now().isoformat(),
            'stats': self.stats,
            'validation_results': self.validation_results,
            'issues': self.issues,
            'etl_ready': self.stats['validation_passed']
        }
        
        json_path = report_dir / f'taxation_etl_validation_{timestamp}.json'
        with open(json_path, 'w') as f:
            json.dump(json_report, f, indent=2, default=str)
            
        # Markdown report
        md_content = f"""# Taxation ETL Validation Report
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Records**: {self.stats['total_records']:,}
**Valid Records**: {self.stats['valid_records']:,}
**ETL Ready**: {'✅ YES' if self.stats['validation_passed'] else '❌ NO'}

## Validation Summary

### Data Quality
- **Total Amount**: ${self.validation_results['data_quality']['completeness']['total_amount']:,.2f}
- **Date Range**: {self.validation_results['data_quality']['completeness']['date_range']}
- **Government Levels**: {self.validation_results['data_quality']['completeness']['government_levels']}
- **Time Periods**: {self.validation_results['data_quality']['completeness']['time_periods']}

### Issues Found
"""
        
        if self.issues:
            # Group issues by severity
            by_severity = {}
            for issue in self.issues:
                sev = issue['severity']
                if sev not in by_severity:
                    by_severity[sev] = []
                by_severity[sev].append(issue['message'])
                
            for severity in ['ERROR', 'WARNING', 'INFO']:
                if severity in by_severity:
                    md_content += f"\n#### {severity} ({len(by_severity[severity])})\n"
                    for msg in by_severity[severity]:
                        md_content += f"- {msg}\n"
        else:
            md_content += "\n✅ No issues found - data is ready for ETL!\n"
            
        md_content += f"""
## Next Steps
"""
        
        if self.stats['validation_passed']:
            md_content += """
1. Run the taxation ETL procedure
2. Verify records in fact_circular_flow table
3. Update circular flow analytics views
4. Test T component calculations
"""
        else:
            md_content += """
1. Fix all ERROR level issues
2. Review WARNING level issues
3. Re-run validation
4. Proceed with ETL once validation passes
"""
        
        md_path = report_dir / f'taxation_etl_validation_{timestamp}.md'
        with open(md_path, 'w') as f:
            f.write(md_content)
            
        return json_path, md_path
        
    def run_all_validations(self):
        """Run all validation checks."""
        logger.info("Starting taxation ETL validation...")
        
        try:
            self.validate_tax_category_mappings()
            self.validate_amount_transformations()
            self.validate_date_dimension_joins()
            self.validate_government_level_resolution()
            self.check_duplicate_prevention()
            self.validate_foreign_key_constraints()
            self.validate_data_completeness()
            
            json_path, md_path = self.generate_etl_readiness_report()
            
            logger.info(f"Taxation ETL validation complete. Reports saved to:")
            logger.info(f"  JSON: {json_path}")
            logger.info(f"  Markdown: {md_path}")
            
            if self.stats['validation_passed']:
                logger.info("✅ VALIDATION PASSED - Ready for ETL")
            else:
                logger.warning("❌ VALIDATION FAILED - Fix issues before proceeding")
                
            return self.stats['validation_passed']
            
        except Exception as e:
            logger.error(f"Error during validation: {e}")
            raise


def main():
    """Run the taxation ETL validator."""
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
    
    validator = TaxationETLValidator(db_config)
    validation_passed = validator.run_all_validations()
    
    # Exit with appropriate code
    return 0 if validation_passed else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
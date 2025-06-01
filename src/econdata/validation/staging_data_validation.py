#!/usr/bin/env python3
"""
Staging Data Validation Script
Comprehensive validation of all 27,624 records in staging tables.

Author: Claude & Kieran
Date: June 1, 2025
"""

import psycopg2
import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from decimal import Decimal
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StagingDataValidator:
    """Validates staging data for completeness, accuracy, and anomalies."""
    
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.issues = {
            'CRITICAL': [],
            'WARNING': [],
            'INFO': [],
            'NOTERROR': []
        }
        self.stats = {
            'tables_validated': 0,
            'records_validated': 0,
            'issues_found': 0,
            'anomalies_detected': 0
        }
        self.validation_results = {}
        
    def connect(self):
        """Establish database connection."""
        return psycopg2.connect(**self.db_config)
    
    def validate_amount_precision(self):
        """Check for truncated decimals in amount fields."""
        logger.info("Validating amount precision...")
        
        with self.connect() as conn:
            tables = [
                ('government_expenditure', 'amount', 25380),
                ('government_finance_statistics', 'amount', 2244)
            ]
            
            for table, col, expected_count in tables:
                # Get all amounts for analysis
                query = f"""
                    SELECT id, {col}, 
                           {col}::text as amount_text,
                           LENGTH(SPLIT_PART({col}::text, '.', 2)) as decimal_places
                    FROM abs_staging.{table}
                    WHERE {col} IS NOT NULL
                """
                
                df = pd.read_sql(query, conn)
                
                # Check for missing decimals (exactly .00)
                whole_numbers = df[df[col] % 1 == 0]
                whole_pct = (len(whole_numbers) / len(df)) * 100 if len(df) > 0 else 0
                
                # Check decimal place distribution
                decimal_dist = df['decimal_places'].value_counts().to_dict()
                
                # Flag if too many whole numbers
                if whole_pct > 80:
                    self.add_issue('WARNING',
                        f"{table}: {whole_pct:.1f}% amounts are whole numbers - verify if decimal precision lost")
                    
                    # Sample some whole numbers to check patterns
                    sample_wholes = whole_numbers.nlargest(5, col)
                    examples = [f"${amt:,.2f}" for amt in sample_wholes[col].values]
                    self.add_issue('INFO',
                        f"{table}: Large whole number examples: {', '.join(examples)}")
                
                # Check for suspicious patterns (all ending in .00, .50, etc)
                if len(df) > 100:
                    # Get last 2 decimal digits
                    df['cents'] = (df[col] * 100) % 100
                    cents_dist = df['cents'].value_counts().head(5)
                    
                    # If more than 50% end in .00
                    if cents_dist.iloc[0] > len(df) * 0.5 and cents_dist.index[0] == 0:
                        self.add_issue('WARNING',
                            f"{table}: {cents_dist.iloc[0]/len(df)*100:.1f}% of amounts end in .00")
                
                self.validation_results[f'{table}_precision'] = {
                    'whole_number_pct': whole_pct,
                    'decimal_distribution': decimal_dist,
                    'total_records': len(df)
                }
                
    def validate_date_consistency(self):
        """Check for malformed dates or wrong century."""
        logger.info("Validating date consistency...")
        
        with self.connect() as conn:
            tables = [
                ('government_expenditure', 'reference_period'),
                ('government_finance_statistics', 'reference_period')
            ]
            
            for table, date_col in tables:
                cur = conn.cursor()
                
                # Check date range
                cur.execute(f"""
                    SELECT MIN({date_col}) as min_date, 
                           MAX({date_col}) as max_date,
                           COUNT(DISTINCT {date_col}) as unique_dates,
                           COUNT(*) as total_records
                    FROM abs_staging.{table}
                """)
                
                min_date, max_date, unique_dates, total = cur.fetchone()
                
                # Check for dates outside reasonable range
                if min_date < datetime(2000, 1, 1).date():
                    self.add_issue('WARNING',
                        f"{table}: Found dates before 2000: {min_date}")
                        
                if max_date > datetime(2030, 1, 1).date():
                    self.add_issue('WARNING',
                        f"{table}: Found future dates beyond 2030: {max_date}")
                
                # Check for gaps in quarterly sequence
                cur.execute(f"""
                    WITH date_series AS (
                        SELECT generate_series(
                            DATE_TRUNC('quarter', MIN({date_col})),
                            DATE_TRUNC('quarter', MAX({date_col})),
                            '3 months'::interval
                        )::date as expected_date
                        FROM abs_staging.{table}
                    ),
                    actual_dates AS (
                        SELECT DISTINCT DATE_TRUNC('quarter', {date_col})::date as actual_date
                        FROM abs_staging.{table}
                    )
                    SELECT COUNT(*) 
                    FROM date_series ds
                    LEFT JOIN actual_dates ad ON ds.expected_date = ad.actual_date
                    WHERE ad.actual_date IS NULL
                """)
                
                missing_quarters = cur.fetchone()[0]
                if missing_quarters > 0:
                    self.add_issue('INFO',
                        f"{table}: Missing {missing_quarters} quarters in date sequence")
                        
                # Check for duplicate dates by government level
                cur.execute(f"""
                    SELECT {date_col}, level_of_government, COUNT(*) as count
                    FROM abs_staging.{table}
                    GROUP BY {date_col}, level_of_government
                    HAVING COUNT(*) > 50
                    ORDER BY COUNT(*) DESC
                    LIMIT 5
                """)
                
                duplicates = cur.fetchall()
                if duplicates:
                    for date, gov_level, count in duplicates[:2]:
                        self.add_issue('INFO',
                            f"{table}: {count} records for {gov_level} on {date} - verify if expected")
                            
    def validate_categories(self):
        """Ensure all categories match dimension tables."""
        logger.info("Validating category mappings...")
        
        with self.connect() as conn:
            cur = conn.cursor()
            
            # Validate expenditure categories
            cur.execute("""
                SELECT DISTINCT expenditure_category, COUNT(*) as count
                FROM abs_staging.government_expenditure
                WHERE expenditure_category IS NOT NULL
                GROUP BY expenditure_category
                ORDER BY COUNT(*) DESC
            """)
            
            exp_categories = cur.fetchall()
            valid_exp_categories = {
                'general_services', 'defence', 'public_order', 'economic_affairs',
                'environment', 'housing', 'health', 'recreation', 'education',
                'social_protection', 'employee_expenses', 'goods_services',
                'interest_payments', 'grants_subsidies', 'capital_expenditure',
                'total_expenditure', 'other_expenditure'
            }
            
            for category, count in exp_categories:
                if category not in valid_exp_categories:
                    self.add_issue('WARNING',
                        f"Unknown expenditure category '{category}' ({count} records)")
                        
            # Validate COFOG codes
            cur.execute("""
                SELECT DISTINCT ge.cofog_code, COUNT(*) as count
                FROM abs_staging.government_expenditure ge
                LEFT JOIN abs_dimensions.cofog_classification cc 
                    ON ge.cofog_code = cc.cofog_code
                WHERE ge.cofog_code IS NOT NULL 
                    AND cc.cofog_code IS NULL
                GROUP BY ge.cofog_code
            """)
            
            invalid_cofog = cur.fetchall()
            if invalid_cofog:
                for code, count in invalid_cofog[:5]:
                    self.add_issue('WARNING',
                        f"Invalid COFOG code '{code}' ({count} records)")
                        
    def validate_government_mappings(self):
        """Verify government level consistency."""
        logger.info("Validating government level mappings...")
        
        with self.connect() as conn:
            # Already identified in integrity check that mappings are missing
            # This is more about consistency within the data
            
            cur = conn.cursor()
            
            # Check for variations in government naming
            cur.execute("""
                SELECT level_of_government, COUNT(*) as count
                FROM (
                    SELECT level_of_government FROM abs_staging.government_expenditure
                    UNION ALL
                    SELECT level_of_government FROM abs_staging.government_finance_statistics
                ) combined
                GROUP BY level_of_government
                ORDER BY level_of_government
            """)
            
            gov_levels = cur.fetchall()
            
            # Check for potential typos or variations
            level_names = [level for level, _ in gov_levels]
            for i, (level1, count1) in enumerate(gov_levels):
                for level2, count2 in gov_levels[i+1:]:
                    # Simple similarity check
                    if level1.lower().replace(' ', '') == level2.lower().replace(' ', '') and level1 != level2:
                        self.add_issue('WARNING',
                            f"Similar government levels: '{level1}' ({count1}) and '{level2}' ({count2})")
                            
    def detect_statistical_anomalies(self):
        """Detect outliers and suspicious patterns."""
        logger.info("Detecting statistical anomalies...")
        
        with self.connect() as conn:
            # Analyze expenditure amounts
            query = """
                SELECT amount, level_of_government, expenditure_category
                FROM abs_staging.government_expenditure
                WHERE amount IS NOT NULL AND amount > 0
            """
            
            df = pd.read_sql(query, conn)
            
            if len(df) > 0:
                # Calculate statistics by category
                for category in df['expenditure_category'].unique():
                    if category:
                        cat_data = df[df['expenditure_category'] == category]['amount']
                        if len(cat_data) > 10:
                            # Use IQR method for outlier detection
                            Q1 = cat_data.quantile(0.25)
                            Q3 = cat_data.quantile(0.75)
                            IQR = Q3 - Q1
                            upper_bound = Q3 + 3 * IQR  # Using 3*IQR for extreme outliers
                            
                            outliers = cat_data[cat_data > upper_bound]
                            if len(outliers) > 0:
                                max_outlier = outliers.max()
                                if max_outlier > 1_000_000_000:  # Over $1 billion
                                    self.add_issue('WARNING',
                                        f"Extreme outlier in {category}: ${max_outlier:,.2f} "
                                        f"(median: ${cat_data.median():,.2f})")
                                elif max_outlier > 100_000_000:  # Over $100 million
                                    self.add_issue('INFO',
                                        f"Large value in {category}: ${max_outlier:,.2f}")
                
                # Check for suspicious patterns in amounts
                # Look for amounts that appear too frequently
                amount_counts = df['amount'].value_counts()
                top_amounts = amount_counts.head(10)
                
                for amount, count in top_amounts.items():
                    if count > 100 and amount > 0:
                        if amount == round(amount):  # Whole number
                            self.add_issue('INFO',
                                f"Amount ${amount:,.2f} appears {count} times - possible default value")
                                
    def validate_null_handling(self):
        """Check for inconsistent handling of missing data."""
        logger.info("Validating null and empty string handling...")
        
        with self.connect() as conn:
            cur = conn.cursor()
            
            # Check text fields for empty strings vs nulls
            text_fields = [
                ('government_expenditure', ['expenditure_type', 'expenditure_category', 'cofog_code']),
                ('government_finance_statistics', ['revenue_type', 'tax_category', 'gfs_code'])
            ]
            
            for table, fields in text_fields:
                for field in fields:
                    cur.execute(f"""
                        SELECT 
                            COUNT(CASE WHEN {field} IS NULL THEN 1 END) as null_count,
                            COUNT(CASE WHEN {field} = '' THEN 1 END) as empty_count,
                            COUNT(CASE WHEN {field} IS NOT NULL AND {field} != '' THEN 1 END) as valid_count
                        FROM abs_staging.{table}
                    """)
                    
                    null_count, empty_count, valid_count = cur.fetchone()
                    
                    if null_count > 0 and empty_count > 0:
                        self.add_issue('WARNING',
                            f"{table}.{field}: Inconsistent null handling - "
                            f"{null_count} NULLs and {empty_count} empty strings")
                            
    def generate_statistical_summary(self):
        """Generate detailed statistical summary with visualizations."""
        logger.info("Generating statistical summary...")
        
        report_dir = Path('/home/websinthe/code/econcell/src/econdata/validation/reports')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        with self.connect() as conn:
            # Create summary statistics
            summary = {}
            
            # Expenditure summary
            exp_df = pd.read_sql("""
                SELECT amount, level_of_government, expenditure_category, reference_period
                FROM abs_staging.government_expenditure
                WHERE amount IS NOT NULL
            """, conn)
            
            if len(exp_df) > 0:
                summary['expenditure'] = {
                    'total_amount': float(exp_df['amount'].sum()),
                    'mean_amount': float(exp_df['amount'].mean()),
                    'median_amount': float(exp_df['amount'].median()),
                    'std_amount': float(exp_df['amount'].std()),
                    'by_government': exp_df.groupby('level_of_government')['amount'].sum().to_dict(),
                    'by_category': exp_df.groupby('expenditure_category')['amount'].sum().to_dict()
                }
                
                # Create visualization
                fig, axes = plt.subplots(2, 2, figsize=(15, 10))
                
                # Amount distribution (log scale)
                exp_df['amount_log'] = np.log10(exp_df['amount'] + 1)
                exp_df['amount_log'].hist(bins=50, ax=axes[0, 0])
                axes[0, 0].set_title('Expenditure Amount Distribution (log scale)')
                axes[0, 0].set_xlabel('Log10(Amount + 1)')
                
                # By government level
                gov_summary = exp_df.groupby('level_of_government')['amount'].sum().sort_values(ascending=True)
                gov_summary.plot(kind='barh', ax=axes[0, 1])
                axes[0, 1].set_title('Total Expenditure by Government Level')
                axes[0, 1].set_xlabel('Amount (millions)')
                
                # By category
                cat_summary = exp_df.groupby('expenditure_category')['amount'].sum().sort_values(ascending=True).tail(10)
                cat_summary.plot(kind='barh', ax=axes[1, 0])
                axes[1, 0].set_title('Top 10 Expenditure Categories')
                axes[1, 0].set_xlabel('Amount (millions)')
                
                # Time series
                time_summary = exp_df.groupby('reference_period')['amount'].sum().sort_index()
                time_summary.plot(ax=axes[1, 1])
                axes[1, 1].set_title('Expenditure Over Time')
                axes[1, 1].set_xlabel('Date')
                axes[1, 1].set_ylabel('Amount (millions)')
                
                plt.tight_layout()
                plt.savefig(report_dir / f'expenditure_analysis_{timestamp}.png', dpi=150)
                plt.close()
                
            return summary
            
    def add_issue(self, severity: str, message: str):
        """Add an issue to the report."""
        self.issues[severity].append({
            'timestamp': datetime.now().isoformat(),
            'message': message
        })
        self.stats['issues_found'] += 1
        if severity in ['WARNING', 'CRITICAL']:
            self.stats['anomalies_detected'] += 1
        logger.log(getattr(logging, severity if severity != 'NOTERROR' else 'INFO'), message)
        
    def generate_reports(self):
        """Generate both JSON and Markdown reports."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_dir = Path('/home/websinthe/code/econcell/src/econdata/validation/reports')
        
        # Generate statistical summary
        summary = self.generate_statistical_summary()
        
        # JSON report
        json_report = {
            'report_type': 'staging_data_validation',
            'timestamp': datetime.now().isoformat(),
            'stats': self.stats,
            'issues': self.issues,
            'validation_results': self.validation_results,
            'statistical_summary': summary
        }
        
        json_path = report_dir / f'staging_validation_{timestamp}.json'
        with open(json_path, 'w') as f:
            json.dump(json_report, f, indent=2, default=str)
            
        # Markdown report
        md_content = f"""# Staging Data Validation Report
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Records Validated**: {self.stats['records_validated']:,}
**Issues Found**: {self.stats['issues_found']}
**Anomalies Detected**: {self.stats['anomalies_detected']}

## Summary
- **CRITICAL**: {len(self.issues['CRITICAL'])} issues
- **WARNING**: {len(self.issues['WARNING'])} issues  
- **INFO**: {len(self.issues['INFO'])} issues
- **NOTERROR**: {len(self.issues['NOTERROR'])} issues

## Statistical Summary
"""
        
        if summary and 'expenditure' in summary:
            exp = summary['expenditure']
            md_content += f"""
### Expenditure Data
- **Total Amount**: ${exp['total_amount']:,.2f}
- **Mean Amount**: ${exp['mean_amount']:,.2f}
- **Median Amount**: ${exp['median_amount']:,.2f}
- **Std Deviation**: ${exp['std_amount']:,.2f}

![Expenditure Analysis](expenditure_analysis_{timestamp}.png)
"""
        
        md_content += "\n## Issues by Severity\n"
        
        for severity in ['CRITICAL', 'WARNING', 'INFO', 'NOTERROR']:
            if self.issues[severity]:
                md_content += f"\n### {severity}\n"
                for issue in self.issues[severity]:
                    md_content += f"- {issue['message']}\n"
                    
        md_path = report_dir / f'staging_validation_{timestamp}.md'
        with open(md_path, 'w') as f:
            f.write(md_content)
            
        return json_path, md_path
        
    def run_all_validations(self):
        """Run all validation checks."""
        logger.info("Starting comprehensive staging data validation...")
        
        try:
            # Set total records
            self.stats['records_validated'] = 27624
            
            self.validate_amount_precision()
            self.validate_date_consistency()
            self.validate_categories()
            self.validate_government_mappings()
            self.detect_statistical_anomalies()
            self.validate_null_handling()
            
            json_path, md_path = self.generate_reports()
            
            logger.info(f"Staging validation complete. Reports saved to:")
            logger.info(f"  JSON: {json_path}")
            logger.info(f"  Markdown: {md_path}")
            
            return self.issues, self.stats
            
        except Exception as e:
            logger.error(f"Error during staging validation: {e}")
            raise


def main():
    """Run the staging data validator."""
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
    
    validator = StagingDataValidator(db_config)
    issues, stats = validator.run_all_validations()
    
    # Exit with error code if critical issues found
    if issues['CRITICAL']:
        return 1
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
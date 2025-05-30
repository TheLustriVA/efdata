#!/usr/bin/env python3
"""
Create test fixtures for ABS spider testing.

This script creates small Excel files that mimic ABS GFS structure
for testing without downloading large files.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Create fixtures directory
fixtures_dir = Path(__file__).parent / 'fixtures' / 'abs'
fixtures_dir.mkdir(parents=True, exist_ok=True)

def create_sample_gfs_data():
    """Create a sample GFS dataset."""
    # Generate sample data
    periods = pd.date_range('2022-07-01', '2024-06-30', freq='YS-JUL')
    
    data = []
    tax_types = [
        ('Income taxes - individuals', 'income_tax', 150000),
        ('Income taxes - companies', 'income_tax', 80000),
        ('Goods and services tax', 'gst', 70000),
        ('Excise and customs duties', 'excise', 25000),
        ('Payroll tax', 'payroll', 15000),
        ('Land tax', 'property', 8000),
        ('Stamp duties', 'property', 12000),
    ]
    
    gov_levels = ['Commonwealth', 'State', 'Local', 'Total']
    
    for period in periods:
        for tax_name, category, base_amount in tax_types:
            for gov_level in gov_levels:
                # Add some variation
                amount = base_amount * (1 + np.random.normal(0, 0.1))
                
                # Adjust by government level
                if gov_level == 'Commonwealth':
                    if category in ['income_tax', 'gst', 'excise']:
                        amount *= 1.0
                    else:
                        amount *= 0.1
                elif gov_level == 'State':
                    if category in ['payroll', 'property']:
                        amount *= 0.8
                    else:
                        amount *= 0.2
                elif gov_level == 'Local':
                    amount *= 0.05
                
                data.append({
                    'Period': period.strftime('%Y-%m-%d'),
                    'Revenue Type': tax_name,
                    'Government Level': gov_level,
                    'Amount ($ millions)': round(amount, 2),
                    'Notes': 'Test data'
                })
    
    return pd.DataFrame(data)

def create_test_excel_files():
    """Create various test Excel files."""
    
    # 1. Valid GFS file
    print("Creating valid_gfs_sample.xlsx...")
    df = create_sample_gfs_data()
    
    # Create Excel with multiple sheets (mimicking ABS structure)
    with pd.ExcelWriter(fixtures_dir / 'valid_gfs_sample.xlsx') as writer:
        # Summary sheet
        df_summary = df.groupby(['Period', 'Government Level'])['Amount ($ millions)'].sum().reset_index()
        df_summary.to_excel(writer, sheet_name='Summary', index=False)
        
        # Detailed data
        df.to_excel(writer, sheet_name='Table 1', index=False)
        
        # Metadata sheet
        metadata = pd.DataFrame({
            'Item': ['Publication', 'Reference Period', 'Release Date', 'Next Release'],
            'Value': ['Government Finance Statistics', '2022-23 to 2023-24', '2024-04-30', '2024-10-31']
        })
        metadata.to_excel(writer, sheet_name='Metadata', index=False)
    
    # 2. File with challenging headers
    print("Creating complex_headers.xlsx...")
    df_complex = df.copy()
    
    with pd.ExcelWriter(fixtures_dir / 'complex_headers.xlsx') as writer:
        # Add empty rows at top (common in ABS files)
        empty_df = pd.DataFrame([[None] * len(df_complex.columns)] * 5)
        empty_df.columns = df_complex.columns
        pd.concat([empty_df, df_complex]).to_excel(writer, sheet_name='Data', index=False, header=False)
    
    # 3. Small file for quick tests
    print("Creating minimal_test.xlsx...")
    df_minimal = df[df['Government Level'] == 'Commonwealth'].head(20)
    df_minimal.to_excel(fixtures_dir / 'minimal_test.xlsx', index=False)
    
    # 4. Create a CSV version for even simpler tests
    print("Creating test_data.csv...")
    df.to_csv(fixtures_dir / 'test_data.csv', index=False)
    
    print(f"\nTest fixtures created in: {fixtures_dir}")
    print(f"Total files: {len(list(fixtures_dir.glob('*')))}")

if __name__ == '__main__':
    create_test_excel_files()
    print("\nTest fixtures ready for use!")
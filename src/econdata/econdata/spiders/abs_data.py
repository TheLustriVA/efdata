"""
Australian Bureau of Statistics (ABS) Government Finance Statistics Spider

This spider collects taxation revenue data (T component) from ABS GFS publications.
Primary source: Catalogue 5512.0 - Government Finance Statistics

Key considerations:
- XLSX file format (not CSV like RBA)
- Large file sizes (10-50MB typical)
- Annual data requiring quarterly interpolation
- Complex multi-sheet workbooks
- Headers with merged cells and footnotes
"""

import scrapy
from pathlib import Path
import os
import pandas as pd
import numpy as np
from datetime import datetime
import json
import hashlib
from typing import Dict, List, Optional, Tuple
import logging
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class ABSGFSSpider(scrapy.Spider):
    """
    Spider for collecting Government Finance Statistics from ABS.
    
    This spider handles:
    1. Downloading large XLSX files with retry logic
    2. Parsing complex multi-sheet workbooks
    3. Extracting taxation revenue by type and level of government
    4. Converting annual data to quarterly estimates
    """
    
    name = 'abs_gfs'
    
    # ABS GFS publication URLs
    start_urls = [
        # Latest GFS annual release page with XLSX files
        'https://www.abs.gov.au/statistics/economy/government/government-finance-statistics-annual/latest-release',
    ]
    
    # Custom settings for handling large files
    custom_settings = {
        'DOWNLOAD_TIMEOUT': 300,  # 5 minutes for large XLSX files
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429],
        'CONCURRENT_REQUESTS': 2,  # Be gentle with ABS servers
        'DOWNLOAD_DELAY': 2,  # 2 second delay between requests
        'USER_AGENT': 'EconCell/1.0 (+https://github.com/TheLustriVA/Econcell)',
    }
    
    # Taxation categories to extract
    TAX_CATEGORIES = {
        'income_tax': ['Income taxes', 'Taxes on income'],
        'gst': ['Goods and services tax', 'GST'],
        'excise': ['Excise and customs duties', 'Excise'],
        'payroll': ['Payroll tax'],
        'property': ['Property taxes', 'Land tax', 'Stamp duties'],
        'other': ['Other taxes', 'Other taxation revenue']
    }
    
    # Expenditure categories (COFOG - Classification of Functions of Government)
    EXPENDITURE_CATEGORIES = {
        'general_services': ['General public services', 'General services'],
        'defence': ['Defence', 'Defence affairs'],
        'public_order': ['Public order and safety', 'Police', 'Fire protection', 'Law courts'],
        'economic_affairs': ['Economic affairs', 'Transport', 'Communication'],
        'environment': ['Environmental protection', 'Waste management'],
        'housing': ['Housing and community amenities', 'Housing', 'Community development'],
        'health': ['Health', 'Hospital services', 'Medical services'],
        'recreation': ['Recreation, culture and religion', 'Recreation', 'Culture'],
        'education': ['Education', 'Primary education', 'Secondary education', 'Tertiary education'],
        'social_protection': ['Social protection', 'Social security', 'Welfare']
    }
    
    # Government levels
    GOV_LEVELS = ['Commonwealth', 'State', 'Local', 'Total']
    
    def __init__(self, test_mode=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_mode = test_mode
        self.downloads_dir = Path('downloads/abs_gfs')
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        
        # Track download progress for large files
        self.download_progress = {}
        
        # Test mode limits
        if self.test_mode:
            self.files_downloaded = 0
            self.max_test_files = 1
            self.custom_settings.update({
                'CLOSESPIDER_ITEMCOUNT': 10,
                'CLOSESPIDER_TIMEOUT': 60,
                'DOWNLOAD_TIMEOUT': 60,
                'DOWNLOAD_MAXSIZE': 5 * 1024 * 1024,  # 5MB
                # Use test pipelines that write to test schema
                'ITEM_PIPELINES': {
                    'econdata.pipelines.abs_test_pipeline.ABSTestPipeline': 300,
                }
            })
            logger.info("Running in TEST MODE with limited downloads")
        
    def parse(self, response):
        """
        Parse the main ABS GFS page to find XLSX download links.
        """
        # Look for links to XLSX files
        xlsx_links = response.css('a[href*=".xlsx"]::attr(href)').getall()
        xlsx_links.extend(response.css('a[href*=".xls"]::attr(href)').getall())
        
        # Also look for links containing "5512" (the catalogue number)
        gfs_links = response.css('a[href*="5512"]::attr(href)').getall()
        
        # Process each potential GFS file
        for link in set(xlsx_links + gfs_links):
            absolute_url = urljoin(response.url, link)
            
            # Check if this looks like a GFS file
            if self._is_gfs_file(absolute_url):
                yield scrapy.Request(
                    url=absolute_url,
                    callback=self.download_gfs_file,
                    meta={
                        'download_timeout': 300,
                        'handle_httpstatus_list': [200, 206],  # Handle partial content
                    },
                    dont_filter=True
                )
        
        # Follow pagination or archive links
        archive_links = response.css('a:contains("Previous releases")::attr(href)').getall()
        archive_links.extend(response.css('a:contains("Time series")::attr(href)').getall())
        
        for link in archive_links:
            yield response.follow(link, callback=self.parse)
    
    def _is_gfs_file(self, url: str) -> bool:
        """Check if URL likely contains GFS data."""
        gfs_indicators = [
            '5512',  # Catalogue number
            'government-finance',
            'gfs',
            'taxation',
            'revenue'
        ]
        url_lower = url.lower()
        return any(indicator in url_lower for indicator in gfs_indicators)
    
    def download_gfs_file(self, response):
        """
        Download and save GFS XLSX file with progress tracking.
        """
        # Check test mode file limit
        if self.test_mode:
            if self.files_downloaded >= self.max_test_files:
                self.log(f"Test mode: Reached file limit of {self.max_test_files}")
                return
            self.files_downloaded += 1
        
        # Extract filename from URL or headers
        filename = self._extract_filename(response)
        filepath = self.downloads_dir / filename
        
        # Check if file already exists and is complete
        if filepath.exists():
            expected_size = int(response.headers.get('Content-Length', 0))
            actual_size = filepath.stat().st_size
            
            if expected_size > 0 and actual_size == expected_size:
                self.log(f"File {filename} already downloaded completely")
                yield from self.parse_gfs_file(filepath)
                return
        
        # Save the file
        try:
            filepath.write_bytes(response.body)
            self.log(f"Downloaded GFS file: {filename} ({len(response.body):,} bytes)")
            
            # Parse the downloaded file
            yield from self.parse_gfs_file(filepath)
            
        except Exception as e:
            self.log(f"Error downloading {filename}: {str(e)}", level=logging.ERROR)
            # Retry with smaller chunks if file is too large
            if len(response.body) > 50 * 1024 * 1024:  # 50MB
                yield from self._download_with_chunks(response)
    
    def _extract_filename(self, response) -> str:
        """Extract filename from response headers or URL."""
        # Try Content-Disposition header first
        cd = response.headers.get('Content-Disposition', b'').decode('utf-8')
        if 'filename=' in cd:
            filename = cd.split('filename=')[-1].strip('"')
        else:
            # Fall back to URL
            filename = os.path.basename(response.url.split('?')[0])
        
        # Ensure it has an extension
        if not filename.endswith(('.xlsx', '.xls')):
            filename += '.xlsx'
            
        # Add timestamp to avoid overwriting
        timestamp = datetime.now().strftime('%Y%m%d')
        name, ext = os.path.splitext(filename)
        return f"{name}_{timestamp}{ext}"
    
    def parse_gfs_file(self, filepath: Path):
        """
        Parse the downloaded GFS XLSX file and extract taxation and expenditure data.
        """
        try:
            # Read Excel file with all sheets
            excel_file = pd.ExcelFile(filepath)
            
            # Find sheets containing taxation data
            tax_sheets = self._find_tax_sheets(excel_file)
            
            # Find sheets containing expenditure data
            exp_sheets = self._find_expenditure_sheets(excel_file)
            
            # Process taxation sheets
            for sheet_name in tax_sheets:
                df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
                
                # Process the sheet to extract taxation data
                tax_data = self._extract_tax_data(df, sheet_name)
                
                # Yield items for pipeline processing
                for item in tax_data:
                    yield {
                        'spider': self.name,
                        'source_file': filepath.name,
                        'sheet_name': sheet_name,
                        'data_type': 'taxation',
                        'reference_period': item['period'],
                        'level_of_government': item['gov_level'],
                        'revenue_type': item['tax_type'],
                        'tax_category': item['category'],
                        'amount': item['amount'],
                        'unit': item.get('unit', 'AUD millions'),
                        'seasonally_adjusted': item.get('sa', False),
                        'data_quality': item.get('quality', 'final'),
                        'extraction_timestamp': datetime.utcnow().isoformat(),
                        'file_checksum': self._calculate_checksum(filepath)
                    }
            
            # Process expenditure sheets
            for sheet_name in exp_sheets:
                df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
                
                # Process the sheet to extract expenditure data
                exp_data = self._extract_expenditure_data(df, sheet_name)
                
                # Yield items for pipeline processing
                for item in exp_data:
                    yield {
                        'spider': self.name,
                        'source_file': filepath.name,
                        'sheet_name': sheet_name,
                        'data_type': 'expenditure',
                        'reference_period': item['period'],
                        'level_of_government': item['gov_level'],
                        'expenditure_type': item['exp_type'],
                        'expenditure_category': item['category'],
                        'cofog_code': item.get('cofog_code'),
                        'amount': item['amount'],
                        'unit': item.get('unit', 'AUD millions'),
                        'seasonally_adjusted': item.get('sa', False),
                        'data_quality': item.get('quality', 'final'),
                        'extraction_timestamp': datetime.utcnow().isoformat(),
                        'file_checksum': self._calculate_checksum(filepath)
                    }
                    
        except Exception as e:
            self.log(f"Error parsing {filepath}: {str(e)}", level=logging.ERROR)
            # Save problematic file for manual review
            error_path = self.downloads_dir / 'errors' / filepath.name
            error_path.parent.mkdir(exist_ok=True)
            filepath.rename(error_path)
    
    def _find_tax_sheets(self, excel_file: pd.ExcelFile) -> List[str]:
        """Identify sheets containing taxation data."""
        tax_sheets = []
        
        # Skip contents/index sheets
        skip_sheets = ['contents', 'index', 'glossary', 'notes']
        
        for sheet in excel_file.sheet_names:
            sheet_lower = sheet.lower()
            
            # Skip non-data sheets
            if any(skip in sheet_lower for skip in skip_sheets):
                continue
                
            # For ABS GFS, Table sheets usually contain the data
            if 'table' in sheet_lower:
                # Check if it contains tax data
                try:
                    df = pd.read_excel(excel_file, sheet_name=sheet, nrows=20)
                    content = ' '.join(df.astype(str).values.flatten()).lower()
                    if 'taxation revenue' in content or 'tax' in content:
                        tax_sheets.append(sheet)
                except:
                    continue
        
        return tax_sheets
    
    def _find_expenditure_sheets(self, excel_file: pd.ExcelFile) -> List[str]:
        """Identify sheets containing expenditure data."""
        exp_sheets = []
        
        # Skip contents/index sheets
        skip_sheets = ['contents', 'index', 'glossary', 'notes']
        
        for sheet in excel_file.sheet_names:
            sheet_lower = sheet.lower()
            
            # Skip non-data sheets
            if any(skip in sheet_lower for skip in skip_sheets):
                continue
                
            # For ABS GFS, Table sheets usually contain the data
            if 'table' in sheet_lower:
                # Check if it contains expenditure data
                try:
                    df = pd.read_excel(excel_file, sheet_name=sheet, nrows=20)
                    content = ' '.join(df.astype(str).values.flatten()).lower()
                    
                    # Look for expenditure indicators
                    exp_indicators = ['expenses', 'expenditure', 'spending', 'outlays', 
                                     'gfs expenses', 'total expenses', 'cofog']
                    
                    if any(indicator in content for indicator in exp_indicators):
                        # Exclude if it's primarily a revenue sheet
                        if 'taxation revenue' not in content:
                            exp_sheets.append(sheet)
                except:
                    continue
        
        return exp_sheets
    
    def _extract_tax_data(self, df: pd.DataFrame, sheet_name: str) -> List[Dict]:
        """
        Extract taxation data from ABS GFS format.
        
        Simplified to handle the actual ABS format:
        - Years in row 4
        - Data values starting around row 7
        - First column contains row labels
        """
        import re
        tax_data = []
        
        # Extract government level from sheet name or table title
        gov_level = self._extract_government_level(df, sheet_name)
        
        # Find year row (typically row 4, but search for it)
        year_row_idx = None
        years = []
        year_cols = []
        
        for i in range(min(10, len(df))):
            row = df.iloc[i]
            # Check if this row contains years (format: YYYY-YY)
            year_count = 0
            for j, val in enumerate(row):
                if pd.notna(val) and re.match(r'^\d{4}-\d{2}$', str(val).strip()):
                    year_count += 1
                    if year_row_idx is None:
                        year_row_idx = i
                        years.append(str(val).strip())
                        year_cols.append(j)
                    elif year_row_idx == i:
                        years.append(str(val).strip())
                        year_cols.append(j)
            
            if year_count >= 3:  # Found year row
                break
        
        if not years:
            self.log(f"No years found in {sheet_name}", level=logging.WARNING)
            return tax_data
        
        # Find rows containing taxation data
        for row_idx in range(year_row_idx + 1, min(len(df), year_row_idx + 50)):
            row_label = str(df.iloc[row_idx, 0]).strip() if pd.notna(df.iloc[row_idx, 0]) else ""
            
            # Skip empty rows or headers
            if not row_label or row_label.upper() in ['GFS REVENUE', 'GFS EXPENSES', 'NET OPERATING BALANCE']:
                continue
            
            # Check if this row contains tax-related data
            if 'tax' in row_label.lower() or row_label.lower() in ['gst', 'excise', 'customs', 'levy']:
                # Extract values for each year
                for j, (year, col_idx) in enumerate(zip(years, year_cols)):
                    try:
                        value = df.iloc[row_idx, col_idx]
                        amount = self._clean_numeric_value(value)
                        
                        if amount is not None:
                            # Determine tax category
                            category = self._categorize_tax_type(row_label)
                            
                            tax_data.append({
                                'period': self._convert_financial_year_to_date(year),
                                'tax_type': row_label,
                                'category': category,
                                'gov_level': gov_level,
                                'amount': amount,
                                'unit': 'AUD millions',
                                'quality': 'final'
                            })
                    except Exception as e:
                        self.log(f"Error extracting value at row {row_idx}, col {col_idx}: {e}", 
                                level=logging.DEBUG)
                        continue
        
        # If annual data, create quarterly estimates
        if tax_data and self._is_annual_data(tax_data):
            tax_data = self._interpolate_to_quarterly(tax_data)
        
        return tax_data
    
    def _find_data_start(self, df: pd.DataFrame) -> Optional[int]:
        """Find where the actual data starts in the sheet."""
        # Look for rows with multiple numeric values
        for i in range(min(30, len(df))):  # Check first 30 rows
            row = df.iloc[i]
            numeric_count = row.apply(lambda x: isinstance(x, (int, float)) or 
                                    (isinstance(x, str) and x.replace('.', '').replace('-', '').isdigit())).sum()
            if numeric_count >= 3:  # At least 3 numeric columns
                # Backtrack to find the header
                return max(0, i - 3)
        return None
    
    def _extract_headers(self, df: pd.DataFrame, start_row: int) -> Dict:
        """Extract and parse complex headers."""
        headers = {}
        
        # Typically headers span 2-3 rows before data
        header_rows = []
        for i in range(max(0, start_row - 2), start_row + 1):
            if i < len(df):
                header_rows.append(df.iloc[i])
        
        # Combine header rows
        for col_idx in range(len(df.columns)):
            header_parts = []
            for row in header_rows:
                if col_idx < len(row) and pd.notna(row.iloc[col_idx]):
                    header_parts.append(str(row.iloc[col_idx]))
            
            headers[col_idx] = ' '.join(header_parts)
        
        return headers
    
    def _identify_period_columns(self, df: pd.DataFrame, headers: Dict) -> List[Dict]:
        """Identify columns containing year/period data."""
        period_cols = []
        
        for col_idx, header in headers.items():
            # Look for year patterns (e.g., 2023, 2023-24, FY2023)
            if any(str(year) in str(header) for year in range(2000, 2030)):
                period = self._parse_period(header)
                if period:
                    period_cols.append({
                        'col': col_idx,
                        'period': period,
                        'header': header
                    })
        
        return sorted(period_cols, key=lambda x: x['period'])
    
    def _identify_tax_rows(self, df: pd.DataFrame, start_row: int) -> List[Dict]:
        """Identify rows containing different tax types."""
        tax_rows = []
        
        # Scan rows after headers
        for row_idx in range(start_row + 3, min(start_row + 100, len(df))):
            row_label = str(df.iloc[row_idx, 0]) if pd.notna(df.iloc[row_idx, 0]) else ''
            
            # Match against known tax categories
            for category, patterns in self.TAX_CATEGORIES.items():
                if any(pattern.lower() in row_label.lower() for pattern in patterns):
                    # Determine government level if specified
                    gov_level = 'Total'
                    for level in self.GOV_LEVELS:
                        if level.lower() in row_label.lower():
                            gov_level = level
                            break
                    
                    tax_rows.append({
                        'row': row_idx,
                        'type': row_label.strip(),
                        'category': category,
                        'gov_level': gov_level
                    })
                    break
        
        return tax_rows
    
    def _extract_government_level(self, df: pd.DataFrame, sheet_name: str) -> str:
        """Extract government level from sheet data or name."""
        # Check first few rows for government level indicators
        for i in range(min(5, len(df))):
            for j in range(min(3, len(df.columns))):
                cell = str(df.iloc[i, j]) if pd.notna(df.iloc[i, j]) else ""
                if 'commonwealth' in cell.lower():
                    return 'Commonwealth'
                elif 'state' in cell.lower():
                    # Try to extract specific state
                    if 'new south wales' in cell.lower():
                        return 'NSW State'
                    elif 'victoria' in cell.lower():
                        return 'VIC State'
                    elif 'queensland' in cell.lower():
                        return 'QLD State'
                    elif 'south australia' in cell.lower():
                        return 'SA State'
                    elif 'western australia' in cell.lower():
                        return 'WA State'
                    elif 'tasmania' in cell.lower():
                        return 'TAS State'
                    elif 'northern territory' in cell.lower():
                        return 'NT Territory'
                    elif 'australian capital territory' in cell.lower():
                        return 'ACT Territory'
                    else:
                        return 'State'
                elif 'local' in cell.lower():
                    return 'Local'
        
        # Default based on sheet name patterns
        if 'commonwealth' in sheet_name.lower():
            return 'Commonwealth'
        elif 'state' in sheet_name.lower():
            return 'State'
        elif 'local' in sheet_name.lower():
            return 'Local'
        else:
            return 'Total'
    
    def _categorize_tax_type(self, tax_label: str) -> str:
        """Categorize tax type based on label."""
        label_lower = tax_label.lower()
        
        if 'income' in label_lower or 'company' in label_lower or 'personal' in label_lower:
            return 'Income Tax'
        elif 'gst' in label_lower or 'goods and services' in label_lower:
            return 'GST'
        elif 'payroll' in label_lower:
            return 'Payroll Tax'
        elif 'excise' in label_lower:
            return 'Excise'
        elif 'customs' in label_lower:
            return 'Customs Duty'
        elif 'land' in label_lower:
            return 'Land Tax'
        elif 'stamp' in label_lower:
            return 'Stamp Duty'
        elif 'gambling' in label_lower or 'gaming' in label_lower:
            return 'Gambling Tax'
        elif 'motor' in label_lower or 'vehicle' in label_lower:
            return 'Motor Vehicle Tax'
        elif 'total' in label_lower and 'tax' in label_lower:
            return 'Total Taxation'
        else:
            return 'Other Tax'
    
    def _clean_numeric_value(self, value) -> Optional[float]:
        """Clean and convert value to numeric."""
        if pd.isna(value):
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        # Handle string values
        value_str = str(value).strip()
        
        # Remove common annotations
        value_str = value_str.replace(',', '').replace('$', '')
        value_str = value_str.replace('m', '').replace('M', '')  # millions indicator
        
        # Handle special cases
        if value_str in ['-', '..', 'np', 'na', 'n.a.']:
            return None
        
        try:
            return float(value_str)
        except:
            return None
    
    def _parse_period(self, period_str: str) -> Optional[str]:
        """Parse various period formats to standard YYYY-MM-DD."""
        period_str = str(period_str).strip()
        
        # Financial year format (e.g., 2023-24)
        if '-' in period_str and len(period_str.split('-')[0]) == 4:
            year = int(period_str.split('-')[0])
            return f"{year}-07-01"  # Start of financial year
        
        # Calendar year
        for year in range(2000, 2030):
            if str(year) in period_str and 'FY' not in period_str:
                return f"{year}-01-01"
        
        # FY format (e.g., FY2023)
        if 'FY' in period_str:
            year = int(''.join(c for c in period_str if c.isdigit()))
            return f"{year-1}-07-01"  # FY2023 starts July 2022
        
        return None
    
    def _is_annual_data(self, tax_data: List[Dict]) -> bool:
        """Check if the data is annual (vs quarterly)."""
        if not tax_data:
            return False
        
        # Get unique periods
        periods = sorted(set(item['period'] for item in tax_data))
        
        if len(periods) < 2:
            return True
        
        # Check gap between periods
        try:
            date1 = pd.to_datetime(periods[0])
            date2 = pd.to_datetime(periods[1])
            gap_days = (date2 - date1).days
            
            # Annual if gap is > 300 days
            return gap_days > 300
        except:
            return True
    
    def _extract_expenditure_data(self, df: pd.DataFrame, sheet_name: str) -> List[Dict]:
        """
        Extract expenditure data from ABS GFS format.
        """
        import re
        exp_data = []
        
        # Extract government level from sheet name or table title
        gov_level = self._extract_government_level(df, sheet_name)
        
        # Find year row (typically row 4, but search for it)
        year_row_idx = None
        years = []
        year_cols = []
        
        for i in range(min(10, len(df))):
            row = df.iloc[i]
            # Check if this row contains years (format: YYYY-YY)
            year_count = 0
            for j, val in enumerate(row):
                if pd.notna(val) and re.match(r'^\d{4}-\d{2}$', str(val).strip()):
                    year_count += 1
                    if year_row_idx is None:
                        year_row_idx = i
                        years.append(str(val).strip())
                        year_cols.append(j)
                    elif year_row_idx == i:
                        years.append(str(val).strip())
                        year_cols.append(j)
            
            if year_count >= 3:  # Found year row
                break
        
        if not years:
            self.log(f"No years found in {sheet_name}", level=logging.WARNING)
            return exp_data
        
        # Find rows containing expenditure data
        for row_idx in range(year_row_idx + 1, min(len(df), year_row_idx + 100)):
            row_label = str(df.iloc[row_idx, 0]).strip() if pd.notna(df.iloc[row_idx, 0]) else ""
            
            # Skip empty rows or revenue headers
            if not row_label or 'revenue' in row_label.lower():
                continue
            
            # Check if this row contains expenditure-related data
            exp_keywords = ['expense', 'expenditure', 'spending', 'outlays']
            cofog_keywords = list(self.EXPENDITURE_CATEGORIES.keys())
            
            # Check for direct expenditure keywords or COFOG categories
            is_expenditure = False
            category = 'other'
            
            # First check for COFOG categories
            for cat_key, patterns in self.EXPENDITURE_CATEGORIES.items():
                if any(pattern.lower() in row_label.lower() for pattern in patterns):
                    is_expenditure = True
                    category = cat_key
                    break
            
            # If not found, check for general expenditure keywords
            if not is_expenditure and any(kw in row_label.lower() for kw in exp_keywords):
                is_expenditure = True
                category = self._categorize_expenditure_type(row_label)
            
            if is_expenditure:
                # Extract COFOG code if present (format: nn.n or nn)
                cofog_match = re.search(r'\b(\d{1,2}(?:\.\d)?)\b', row_label)
                cofog_code = cofog_match.group(1) if cofog_match else None
                
                # Extract values for each year
                for j, (year, col_idx) in enumerate(zip(years, year_cols)):
                    try:
                        value = df.iloc[row_idx, col_idx]
                        amount = self._clean_numeric_value(value)
                        
                        if amount is not None:
                            exp_data.append({
                                'period': self._convert_financial_year_to_date(year),
                                'exp_type': row_label,
                                'category': category,
                                'cofog_code': cofog_code,
                                'gov_level': gov_level,
                                'amount': amount,
                                'unit': 'AUD millions',
                                'quality': 'final'
                            })
                    except Exception as e:
                        self.log(f"Error extracting value at row {row_idx}, col {col_idx}: {e}", 
                                level=logging.DEBUG)
                        continue
        
        # If annual data, create quarterly estimates
        if exp_data and self._is_annual_data(exp_data):
            exp_data = self._interpolate_expenditure_to_quarterly(exp_data)
        
        return exp_data
    
    def _categorize_expenditure_type(self, exp_label: str) -> str:
        """Categorize expenditure type based on label."""
        label_lower = exp_label.lower()
        
        # Check against EXPENDITURE_CATEGORIES
        for category, patterns in self.EXPENDITURE_CATEGORIES.items():
            if any(pattern.lower() in label_lower for pattern in patterns):
                return category
        
        # Additional categorization logic
        if 'salaries' in label_lower or 'wages' in label_lower:
            return 'employee_expenses'
        elif 'grants' in label_lower:
            return 'grants_subsidies'
        elif 'interest' in label_lower:
            return 'interest_payments'
        elif 'capital' in label_lower:
            return 'capital_expenditure'
        elif 'total' in label_lower and 'expense' in label_lower:
            return 'total_expenditure'
        else:
            return 'other_expenditure'
    
    def _interpolate_expenditure_to_quarterly(self, annual_data: List[Dict]) -> List[Dict]:
        """
        Convert annual expenditure data to quarterly estimates.
        """
        quarterly_data = []
        
        # Group by expenditure type and government level
        from itertools import groupby
        key_func = lambda x: (x['exp_type'], x['gov_level'], x['category'])
        sorted_data = sorted(annual_data, key=key_func)
        
        for key, group in groupby(sorted_data, key_func):
            group_list = list(group)
            exp_type, gov_level, category = key
            
            # Sort by period
            group_list.sort(key=lambda x: x['period'])
            
            for i, item in enumerate(group_list):
                annual_amount = item['amount']
                base_date = pd.to_datetime(item['period'])
                
                # Create 4 quarterly estimates
                for quarter in range(4):
                    quarter_date = base_date + pd.DateOffset(months=quarter * 3)
                    
                    # Apply seasonal patterns based on expenditure type
                    quarterly_amount = annual_amount / 4
                    
                    # Government spending patterns
                    if category == 'health':
                        # Health spending higher in winter (Q2, Q3)
                        seasonal_factors = [0.95, 1.05, 1.05, 0.95]
                        quarterly_amount *= seasonal_factors[quarter]
                    elif category == 'education':
                        # Education spending follows school terms
                        seasonal_factors = [1.1, 0.9, 1.1, 0.9]
                        quarterly_amount *= seasonal_factors[quarter]
                    elif category == 'social_protection':
                        # Social spending higher in Q4 (end of year payments)
                        seasonal_factors = [0.95, 0.98, 1.02, 1.05]
                        quarterly_amount *= seasonal_factors[quarter]
                    
                    quarterly_data.append({
                        **item,
                        'period': quarter_date.strftime('%Y-%m-%d'),
                        'amount': round(quarterly_amount, 2),
                        'interpolated': True,
                        'interpolation_method': 'seasonal_linear'
                    })
        
        return quarterly_data
    
    def _convert_financial_year_to_date(self, fy_string: str) -> str:
        """Convert financial year string (e.g., '2014-15') to end date."""
        try:
            # Extract the start year
            if '-' in fy_string:
                start_year = int(fy_string.split('-')[0])
                # Financial year ends June 30
                return f"{start_year + 1}-06-30"
            else:
                # Already a date
                return fy_string
        except:
            return fy_string
    
    def _interpolate_to_quarterly(self, annual_data: List[Dict]) -> List[Dict]:
        """
        Convert annual data to quarterly estimates.
        
        Uses simple linear interpolation as a baseline.
        More sophisticated methods can be added based on historical patterns.
        """
        quarterly_data = []
        
        # Group by tax type and government level
        from itertools import groupby
        key_func = lambda x: (x['tax_type'], x['gov_level'], x['category'])
        sorted_data = sorted(annual_data, key=key_func)
        
        for key, group in groupby(sorted_data, key_func):
            group_list = list(group)
            tax_type, gov_level, category = key
            
            # Sort by period
            group_list.sort(key=lambda x: x['period'])
            
            for i, item in enumerate(group_list):
                annual_amount = item['amount']
                base_date = pd.to_datetime(item['period'])
                
                # Create 4 quarterly estimates
                for quarter in range(4):
                    quarter_date = base_date + pd.DateOffset(months=quarter * 3)
                    
                    # Simple equal distribution
                    # TODO: Use seasonal patterns from historical data
                    quarterly_amount = annual_amount / 4
                    
                    # Add seasonal adjustment factors based on tax type
                    if category == 'income_tax':
                        # Income tax typically higher in Q4 (tax returns)
                        seasonal_factors = [0.9, 0.95, 1.0, 1.15]
                        quarterly_amount *= seasonal_factors[quarter]
                    elif category == 'gst':
                        # GST relatively stable with slight Christmas boost
                        seasonal_factors = [0.98, 0.99, 1.01, 1.02]
                        quarterly_amount *= seasonal_factors[quarter]
                    
                    quarterly_data.append({
                        **item,
                        'period': quarter_date.strftime('%Y-%m-%d'),
                        'amount': round(quarterly_amount, 2),
                        'interpolated': True,
                        'interpolation_method': 'seasonal_linear'
                    })
        
        return quarterly_data
    
    def _calculate_checksum(self, filepath: Path) -> str:
        """Calculate SHA256 checksum of file for integrity tracking."""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _download_with_chunks(self, response):
        """
        Handle very large files by downloading in chunks.
        
        This is a fallback for files that are too large for memory.
        """
        # This would implement HTTP range requests
        # For now, log the issue
        self.log(f"File too large for single download: {response.url}", level=logging.WARNING)
        # In a production system, this would:
        # 1. Use HTTP Range headers to download in chunks
        # 2. Reassemble the file on disk
        # 3. Verify integrity with checksums
        return []  # Return empty list for now
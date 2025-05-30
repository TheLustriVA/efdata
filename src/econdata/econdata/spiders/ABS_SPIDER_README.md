# ABS Government Finance Statistics Spider

## Overview

The `abs_gfs` spider collects taxation revenue data (T component) from the Australian Bureau of Statistics Government Finance Statistics publications. This fills a critical gap in the RBA circular flow model as the RBA does not provide direct taxation data.

## Features

- **XLSX File Handling**: Downloads and parses Excel files (unlike RBA's CSV format)
- **Large File Support**: Handles files up to 100MB with chunking and retry logic
- **Multi-sheet Parsing**: Intelligently identifies taxation data across multiple worksheets
- **Annual to Quarterly Conversion**: Interpolates annual data to quarterly estimates using seasonal patterns
- **Data Validation**: Comprehensive validation of amounts, categories, and government levels
- **Error Recovery**: Automatic retry on failures with exponential backoff

## Data Collected

### Tax Categories
- **Income Tax**: Personal and corporate income taxes
- **GST**: Goods and Services Tax
- **Excise & Customs**: Fuel, alcohol, tobacco excises and import duties
- **Payroll Tax**: State-level employment taxes
- **Property Taxes**: Land tax, stamp duties, and other property-related taxes
- **Other**: Miscellaneous taxes and levies

### Government Levels
- Commonwealth (Federal)
- State (by individual state/territory)
- Local Government
- Total (All levels consolidated)

## Usage

### Manual Testing
```bash
# From the econdata directory
cd src/econdata
scrapy crawl abs_gfs

# Using the scheduler test command
python src/scheduler/start_scheduler.py test-abs
```

### Scheduled Execution
The spider runs automatically on the 15th of each month at 2:00 AM AEST via the scheduler.

### Database Requirements
Before running, ensure the taxation schema is created:
```bash
psql -U postgres -d econdata -f debug/abs_taxation_schema.sql
```

## Configuration

### Spider Settings
```python
# Custom settings in spider
DOWNLOAD_TIMEOUT = 300  # 5 minutes for large files
RETRY_TIMES = 3
CONCURRENT_REQUESTS = 2  # Be gentle with ABS servers
DOWNLOAD_DELAY = 2  # 2 second delay between requests
```

### Environment Variables
No additional environment variables required beyond standard database configuration.

## Data Flow

1. **Download**: Spider fetches XLSX files from ABS website
2. **Parse**: Complex Excel sheets parsed to extract taxation data
3. **Validate**: Data validated against business rules
4. **Enrich**: Additional metadata added (fiscal year, quarter)
5. **Stage**: Data inserted into `abs_staging.government_finance_statistics`
6. **Process**: ETL function transforms staged data to fact tables
7. **Integrate**: Taxation data linked to circular flow model

## Troubleshooting

### Common Issues

1. **File Too Large Error**
   - Check `DOWNLOAD_MAXSIZE` setting (default 100MB)
   - Large files saved to `downloads/abs_gfs/errors/` for manual review

2. **Excel Parsing Errors**
   - Verify pandas and openpyxl are installed
   - Check sheet structure hasn't changed significantly

3. **Validation Failures**
   - Review `spider.log` for specific validation errors
   - Check `abs_staging.data_quality_checks` view for issues

4. **No Data Found**
   - Verify ABS website structure hasn't changed
   - Check if publication schedule has changed

### Logs
```bash
# View spider logs
tail -f src/scheduler/scheduler.log

# Check database for staging records
psql -d econdata -c "SELECT COUNT(*), MIN(reference_period), MAX(reference_period) FROM abs_staging.government_finance_statistics;"

# View data quality issues
psql -d econdata -c "SELECT * FROM abs_staging.data_quality_checks;"
```

## Performance Considerations

- **Download Size**: GFS files can be 10-50MB
- **Processing Time**: ~2-5 minutes per file depending on complexity
- **Memory Usage**: Peaks at ~500MB during Excel processing
- **Database Load**: Inserts ~1000-5000 records per run

## Future Enhancements

1. **Treasury Integration**: Add monthly financial statements for higher frequency updates
2. **State Budget Data**: Extend to individual state budget publications
3. **API Migration**: Switch to API when ABS launches one
4. **ML Classification**: Use LLMs to classify new tax types automatically
5. **Forecasting**: Add predictive models for tax revenue estimation

## Dependencies

- pandas >= 2.0.0 (for Excel processing)
- openpyxl (pandas Excel engine)
- psycopg2-binary (PostgreSQL connection)
- scrapy >= 2.11.0 (web scraping framework)

## Maintenance

The spider is designed to be resilient to format changes through:
- Fuzzy matching of column headers
- AI-powered tax classification
- Flexible sheet detection
- Comprehensive error logging

Regular maintenance tasks:
- Monitor ABS publication schedule changes
- Update URL patterns if website restructures
- Review validation thresholds annually
- Archive old downloaded files monthly
# ABS Spider Testing Strategy: Dry-Run Recommendations

## Executive Summary

**Recommended Approach**: Implement a **hybrid testing strategy** combining:
1. Local mock files with realistic data structures
2. Test-specific database schema/user
3. Spider test mode with configurable data limits

This provides the best balance of realism, safety, and development velocity.

## Analysis of Testing Approaches

### Option 1: Mock API Server

**Implementation**: Local HTTP server mimicking ABS website structure

**Pros:**
- Complete control over test scenarios
- No external dependencies
- Can simulate errors and edge cases
- Fast and repeatable

**Cons:**
- High initial setup effort
- Must maintain mock data as ABS changes
- Doesn't test real HTTP handling
- May miss real-world complexities

**Verdict**: ❌ Too much overhead for current needs

### Option 2: Staging Database

**Implementation**: Separate PostgreSQL database or schema for testing

**Pros:**
- Production-like environment
- No risk to production data
- Can test full ETL pipeline
- Easy cleanup between tests

**Cons:**
- Requires database administration
- Still needs test data source
- May diverge from production schema
- Additional maintenance burden

**Verdict**: ✅ Good for integration testing

### Option 3: Local Sample Files

**Implementation**: Small XLSX files mimicking ABS structure

**Pros:**
- Simple to implement
- No network dependencies
- Fast test execution
- Version controlled test data

**Cons:**
- Doesn't test download logic
- May not catch parsing edge cases
- Manual creation of test files
- Limited scenario coverage

**Verdict**: ✅ Good for unit testing

### Option 4: Spider Test Mode

**Implementation**: Add `--test-mode` flag limiting downloads/processing

**Pros:**
- Tests real ABS interaction
- Minimal code changes
- Configurable limits
- Production code path

**Cons:**
- Still downloads some data
- Depends on ABS availability
- Slower than pure mocks
- Network dependency

**Verdict**: ✅ Good for smoke testing

## Recommended Implementation

### 1. Create Test Infrastructure

```python
# src/econdata/econdata/spiders/abs_data_test_mode.py

class ABSGFSTestSpider(ABSGFSSpider):
    """Test version of ABS spider with safety limits"""
    
    name = 'abs_gfs_test'
    
    custom_settings = {
        **ABSGFSSpider.custom_settings,
        'CLOSESPIDER_ITEMCOUNT': 10,  # Stop after 10 items
        'CLOSESPIDER_TIMEOUT': 60,     # 1 minute timeout
        'DOWNLOAD_MAXSIZE': 5 * 1024 * 1024,  # 5MB max
    }
    
    def __init__(self, test_mode=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_mode = test_mode
        self.test_file_limit = 1  # Only process 1 file
        
    def parse(self, response):
        """Override to limit scope in test mode"""
        if self.test_mode:
            # Only follow first XLSX link
            xlsx_links = response.css('a[href*=".xlsx"]::attr(href)').getall()[:1]
            for link in xlsx_links:
                yield response.follow(link, callback=self.download_gfs_file)
        else:
            yield from super().parse(response)
```

### 2. Test Database Configuration

```sql
-- Create test schema
CREATE SCHEMA IF NOT EXISTS abs_staging_test;
CREATE SCHEMA IF NOT EXISTS abs_dimensions_test;

-- Create test user with limited permissions
CREATE USER econcell_test WITH PASSWORD 'test_only_password';
GRANT USAGE ON SCHEMA abs_staging_test, abs_dimensions_test TO econcell_test;
GRANT CREATE ON SCHEMA abs_staging_test, abs_dimensions_test TO econcell_test;

-- Copy table structures
CREATE TABLE abs_staging_test.government_finance_statistics 
    (LIKE abs_staging.government_finance_statistics INCLUDING ALL);
```

### 3. Sample Test Data

```bash
# Create test fixtures directory
mkdir -p src/econdata/tests/fixtures/abs

# Add small sample XLSX files (under 1MB)
# - valid_gfs_sample.xlsx (correct format)
# - invalid_headers.xlsx (parsing challenge)
# - empty_sheets.xlsx (edge case)
# - multi_year.xlsx (interpolation test)
```

### 4. Test Execution Script

```python
# src/econdata/tests/test_abs_spider.py

import pytest
from scrapy.crawler import CrawlerProcess
from econdata.spiders.abs_data import ABSGFSSpider

class TestABSSpider:
    
    @pytest.fixture
    def spider_settings(self):
        return {
            'ITEM_PIPELINES': {
                'econdata.pipelines.abs_taxation_pipeline.ABSTaxationPipeline': 450,
            },
            'DB_NAME': 'econdata_test',
            'DB_USER': 'econcell_test',
            'DB_PASSWORD': 'test_only_password',
            'DOWNLOAD_DELAY': 0,  # No delay in tests
            'ROBOTSTXT_OBEY': False,
        }
    
    def test_local_file_parsing(self, spider_settings):
        """Test with local sample files"""
        process = CrawlerProcess(spider_settings)
        process.crawl(
            ABSGFSSpider,
            start_urls=['file:///path/to/fixtures/'],
            test_mode=True
        )
        process.start()
    
    def test_dry_run_live(self, spider_settings):
        """Limited test against real ABS site"""
        spider_settings['CLOSESPIDER_ITEMCOUNT'] = 5
        spider_settings['DOWNLOAD_TIMEOUT'] = 30
        
        process = CrawlerProcess(spider_settings)
        process.crawl(ABSGFSSpider, test_mode=True)
        process.start()
```

### 5. Dry-Run Command

```bash
# Add to scheduler
elif args.command == 'test-abs-dry':
    # Use test database and limits
    os.environ['DB_NAME'] = 'econdata_test'
    os.environ['SCRAPY_CLOSESPIDER_ITEMCOUNT'] = '10'
    os.environ['SCRAPY_DOWNLOAD_MAXSIZE'] = '5242880'  # 5MB
    
    scheduler = SpiderScheduler()
    scheduler.run_spider_now('abs_gfs_test')
    
    # Show test results
    print("\nTest Results:")
    print("- Check abs_staging_test.government_finance_statistics")
    print("- Review logs in src/scheduler/scheduler.log")
    print("- No production data affected")
```

## Implementation Priority

### Phase 1: Immediate (Week 1)
1. ✅ Create test schema in database
2. ✅ Add `test_mode` parameter to spider
3. ✅ Implement item count limits
4. ✅ Add dry-run command to scheduler

### Phase 2: Short-term (Week 2)
1. Create sample XLSX fixtures
2. Write unit tests for parsing logic
3. Add validation test suite
4. Document test procedures

### Phase 3: Long-term (Month 2)
1. Consider Docker test environment
2. Add CI/CD integration tests
3. Build test data generator
4. Performance benchmarking

## Testing Workflow

```bash
# 1. Quick smoke test (no downloads)
pytest src/econdata/tests/test_abs_spider.py::test_local_file_parsing

# 2. Integration test (limited downloads)
python src/scheduler/start_scheduler.py test-abs-dry

# 3. Full test (staging database)
DB_NAME=econdata_staging scrapy crawl abs_gfs

# 4. Production run (with monitoring)
python src/scheduler/start_scheduler.py test-abs
```

## Monitoring & Validation

### Dry-Run Checklist
- [ ] Spider completes without errors
- [ ] Test database contains expected records
- [ ] No production database changes
- [ ] Download size under limit
- [ ] Execution time reasonable (<2 minutes)

### Validation Queries
```sql
-- Check test results
SELECT COUNT(*), MIN(reference_period), MAX(reference_period)
FROM abs_staging_test.government_finance_statistics;

-- Verify no production impact
SELECT COUNT(*) FROM abs_staging.government_finance_statistics 
WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '1 hour';
```

## Risk Mitigation

1. **Network Issues**: Use local fixtures for critical tests
2. **Schema Drift**: Automated schema comparison tests
3. **Data Quality**: Validation pipeline catches issues early
4. **Performance**: Time limits prevent runaway processes
5. **Security**: Test credentials never in production code

## Conclusion

The hybrid approach provides multiple testing levels:
- **Unit tests**: Fast, focused, no dependencies
- **Integration tests**: Real parsing, test database
- **Smoke tests**: Limited production-like runs
- **Full tests**: Complete flow in staging

This strategy ensures safe, efficient testing while maintaining confidence in the spider's production readiness.
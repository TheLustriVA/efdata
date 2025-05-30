# Taxation Spider Design Document

## Executive Summary

The RBA does NOT provide direct taxation data in their statistical tables. To complete the T (Taxation) component of the circular flow model, we need to implement data collection from the Australian Bureau of Statistics (ABS) and potentially the Treasury. This document outlines a future-proof architecture for taxation data collection.

## Current State Analysis

### Key Findings
1. **No RBA Taxation Data**: The RBA statistical tables focus on monetary policy, banking, and trade - not fiscal data
2. **Database Ready**: Our schema already supports taxation data with proper dimensions and fact tables
3. **Clear Requirements**: Documentation clearly identifies ABS Government Finance Statistics (5512.0) as the primary source
4. **Infrastructure Exists**: Scrapy framework, AI enrichment, and database pipelines are ready

### Data Gap
- **Missing**: T (Taxation) - government revenue by type and level
- **Missing**: G (Government Spending) - detailed functional breakdown
- **Impact**: Cannot validate S+T+M = I+G+X circular flow equation

## Proposed Architecture

### 1. ABS Spider (`abs_data.py`)

```python
class ABSDataSpider(scrapy.Spider):
    """
    Collects Government Finance Statistics from ABS
    Primary source: Catalogue 5512.0
    """
    
    name = 'abs_gfs'
    
    # Key design decisions:
    # 1. Handle XLSX downloads (not CSV like RBA)
    # 2. Parse multi-sheet workbooks
    # 3. Deal with ABS's complex headers
    # 4. Implement retry logic for large files
    
    def parse_taxation_data(self, response):
        """
        Extract:
        - Income tax (personal, corporate)
        - GST revenue
        - Excise and customs duties
        - Payroll tax (state level)
        - Land tax and stamp duties
        """
```

### 2. Treasury Spider (`treasury_data.py`)

```python
class TreasuryDataSpider(scrapy.Spider):
    """
    Collects Monthly Financial Statements
    Provides more frequent updates than annual ABS
    """
    
    name = 'treasury_mfs'
    
    # Design considerations:
    # 1. PDF parsing capability needed
    # 2. Table extraction from formatted reports
    # 3. Reconciliation with ABS annual data
```

### 3. Data Pipeline Enhancements

#### Staging Tables
```sql
-- New staging tables needed
CREATE TABLE abs_staging.government_finance_statistics (
    reference_period TEXT,
    level_of_government TEXT,  -- Commonwealth, State, Local
    revenue_type TEXT,          -- Tax classification
    cofog_code TEXT,           -- Classification of Functions of Govt
    amount NUMERIC,
    unit TEXT,
    seasonally_adjusted BOOLEAN
);

CREATE TABLE treasury_staging.monthly_financial_statements (
    report_month DATE,
    revenue_category TEXT,
    budget_estimate NUMERIC,
    actual_amount NUMERIC,
    variance NUMERIC
);
```

#### ETL Process
1. **Download Management**: Handle large XLSX files efficiently
2. **Format Conversion**: XLSX → staging tables
3. **Data Validation**: Cross-check Treasury vs ABS totals
4. **Frequency Alignment**: Convert annual to quarterly estimates
5. **AI Enrichment**: Classify revenue types to standard taxonomy

### 4. Future-Proofing Strategies

#### A. Flexible Data Source Architecture
```python
class BaseGovernmentDataSpider(scrapy.Spider):
    """Abstract base for all government data sources"""
    
    def validate_fiscal_data(self, data):
        """Common validation for all fiscal sources"""
        
    def map_to_circular_flow(self, data):
        """Standard mapping to T or G components"""
```

#### B. Multi-Source Reconciliation
- Design for multiple sources from day 1
- Build reconciliation views in database
- Track data lineage and confidence scores

#### C. API-First Design
Even though current sources are file-based:
```python
def check_for_api(self):
    """
    Periodically check if ABS/Treasury launch APIs
    Seamlessly switch from file downloads when available
    """
```

### 5. Error Handling & Resilience

#### Common Challenges & Solutions

1. **Large File Downloads**
   ```python
   # Implement chunked downloads
   # Resume capability for failed downloads
   # Progress tracking in database
   ```

2. **Format Changes**
   ```python
   # AI-powered header detection
   # Fuzzy matching for column names
   # Alert system for manual review
   ```

3. **Missing Data Periods**
   ```python
   # Interpolation strategies
   # Use Treasury data to fill ABS gaps
   # Clear data quality indicators
   ```

### 6. Integration with Existing System

#### Database Integration
```sql
-- Link to circular flow
INSERT INTO rba_analytics.circular_flow (
    date, frequency, component, value, data_source_id
)
SELECT 
    reference_period::date,
    'Quarterly',
    'T',
    SUM(amount),
    source.id
FROM abs_staging.government_finance_statistics
GROUP BY reference_period;
```

#### AI Enhancement
```python
# Use existing LLM pipeline for:
# - Revenue type classification
# - Anomaly detection in tax receipts
# - Natural language descriptions
```

### 7. Incremental Implementation Plan

#### Phase 1: Basic ABS Integration (Week 1)
- [ ] Create `abs_data.py` spider
- [ ] Implement XLSX download handling
- [ ] Parse basic taxation totals
- [ ] Store in staging tables

#### Phase 2: Full Taxonomy (Week 2)
- [ ] Complete revenue type classification
- [ ] Add level of government dimension
- [ ] Implement data validation
- [ ] Create reconciliation views

#### Phase 3: Treasury Integration (Week 3)
- [ ] Create `treasury_data.py` spider
- [ ] Add PDF parsing capability
- [ ] Build monthly update process
- [ ] Cross-validate with ABS

#### Phase 4: Production Hardening (Week 4)
- [ ] Add comprehensive error handling
- [ ] Implement monitoring and alerts
- [ ] Create data quality dashboards
- [ ] Document operational procedures

### 8. Success Metrics

1. **Data Completeness**: 100% coverage of major tax categories
2. **Timeliness**: Monthly updates from Treasury within 48 hours
3. **Accuracy**: <1% variance between sources after reconciliation
4. **Reliability**: 99.9% uptime for scheduled collections

### 9. Risk Mitigation

| Risk | Mitigation Strategy |
|------|-------------------|
| ABS changes data format | AI-powered format detection, manual review queue |
| Large files timeout | Chunked downloads, CDN caching |
| API rate limits (future) | Implement backoff, queue management |
| Data reconciliation fails | Multiple validation layers, alerting |

### 10. Code Quality Standards

- Type hints throughout
- Comprehensive docstrings
- Unit tests for parsers
- Integration tests with sample data
- Performance benchmarks

## Conclusion

This design provides a robust, future-proof architecture for collecting taxation data. By building on existing EconCell infrastructure and planning for multiple data sources, we can fill the critical T component gap while maintaining system reliability and data quality.

The modular design allows incremental implementation while the AI integration provides resilience against format changes. This positions EconCell to offer comprehensive circular flow analysis including full fiscal policy modeling capabilities.
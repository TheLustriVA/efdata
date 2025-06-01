# G Component: Detail + Validation Strategy
**Date**: June 1, 2025  
**Proposed Approach**: ABS for Detail, RBA for Validation  

## Strategy Overview

Use ABS expenditure data as the **primary detailed source** while leveraging RBA data as a **sanity check and validation benchmark**.

## Data Characteristics

### ABS Expenditure (Primary Detail Source)
- **Records**: 25,380
- **Categories**: 14 detailed expenditure types
- **Period**: 2015-2025 (recent, high-quality)
- **Granularity**: Government function level (COFOG)
- **Total**: $75.9 million

### RBA Expenditure (Validation Benchmark)  
- **Records**: 1,726
- **Series**: 7 broader categories
- **Period**: 1959-2024 (long historical)
- **Granularity**: National accounts level
- **Total**: $277.3 million (longer period)

## Validation Analysis (2015-2024 Overlap)

| Year | RBA Total | ABS Total | Variance |
|------|-----------|-----------|----------|
| 2015 | $7.9B     | $4.4B     | -44.7%   |
| 2016 | $8.1B     | $5.9B     | -27.2%   |
| 2017 | $8.4B     | $6.1B     | -27.2%   |
| 2018 | $8.7B     | $6.4B     | -26.8%   |
| 2019 | $9.0B     | $6.7B     | -25.3%   |
| 2020 | $8.8B     | $7.4B     | -16.1%   |
| 2021 | $9.5B     | $8.1B     | -14.3%   |
| 2022 | $10.1B    | $8.5B     | -16.5%   |
| 2023 | $10.4B    | $8.7B     | -15.8%   |
| 2024 | $10.5B    | $10.9B    | **+3.7%** |

### Key Insights
1. **Consistent Pattern**: ABS typically 15-30% lower than RBA
2. **Convergence**: 2024 shows near-perfect alignment (+3.7%)
3. **Different Scope**: Likely different coverage definitions
4. **Reliable Variance**: Predictable difference enables validation

## Implementation Strategy

### 1. Primary Data Flow
```sql
-- Use ABS as primary source for detailed analysis
INSERT INTO rba_facts.fact_circular_flow (...)
SELECT ... FROM abs_staging.government_expenditure
-- Mark as is_primary_series = true
```

### 2. Validation Framework
```sql
-- Create validation view comparing sources
CREATE VIEW rba_analytics.g_component_validation AS
WITH abs_annual AS (
    SELECT year, SUM(value) as abs_total
    FROM rba_facts.fact_circular_flow 
    WHERE component_key = 5 AND source_key = 10  -- ABS G component
    GROUP BY year
),
rba_annual AS (
    SELECT year, SUM(value) as rba_total  
    FROM rba_facts.fact_circular_flow
    WHERE component_key = 5 AND source_key != 10  -- RBA G component
    GROUP BY year
)
SELECT 
    year,
    abs_total,
    rba_total,
    (abs_total - rba_total) / rba_total * 100 as variance_pct,
    CASE 
        WHEN ABS(variance_pct) > 50 THEN 'HIGH_VARIANCE'
        WHEN ABS(variance_pct) > 30 THEN 'MEDIUM_VARIANCE'  
        ELSE 'NORMAL_VARIANCE'
    END as alert_level
FROM abs_annual a
JOIN rba_annual r USING (year);
```

### 3. Automated Quality Checks
```sql
-- Daily validation function
CREATE FUNCTION validate_g_component_consistency()
RETURNS TABLE(check_name text, status text, details text)
AS $$
BEGIN
    -- Check if variance is within expected range (-40% to +10%)
    RETURN QUERY
    SELECT 
        'G Component Variance'::text,
        CASE WHEN variance_pct BETWEEN -40 AND 10 
             THEN 'PASS'::text 
             ELSE 'FAIL'::text 
        END,
        'Current variance: ' || variance_pct::text || '%'
    FROM rba_analytics.g_component_validation
    WHERE year = EXTRACT(YEAR FROM CURRENT_DATE);
END;
$$;
```

### 4. Circular Flow Integration
```sql
-- Modified view to use ABS as primary, RBA as fallback
CREATE OR REPLACE VIEW rba_analytics.v_circular_flow_balance AS
...
-- For G component: prioritize ABS (is_primary_series = true)
-- RBA serves as validation/historical context only
```

## Benefits of This Approach

### ✅ **Advantages**
1. **Rich Detail**: 14 ABS categories vs 7 RBA series
2. **Quality Assurance**: Automatic variance monitoring  
3. **Historical Context**: RBA provides long-term trends
4. **Operational**: ABS data more suited for government analysis
5. **Validation**: Built-in sanity checks against national accounts

### ⚠️ **Considerations**
1. **Coverage Differences**: Need to document scope variances
2. **Definition Alignment**: May require mapping between classification systems
3. **Temporal Gaps**: RBA has longer history, ABS more recent
4. **Maintenance**: Requires monitoring both data sources

## Implementation Timeline

### Phase 3A: ABS ETL (Primary)
- Load 25,380 ABS expenditure records as primary G component
- Mark as `is_primary_series = true`
- Create detailed expenditure analytics

### Phase 3B: Validation Setup  
- Create validation views and functions
- Set up variance monitoring alerts
- Document expected variance ranges

### Phase 3C: Integration Testing
- Test circular flow calculations with ABS primary data
- Validate equilibrium equations still balance
- Performance test with larger dataset

## Success Criteria

1. **Data Quality**: G component variance within -40% to +10% range
2. **Completeness**: All 14 ABS expenditure categories mapped
3. **Performance**: Circular flow calculations complete in <5 seconds
4. **Validation**: Automated alerts catch data quality issues
5. **Usability**: Detailed breakdowns available for analysis

This approach maximizes the value of both data sources while maintaining data quality and operational efficiency.
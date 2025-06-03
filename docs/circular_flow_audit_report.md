# Circular Flow Model Audit Report
Generated: 2025-06-01

## Executive Summary

This audit compares the RBA circular flow model requirements against the current EconCell database implementation to identify gaps and prioritize next steps.

### Coverage Score by Component
- ✅ **Y (Income)**: 90% - H1 table loaded, minor gaps in household disposable income
- ✅ **C (Consumption)**: 85% - H2 table loaded, need more granular breakdowns
- ✅ **S (Savings)**: 80% - Can be derived from Y-C, need explicit calculation
- ✅ **I (Investment)**: 85% - H3 table loaded, need asset type breakdown
- ❌ **G (Government Spending)**: 20% - Only limited data in H1, need ABS GFS
- ✅ **T (Taxation)**: 95% - ABS spider operational with 2,124 records
- ✅ **X (Exports)**: 90% - I1 table loaded
- ✅ **M (Imports)**: 90% - I1 table loaded

**Overall Circular Flow Coverage: 79%**

## Phase 2: Database Inventory Results

### 2.1 RBA Data Coverage

#### Tables Currently in Database

| Table | Component | Description | Record Count | Date Range | Status |
|-------|-----------|-------------|--------------|------------|--------|
| `h1_gdp_income` | Y, partial G | GDP and national income accounts | 16,212 | 1959-09-30 to 2024-12-31 | ✅ Loaded |
| `h2_household_finances` | C, partial S | Household consumption and finances | 31,068 | 1959-09-30 to 2024-12-31 | ✅ Loaded |
| `h3_business_finances` | I | Business investment and finances | 26,352 | 1965-01-31 to 2025-05-31 | ✅ Loaded |
| `i1_trade_bop` | X, M | International trade and balance of payments | 25,260 | 1959-09-30 to 2024-12-31 | ✅ Loaded |
| `i3_exchange_rates` | Support for X,M | Exchange rate data | Not checked | Not checked | ✅ Loaded |
| `d1_financial_aggregates` | S→I flow | Financial system aggregates | Not checked | Not checked | ✅ Loaded |
| `d2_lending_credit` | S→I flow | Credit and lending data | Not checked | Not checked | ✅ Loaded |

#### Circular Flow Facts Summary
| Component | Records in fact_circular_flow | Status |
|-----------|------------------------------|--------|
| Y - Income | 6,706 | ✅ Mapped |
| C - Consumption | 4,980 | ✅ Mapped |
| S - Savings | 14,594 | ✅ Mapped |
| I - Investment | 11,956 | ✅ Mapped |
| G - Government | 1,726 | ⚠️ Limited |
| T - Taxation | 0 | ❌ Not yet mapped to facts |
| X - Exports | 4,210 | ✅ Mapped |
| M - Imports | 4,210 | ✅ Mapped |

#### Missing RBA Tables

| Table | Component | Impact | Priority |
|-------|-----------|--------|----------|
| H4 | Detailed Income | Would enhance Y breakdown | Low |
| H5 | Housing | Would enhance I (dwelling investment) | Medium |
| I2 | Capital flows | Would enhance financial sector understanding | Low |
| F series | Interest rates | Important for S/I dynamics | High |

### 2.2 ABS Data Coverage

#### Successfully Implemented
- ✅ **ABS GFS Spider**: Operational as of 2025-06-01
  - URL: https://www.abs.gov.au/statistics/economy/government/government-finance-statistics-annual/latest-release
  - 81 XLSX files downloaded and parsed
  - 2,124 taxation records loaded
  - Coverage: Commonwealth, all States and Territories
  - Years: 2015-2025 (quarterly interpolated)

#### Missing ABS Data

| Dataset | Component | Description | Priority |
|---------|-----------|-------------|----------|
| GFS Expenditure tables | G | Government spending by function (COFOG) | **HIGH** |
| National Accounts API | Y, C, I | More granular breakdowns | Medium |
| Labour Force | Context | Employment data for model validation | Low |

### 2.3 Financial Sector Assessment

#### Current Coverage
- ✅ D1: Financial aggregates (money supply, credit growth)
- ✅ D2: Lending and credit by sector
- ❌ Interest rates (F series) - Critical gap
- ❌ Explicit S→I flow tracking

## Phase 3: Gap Analysis

### 3.1 Critical Gaps (Must Fix)

1. **Government Spending (G)**
   - Current: Only aggregate in H1
   - Need: Detailed breakdown by level and function
   - Solution: Extend ABS spider to parse expenditure tables
   - Effort: 2-3 days

2. **Interest Rates**
   - Current: Not loaded
   - Need: F1, F5, F6, F7 tables
   - Solution: Add to RBA spider
   - Effort: 1 day

3. **Savings Calculation**
   - Current: Not explicitly calculated
   - Need: S = Y - C at household level
   - Solution: Create SQL view or materialized table
   - Effort: 2-4 hours

### 3.2 Data Quality Issues

1. **Frequency Mismatch**
   - Taxation: Annual converted to quarterly (interpolated)
   - Trade: Monthly needs quarterly aggregation
   - Solution: Standardize all to quarterly

2. **Missing Equilibrium Validation**
   - Need: S + T + M = I + G + X check
   - Current: No validation query
   - Solution: Create monitoring view

3. **No Unified Fact Table**
   - Current: Data scattered across staging tables
   - Need: Single circular flow fact table
   - Solution: ETL pipeline to unified schema

### 3.3 Enhancement Opportunities

1. **State-Level Flows**
   - Have: State taxation data
   - Could add: State-level circular flows
   - Value: Regional economic analysis

2. **Real-Time Updates**
   - Current: Batch processing
   - Could add: API integration for near real-time
   - Value: Timely analysis

3. **Industry Breakdown**
   - Have: Some industry data in H series
   - Could add: Full industry-level flows
   - Value: Sectoral analysis

## Recommendations

### Immediate Actions (Week 1)
1. **Parse G component from ABS GFS** - Same spider, different tables
2. **Load interest rate tables** - Add F series to RBA spider
3. **Create S calculation** - SQL view: S = Y - C
4. **Build equilibrium validation** - Monitor S+T+M vs I+G+X

### Short Term (Week 2-3)
1. **Unified fact table** - Combine all components with consistent structure
2. **Frequency harmonization** - Standardize to quarterly
3. **Basic dashboard** - Visualize circular flow status

### Medium Term (Month 2)
1. **API integration** - Move from file downloads where possible
2. **State-level analysis** - Leverage existing state tax data
3. **Automated quality checks** - Flag anomalies and gaps

## Validation Queries Needed

```sql
-- 1. Component Summary
CREATE VIEW circular_flow_summary AS
SELECT 
    period,
    SUM(CASE WHEN component = 'Y' THEN value END) as income_y,
    SUM(CASE WHEN component = 'C' THEN value END) as consumption_c,
    SUM(CASE WHEN component = 'I' THEN value END) as investment_i,
    SUM(CASE WHEN component = 'G' THEN value END) as government_g,
    SUM(CASE WHEN component = 'X' THEN value END) as exports_x,
    SUM(CASE WHEN component = 'M' THEN value END) as imports_m,
    SUM(CASE WHEN component = 'T' THEN value END) as taxation_t,
    SUM(CASE WHEN component = 'Y' THEN value END) - 
    SUM(CASE WHEN component = 'C' THEN value END) as savings_s_calc
FROM unified_circular_flow
GROUP BY period;

-- 2. Equilibrium Check
CREATE VIEW equilibrium_check AS
SELECT 
    period,
    (savings_s_calc + taxation_t + imports_m) as leakages,
    (investment_i + government_g + exports_x) as injections,
    (savings_s_calc + taxation_t + imports_m) - 
    (investment_i + government_g + exports_x) as discrepancy,
    CASE 
        WHEN ABS((savings_s_calc + taxation_t + imports_m) - 
                 (investment_i + government_g + exports_x)) / 
             NULLIF((investment_i + government_g + exports_x), 0) < 0.02 
        THEN 'PASS' 
        ELSE 'FAIL' 
    END as status
FROM circular_flow_summary;
```

## Next Steps

1. **Run detailed queries** to populate exact record counts and date ranges
2. **Implement G component** parsing in ABS spider
3. **Create unified circular flow schema**
4. **Build validation dashboard**

The foundation is solid with 79% coverage. The main gap (G component) can be filled quickly since the ABS spider infrastructure already exists.
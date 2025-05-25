# RBA Circular Flow Model to CSV Dataset Mapping Analysis

**Analysis Date:** 2025-05-25  
**Total Datasets Analyzed:** 193 CSV files  
**Circular Flow Components:** 8 core variables (Y, C, S, I, G, T, X, M)  
**Methodology:** Systematic cross-reference analysis with hybrid database architecture

## Executive Summary

This analysis provides a comprehensive mapping between the Reserve Bank of Australia's circular flow model components and the available 193 CSV datasets. The analysis reveals strong coverage for most core components, with some critical gaps identified in government sector data (T, G) and specific limitations in household savings flow tracking.

### Key Findings
- **Complete Coverage:** 6 of 8 components have primary dataset mappings
- **Partial Coverage:** 2 components require multiple dataset integration
- **Critical Gaps:** Limited granular government finance data in CSV format
- **High Quality:** H-series and I-series provide robust quarterly data for core flows

## Phase 1: Systematic Component Mapping

### 1.1 Component Y (Household Income)

**Economic Definition:** Money received by households (wages, rent, interest, transfers)

**Primary CSV Mappings:**
| Dataset | RBA Table | Description | Frequency | Key Variables |
|---------|-----------|-------------|-----------|---------------|
| `h2-data.csv` | H2 | Household Finances | Quarterly | Household disposable income, compensation of employees |
| `h1-data.csv` | H1 | GDP & Income | Quarterly | Gross domestic income, per capita measures |

**Variable Mapping:**
- **Gross Household Disposable Income**: H2 series, quarterly frequency
- **Compensation of Employees**: H1/H2 cross-reference for wage income component
- **Property Income**: H2 series covering rent, dividends, interest received

**Data Quality Assessment:**
- **Completeness**: ✅ High - consistent quarterly series
- **Temporal Coverage**: ✅ Extensive historical data
- **Definition Consistency**: ✅ Aligns with RBA circular flow framework
- **Integration Potential**: ✅ Strong linkage to consumption (C) flows

### 1.2 Component C (Household Consumption)

**Economic Definition:** Purchase of goods and services by households from firms

**Primary CSV Mappings:**
| Dataset | RBA Table | Description | Frequency | Key Variables |
|---------|-----------|-------------|-----------|---------------|
| `h2-data.csv` | H2 | Household Finances | Quarterly | Household final consumption expenditure |
| `c1-data.csv` | C1 | Credit & Charge Cards | Monthly | Transaction values by card type (61 variables) |
| `c2-data.csv` | C2 | Debit Cards | Monthly | Electronic payment flows |

**Variable Mapping:**
- **Household Final Consumption Expenditure (HFCE)**: H2 primary measure
- **Payment System Validation**: C1/C2 monthly transaction flows for consistency checks
- **Consumption Categories**: H2 provides aggregate, C-series provides payment method breakdown

**Data Quality Assessment:**
- **Completeness**: ✅ High - quarterly aggregates with monthly payment validation
- **Temporal Coverage**: ✅ Long quarterly series, shorter monthly payment data
- **Definition Consistency**: ✅ HFCE standard definition maintained
- **Integration Potential**: ✅ Excellent - direct flow from Y through expenditure multiplier

### 1.3 Component S (Household Savings)

**Economic Definition:** Income not spent on consumption, channeled to financial sector

**Primary CSV Mappings:**
| Dataset | RBA Table | Description | Frequency | Key Variables |
|---------|-----------|-------------|-----------|---------------|
| `h2-data.csv` | H2 | Household Finances | Quarterly | Household net saving, saving ratio |
| `d1-data.csv` | D1 | Growth in Financial Aggregates | Monthly | Broad money growth, credit flows |
| `d2-data.csv` | D2 | Lending & Credit Aggregates | Monthly | Credit stock levels by category |

**Variable Mapping:**
- **Household Net Saving**: H2 direct measure (Y - C - T)
- **Household Saving Ratio**: H2 percentage of disposable income
- **Financial Flow Validation**: D1/D2 credit aggregates for S→I transmission

**Data Quality Assessment:**
- **Completeness**: ✅ High - direct calculation from income/expenditure identity
- **Temporal Coverage**: ✅ Consistent quarterly measurement
- **Definition Consistency**: ✅ Standard national accounts definition
- **Integration Potential**: ⚠️ Medium - requires financial sector intermediation modeling

### 1.4 Component I (Private Investment)

**Economic Definition:** Expenditure by firms on capital goods, financed through financial sector

**Primary CSV Mappings:**
| Dataset | RBA Table | Description | Frequency | Key Variables |
|---------|-----------|-------------|-----------|---------------|
| `h3-data.csv` | H3 | Business Finances | Quarterly | Business investment, capital formation |
| `h1-data.csv` | H1 | GDP & Income | Quarterly | Gross fixed capital formation components |
| `d2-data.csv` | D2 | Lending & Credit Aggregates | Monthly | Business credit for investment financing |

**Variable Mapping:**
- **Gross Fixed Capital Formation (Private)**: H1/H3 primary measures
- **Business Investment by Type**: H3 asset category breakdowns
- **Investment Financing**: D2 business credit aggregates

**Data Quality Assessment:**
- **Completeness**: ✅ High - comprehensive GFCF measurement
- **Temporal Coverage**: ✅ Long quarterly series with monthly financing data
- **Definition Consistency**: ✅ Standard GFCF definitions maintained
- **Integration Potential**: ✅ Excellent - clear S→I transmission via financial sector

### 1.5 Component G (Government Expenditure)

**Economic Definition:** Government spending on goods, services, and transfers

**Primary CSV Mappings:**
| Dataset | RBA Table | Description | Frequency | Key Variables |
|---------|-----------|-------------|-----------|---------------|
| `h1-data.csv` | H1 | GDP & Income | Quarterly | Government final consumption expenditure |
| `a1-data.csv` | A1 | RBA Balance Sheet | Weekly | Government deposits, fiscal operations |

**Variable Mapping:**
- **Government Final Consumption Expenditure (GFCE)**: H1 aggregate measure
- **Government Capital Formation**: H1 public investment component
- **Fiscal Operations**: A1 weekly government cash flows

**Data Quality Assessment:**
- **Completeness**: ⚠️ Medium - aggregate measures available, limited detail
- **Temporal Coverage**: ✅ Consistent quarterly GFCE data
- **Definition Consistency**: ✅ Standard national accounts treatment
- **Integration Potential**: ⚠️ Medium - requires external GFS data for detailed analysis

**Critical Gap Identified:** Limited granular government expenditure by function (COFOG) or level of government in available CSV datasets.

### 1.6 Component T (Taxation)

**Economic Definition:** Money paid by households and firms to government sector

**Primary CSV Mappings:**
| Dataset | RBA Table | Description | Frequency | Key Variables |
|---------|-----------|-------------|-----------|---------------|
| `a1-data.csv` | A1 | RBA Balance Sheet | Weekly | Government deposits (proxy for tax receipts) |

**Variable Mapping:**
- **Government Deposits**: A1 weekly flows (indirect taxation measure)
- **Tax Revenue Components**: ❌ Not directly available in CSV format

**Data Quality Assessment:**
- **Completeness**: ❌ Low - only indirect measures available
- **Temporal Coverage**: ✅ Weekly government cash flow data
- **Definition Consistency**: ⚠️ Proxy measures only
- **Integration Potential**: ❌ Poor - requires external Government Finance Statistics

**Critical Gap Identified:** No direct CSV datasets contain detailed taxation revenue by type (income tax, GST, excise, etc.). This represents a significant limitation for circular flow modeling.

### 1.7 Component X (Exports)

**Economic Definition:** Goods and services produced domestically and sold to foreign residents

**Primary CSV Mappings:**
| Dataset | RBA Table | Description | Frequency | Key Variables |
|---------|-----------|-------------|-----------|---------------|
| `i1-data.csv` | I1 | Trade & Balance of Payments | Quarterly | Exports by category, trade balance (20 variables) |
| `i3-data.csv` | I3 | Exchange Rates | Daily | Trade-weighted index, bilateral rates affecting export competitiveness |

**Variable Mapping:**
- **Exports of Goods and Services**: I1 comprehensive measurement
- **Export Categories**: I1 goods/services breakdown
- **Exchange Rate Impact**: I3 daily competitiveness measures

**Data Quality Assessment:**
- **Completeness**: ✅ High - comprehensive trade statistics
- **Temporal Coverage**: ✅ Long quarterly series with daily FX context
- **Definition Consistency**: ✅ Standard balance of payments definitions
- **Integration Potential**: ✅ Excellent - clear international sector flows

### 1.8 Component M (Imports)

**Economic Definition:** Goods and services produced overseas and purchased by domestic residents

**Primary CSV Mappings:**
| Dataset | RBA Table | Description | Frequency | Key Variables |
|---------|-----------|-------------|-----------|---------------|
| `i1-data.csv` | I1 | Trade & Balance of Payments | Quarterly | Imports by category, trade balance |
| `i3-data.csv` | I3 | Exchange Rates | Daily | Exchange rates affecting import costs |

**Variable Mapping:**
- **Imports of Goods and Services**: I1 comprehensive measurement
- **Import Categories**: I1 goods/services breakdown
- **Exchange Rate Impact**: I3 daily cost measures

**Data Quality Assessment:**
- **Completeness**: ✅ High - comprehensive trade statistics
- **Temporal Coverage**: ✅ Long quarterly series with daily FX context
- **Definition Consistency**: ✅ Standard balance of payments definitions
- **Integration Potential**: ✅ Excellent - clear leakage from domestic circular flow

## Phase 2: Data-Component Alignment Summary

### 2.1 Primary Mapping Matrix

| Component | Primary Dataset(s) | Secondary Dataset(s) | Coverage Quality | Integration Complexity |
|-----------|-------------------|---------------------|------------------|----------------------|
| **Y (Income)** | h2-data.csv | h1-data.csv | ✅ High | 🟢 Low |
| **C (Consumption)** | h2-data.csv | c1-data.csv, c2-data.csv | ✅ High | 🟢 Low |
| **S (Savings)** | h2-data.csv | d1-data.csv, d2-data.csv | ✅ High | 🟡 Medium |
| **I (Investment)** | h3-data.csv | h1-data.csv, d2-data.csv | ✅ High | 🟡 Medium |
| **G (Government)** | h1-data.csv | a1-data.csv | ⚠️ Medium | 🟡 Medium |
| **T (Taxation)** | a1-data.csv | None available | ❌ Low | 🔴 High |
| **X (Exports)** | i1-data.csv | i3-data.csv | ✅ High | 🟢 Low |
| **M (Imports)** | i1-data.csv | i3-data.csv | ✅ High | 🟢 Low |

### 2.2 Frequency Harmonization Requirements

| Component | Primary Frequency | Secondary Frequency | Harmonization Need |
|-----------|------------------|--------------------|--------------------|
| Y, C, S | Quarterly | Monthly (payment data) | 🟡 Moderate |
| I | Quarterly | Monthly (credit data) | 🟡 Moderate |
| G | Quarterly | Weekly (cash flows) | 🟡 Moderate |
| T | Weekly (proxy only) | N/A | 🔴 High |
| X, M | Quarterly | Daily (FX rates) | 🟢 Low |

## Phase 3: Ambiguity and Gap Documentation

### 3.1 Critical Data Gaps

#### Government Sector Limitations
- **Missing T (Taxation)**: No detailed tax revenue by type in CSV format
- **Limited G (Government)**: No expenditure by function or level of government
- **Resolution**: Requires external ABS Government Finance Statistics integration

#### Financial Sector Flow Tracking
- **S→I Transmission**: Limited visibility into financial intermediation process
- **Credit Channel**: D-series provides aggregates but limited flow dynamics
- **Resolution**: Enhanced financial flow modeling using B-series institutional data

### 3.2 Mapping Ambiguities

#### Multiple Source Options
- **Investment (I)**: Available in H1 (GDP aggregates) and H3 (business finances)
  - **Recommendation**: Use H3 as primary (business perspective), H1 for validation
- **Income (Y)**: Components split across H1 (GDP income) and H2 (household accounts)
  - **Recommendation**: Use H2 as primary (household perspective), H1 for cross-validation

#### Definition Consistency Issues
- **Current vs Chain Volume**: All major components available in both price bases
  - **Recommendation**: Maintain parallel real/nominal measurement capability
- **Seasonal Adjustment**: Most series available both adjusted and original
  - **Recommendation**: Use seasonally adjusted for modeling, original for validation

### 3.3 Integration Challenges

#### Temporal Alignment
- **Primary Challenge**: Quarterly economic data vs monthly/daily financial indicators
- **Impact**: Medium - requires temporal aggregation/interpolation procedures
- **Mitigation**: Develop quarterly average/end-period conventions

#### Unit Standardization  
- **Primary Challenge**: Mix of $ millions, percentages, indices across datasets
- **Impact**: Low - clear unit documentation available
- **Mitigation**: Systematic unit conversion procedures in ETL process

## Phase 4: Database Schema Recommendations

### 4.1 Staging Layer Design

```sql
-- Raw CSV import staging tables
CREATE SCHEMA rba_staging;

-- Example: H2 Household Finances staging
CREATE TABLE rba_staging.h2_household_finances (
    extract_date DATE DEFAULT CURRENT_DATE,
    series_id VARCHAR(20),
    series_description TEXT,
    period_date DATE,
    value DECIMAL(15,2),
    unit VARCHAR(20),
    frequency VARCHAR(10),
    adjustment_type VARCHAR(20),
    CONSTRAINT pk_h2_staging PRIMARY KEY (extract_date, series_id, period_date)
);

-- Create staging tables for all primary component datasets
-- h1_gdp_income, h3_business_finances, i1_trade_bop, d1_financial_aggregates, etc.
```

### 4.2 Dimension Layer Design

```sql
-- Core dimensional structure
CREATE SCHEMA rba_dimensions;

-- Time dimension with multiple frequency support
CREATE TABLE rba_dimensions.dim_time (
    time_key SERIAL PRIMARY KEY,
    date_value DATE NOT NULL,
    year INTEGER,
    quarter INTEGER,
    month INTEGER,
    frequency VARCHAR(10), -- 'Daily', 'Monthly', 'Quarterly'
    is_quarter_end BOOLEAN,
    is_year_end BOOLEAN
);

-- Circular flow component dimension
CREATE TABLE rba_dimensions.dim_circular_flow_component (
    component_key SERIAL PRIMARY KEY,
    component_code CHAR(1), -- Y, C, S, I, G, T, X, M
    component_name VARCHAR(50),
    component_description TEXT,
    economic_sector VARCHAR(20), -- 'Household', 'Business', 'Government', 'External'
    flow_type VARCHAR(15) -- 'Income', 'Expenditure', 'Leakage', 'Injection'
);

-- Data source dimension for traceability
CREATE TABLE rba_dimensions.dim_data_source (
    source_key SERIAL PRIMARY KEY,
    rba_table_code VARCHAR(10), -- H1, H2, I1, etc.
    csv_filename VARCHAR(50),
    table_description TEXT,
    frequency VARCHAR(10),
    update_frequency VARCHAR(20)
);

-- Unit and measurement dimension
CREATE TABLE rba_dimensions.dim_measurement (
    measurement_key SERIAL PRIMARY KEY,
    unit_type VARCHAR(20), -- 'Currency', 'Percentage', 'Index', 'Count'
    unit_description VARCHAR(50), -- '$ million', 'Per cent', 'Index', 'Number'
    price_basis VARCHAR(20), -- 'Current Prices', 'Chain Volume', 'Nominal'
    adjustment_type VARCHAR(20) -- 'Seasonally Adjusted', 'Original', 'Trend'
);
```

### 4.3 Fact Table Design

```sql
-- Core circular flow measurements
CREATE SCHEMA rba_facts;

CREATE TABLE rba_facts.fact_circular_flow (
    time_key INTEGER REFERENCES rba_dimensions.dim_time(time_key),
    component_key INTEGER REFERENCES rba_dimensions.dim_circular_flow_component(component_key),
    source_key INTEGER REFERENCES rba_dimensions.dim_data_source(source_key),
    measurement_key INTEGER REFERENCES rba_dimensions.dim_measurement(measurement_key),
    value DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_circular_flow PRIMARY KEY (time_key, component_key, source_key, measurement_key)
);

-- Supporting financial flows fact table
CREATE TABLE rba_facts.fact_financial_flows (
    time_key INTEGER REFERENCES rba_dimensions.dim_time(time_key),
    flow_type VARCHAR(20), -- 'Credit_Growth', 'Money_Supply', 'Interest_Rate'
    source_key INTEGER REFERENCES rba_dimensions.dim_data_source(source_key),
    measurement_key INTEGER REFERENCES rba_dimensions.dim_measurement(measurement_key),
    value DECIMAL(15,4), -- Higher precision for rates and ratios
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_financial_flows PRIMARY KEY (time_key, flow_type, source_key, measurement_key)
);
```

### 4.4 Integration Views

```sql
-- Analytical views for circular flow analysis
CREATE SCHEMA rba_analytics;

-- Core circular flow balance validation view
CREATE VIEW rba_analytics.v_circular_flow_balance AS
WITH quarterly_components AS (
    SELECT 
        t.date_value,
        c.component_code,
        AVG(f.value) as avg_value
    FROM rba_facts.fact_circular_flow f
    JOIN rba_dimensions.dim_time t ON f.time_key = t.time_key
    JOIN rba_dimensions.dim_circular_flow_component c ON f.component_key = c.component_key
    JOIN rba_dimensions.dim_measurement m ON f.measurement_key = m.measurement_key
    WHERE t.frequency = 'Quarterly'
      AND m.price_basis = 'Current Prices'
      AND m.adjustment_type = 'Seasonally Adjusted'
    GROUP BY t.date_value, c.component_code
)
SELECT 
    date_value,
    MAX(CASE WHEN component_code = 'S' THEN avg_value END) as savings,
    MAX(CASE WHEN component_code = 'T' THEN avg_value END) as taxation,
    MAX(CASE WHEN component_code = 'M' THEN avg_value END) as imports,
    MAX(CASE WHEN component_code = 'I' THEN avg_value END) as investment,
    MAX(CASE WHEN component_code = 'G' THEN avg_value END) as govt_expenditure,
    MAX(CASE WHEN component_code = 'X' THEN avg_value END) as exports,
    -- Calculate circular flow identity: S + T + M = I + G + X
    (MAX(CASE WHEN component_code = 'S' THEN avg_value END) + 
     MAX(CASE WHEN component_code = 'T' THEN avg_value END) + 
     MAX(CASE WHEN component_code = 'M' THEN avg_value END)) as leakages,
    (MAX(CASE WHEN component_code = 'I' THEN avg_value END) + 
     MAX(CASE WHEN component_code = 'G' THEN avg_value END) + 
     MAX(CASE WHEN component_code = 'X' THEN avg_value END)) as injections
FROM quarterly_components
GROUP BY date_value
ORDER BY date_value;

-- Component-specific analytical views
CREATE VIEW rba_analytics.v_household_flows AS
SELECT 
    t.date_value,
    MAX(CASE WHEN c.component_code = 'Y' THEN f.value END) as income,
    MAX(CASE WHEN c.component_code = 'C' THEN f.value END) as consumption,
    MAX(CASE WHEN c.component_code = 'S' THEN f.value END) as savings,
    -- Calculate household accounting identity: Y = C + S + T_household
    MAX(CASE WHEN c.component_code = 'Y' THEN f.value END) - 
    MAX(CASE WHEN c.component_code = 'C' THEN f.value END) - 
    MAX(CASE WHEN c.component_code = 'S' THEN f.value END) as implied_household_taxes
FROM rba_facts.fact_circular_flow f
JOIN rba_dimensions.dim_time t ON f.time_key = t.time_key
JOIN rba_dimensions.dim_circular_flow_component c ON f.component_key = c.component_key
JOIN rba_dimensions.dim_measurement m ON f.measurement_key = m.measurement_key
WHERE c.component_code IN ('Y', 'C', 'S')
  AND t.frequency = 'Quarterly'
  AND m.price_basis = 'Current Prices'
  AND m.adjustment_type = 'Seasonally Adjusted'
GROUP BY t.date_value
ORDER BY t.date_value;
```

### 4.5 Indexing Strategy

```sql
-- Temporal analysis optimization
CREATE INDEX idx_fact_circular_flow_time ON rba_facts.fact_circular_flow(time_key);
CREATE INDEX idx_fact_circular_flow_component ON rba_facts.fact_circular_flow(component_key);
CREATE INDEX idx_fact_circular_flow_time_component ON rba_facts.fact_circular_flow(time_key, component_key);

-- Source traceability
CREATE INDEX idx_fact_circular_flow_source ON rba_facts.fact_circular_flow(source_key);

-- Time dimension optimization for quarterly analysis
CREATE INDEX idx_dim_time_quarter ON rba_dimensions.dim_time(year, quarter) WHERE frequency = 'Quarterly';
CREATE INDEX idx_dim_time_date ON rba_dimensions.dim_time(date_value);

-- Consider partitioning for large datasets
CREATE TABLE rba_facts.fact_circular_flow_y2024 PARTITION OF rba_facts.fact_circular_flow
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

## Implementation Roadmap

### Phase 1: Foundation Setup (Week 1-2)
1. **Database Schema Creation**: Implement staging, dimension, and fact table structures
2. **ETL Framework**: Develop CSV import procedures for primary datasets
3. **Data Quality Checks**: Implement validation routines for circular flow identity

### Phase 2: Core Component Integration (Week 3-4)  
1. **High-Quality Components**: Integrate Y, C, S, I, X, M from H-series and I-series
2. **Financial Flow Linkages**: Connect D-series data for S→I transmission modeling
3. **Initial Analytics**: Deploy circular flow balance validation views

### Phase 3: Government Sector Enhancement (Week 5-6)
1. **External Data Integration**: Incorporate ABS Government Finance Statistics for T, G
2. **Proxy Validation**: Cross-check government cash flows (A1) against external sources
3. **Complete Flow Modeling**: Achieve full circular flow identity validation

### Phase 4: Performance Optimization (Week 7-8)
1. **Indexing Refinement**: Optimize for common analytical query patterns
2. **Partitioning Strategy**: Implement temporal partitioning for historical data
3. **Analytical Views**: Expand view library for macroeconomic analysis

## Conclusion

This analysis demonstrates that the available RBA CSV datasets provide strong foundation coverage for 6 of 8 circular flow components, with high-quality quarterly data for the core economic flows. The critical gaps in taxation (T) and detailed government expenditure (G) data can be addressed through external integration with ABS Government Finance Statistics.

The recommended hybrid database architecture provides both data traceability (staging layer) and analytical power (dimensional modeling) while maintaining the flexibility to incorporate additional data sources as they become available.

**Next Steps**: Proceed with database schema implementation and ETL development for the high-coverage components, followed by external data integration for complete circular flow modeling capability.
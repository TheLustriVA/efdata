-- =====================================================
-- RBA Circular Flow Model - PostgreSQL Database Schema
-- =====================================================
-- 
-- This DDL implements the hybrid database architecture for mapping
-- RBA circular flow components to CSV datasets as outlined in the
-- systematic cross-reference analysis.
--
-- Architecture: Staging -> Dimensions -> Facts -> Analytics
-- Target: PostgreSQL 12+
-- Date: 2025-05-25
-- =====================================================

-- =====================================================
-- SCHEMA CREATION
-- =====================================================

-- Drop existing schemas if they exist (for development)
-- WARNING: Uncomment only for development environments
DROP SCHEMA IF EXISTS rba_staging CASCADE;
DROP SCHEMA IF EXISTS rba_dimensions CASCADE;
DROP SCHEMA IF EXISTS rba_facts CASCADE;
DROP SCHEMA IF EXISTS rba_analytics CASCADE;

CREATE SCHEMA IF NOT EXISTS rba_staging;
CREATE SCHEMA IF NOT EXISTS rba_dimensions;
CREATE SCHEMA IF NOT EXISTS rba_facts;
CREATE SCHEMA IF NOT EXISTS rba_analytics;

-- Set search path for convenience
SET search_path = rba_staging, rba_dimensions, rba_facts, rba_analytics, public;

-- =====================================================
-- STAGING LAYER - Raw CSV Import Tables
-- =====================================================

-- H1: GDP & Income (Component Y - Income, plus GDP aggregates)
CREATE TABLE rba_staging.h1_gdp_income (
    extract_date DATE DEFAULT CURRENT_DATE,
    series_id VARCHAR(20) NOT NULL,
    series_description TEXT,
    period_date DATE NOT NULL,
    value DECIMAL(15,2),
    unit VARCHAR(30),
    frequency VARCHAR(15),
    adjustment_type VARCHAR(25),
    price_basis VARCHAR(25),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_h1_staging PRIMARY KEY (extract_date, series_id, period_date)
);

-- H2: Household Finances (Components Y, C, S - Primary household flows)
CREATE TABLE rba_staging.h2_household_finances (
    extract_date DATE DEFAULT CURRENT_DATE,
    series_id VARCHAR(20) NOT NULL,
    series_description TEXT,
    period_date DATE NOT NULL,
    value DECIMAL(15,2),
    unit VARCHAR(30),
    frequency VARCHAR(15),
    adjustment_type VARCHAR(25),
    price_basis VARCHAR(25),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_h2_staging PRIMARY KEY (extract_date, series_id, period_date)
);

-- H3: Business Finances (Component I - Investment)
CREATE TABLE rba_staging.h3_business_finances (
    extract_date DATE DEFAULT CURRENT_DATE,
    series_id VARCHAR(20) NOT NULL,
    series_description TEXT,
    period_date DATE NOT NULL,
    value DECIMAL(15,2),
    unit VARCHAR(30),
    frequency VARCHAR(15),
    adjustment_type VARCHAR(25),
    price_basis VARCHAR(25),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_h3_staging PRIMARY KEY (extract_date, series_id, period_date)
);

-- I1: Trade & Balance of Payments (Components X, M - External sector)
CREATE TABLE rba_staging.i1_trade_bop (
    extract_date DATE DEFAULT CURRENT_DATE,
    series_id VARCHAR(20) NOT NULL,
    series_description TEXT,
    period_date DATE NOT NULL,
    value DECIMAL(15,2),
    unit VARCHAR(30),
    frequency VARCHAR(15),
    adjustment_type VARCHAR(25),
    price_basis VARCHAR(25),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_i1_staging PRIMARY KEY (extract_date, series_id, period_date)
);

-- D1: Growth in Financial Aggregates (Supporting S, I flows)
CREATE TABLE rba_staging.d1_financial_aggregates (
    extract_date DATE DEFAULT CURRENT_DATE,
    series_id VARCHAR(20) NOT NULL,
    series_description TEXT,
    period_date DATE NOT NULL,
    value DECIMAL(15,4), -- Higher precision for growth rates
    unit VARCHAR(30),
    frequency VARCHAR(15),
    adjustment_type VARCHAR(25),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_d1_staging PRIMARY KEY (extract_date, series_id, period_date)
);

-- D2: Lending & Credit Aggregates (Supporting S→I transmission)
CREATE TABLE rba_staging.d2_lending_credit (
    extract_date DATE DEFAULT CURRENT_DATE,
    series_id VARCHAR(20) NOT NULL,
    series_description TEXT,
    period_date DATE NOT NULL,
    value DECIMAL(15,2),
    unit VARCHAR(30),
    frequency VARCHAR(15),
    adjustment_type VARCHAR(25),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_d2_staging PRIMARY KEY (extract_date, series_id, period_date)
);

-- A1: RBA Balance Sheet (Components G, T - Government sector proxy)
CREATE TABLE rba_staging.a1_rba_balance_sheet (
    extract_date DATE DEFAULT CURRENT_DATE,
    series_id VARCHAR(20) NOT NULL,
    series_description TEXT,
    period_date DATE NOT NULL,
    value DECIMAL(15,2),
    unit VARCHAR(30),
    frequency VARCHAR(15),
    adjustment_type VARCHAR(25),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_a1_staging PRIMARY KEY (extract_date, series_id, period_date)
);

-- I3: Exchange Rates (Supporting X, M analysis)
CREATE TABLE rba_staging.i3_exchange_rates (
    extract_date DATE DEFAULT CURRENT_DATE,
    series_id VARCHAR(20) NOT NULL,
    series_description TEXT,
    period_date DATE NOT NULL,
    value DECIMAL(10,6), -- High precision for exchange rates
    unit VARCHAR(30),
    frequency VARCHAR(15),
    adjustment_type VARCHAR(25),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_i3_staging PRIMARY KEY (extract_date, series_id, period_date)
);

-- C1: Credit & Charge Cards (Supporting C - Consumption validation)
CREATE TABLE rba_staging.c1_credit_cards (
    extract_date DATE DEFAULT CURRENT_DATE,
    series_id VARCHAR(20) NOT NULL,
    series_description TEXT,
    period_date DATE NOT NULL,
    value DECIMAL(15,2),
    unit VARCHAR(30),
    frequency VARCHAR(15),
    adjustment_type VARCHAR(25),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_c1_staging PRIMARY KEY (extract_date, series_id, period_date)
);

-- =====================================================
-- DIMENSION LAYER - Reference Data
-- =====================================================

-- Time dimension supporting multiple frequencies
CREATE TABLE rba_dimensions.dim_time (
    time_key SERIAL PRIMARY KEY,
    date_value DATE UNIQUE NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER CHECK (quarter BETWEEN 1 AND 4),
    month INTEGER CHECK (month BETWEEN 1 AND 12),
    day_of_year INTEGER CHECK (day_of_year BETWEEN 1 AND 366),
    frequency VARCHAR(15), -- 'Daily', 'Weekly', 'Monthly', 'Quarterly', 'Annual'
    is_quarter_end BOOLEAN DEFAULT FALSE,
    is_year_end BOOLEAN DEFAULT FALSE,
    is_month_end BOOLEAN DEFAULT FALSE,
    quarter_label VARCHAR(10), -- '2024Q1', '2024Q2', etc.
    fiscal_year INTEGER, -- Australian fiscal year (July-June)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create time dimension helper function
CREATE OR REPLACE FUNCTION rba_dimensions.populate_time_dimension(
    start_date DATE,
    end_date DATE
) RETURNS INTEGER AS $$
DECLARE
    loop_date DATE;
    record_count INTEGER := 0;
BEGIN
    loop_date := start_date;
    
    WHILE loop_date <= end_date LOOP
        INSERT INTO rba_dimensions.dim_time (
            date_value,
            year,
            quarter,
            month,
            day_of_year,
            is_quarter_end,
            is_year_end,
            is_month_end,
            quarter_label,
            fiscal_year
        ) VALUES (
            loop_date,
            EXTRACT(YEAR FROM loop_date),
            EXTRACT(QUARTER FROM loop_date),
            EXTRACT(MONTH FROM loop_date),
            EXTRACT(DOY FROM loop_date),
            loop_date = (DATE_TRUNC('quarter', loop_date) + INTERVAL '3 months - 1 day')::DATE,
            loop_date = (DATE_TRUNC('year', loop_date) + INTERVAL '12 months - 1 day')::DATE,
            loop_date = (DATE_TRUNC('month', loop_date) + INTERVAL '1 month - 1 day')::DATE,
            EXTRACT(YEAR FROM loop_date)::TEXT || 'Q' || EXTRACT(QUARTER FROM loop_date)::TEXT,
            CASE 
                WHEN EXTRACT(MONTH FROM loop_date) >= 7 
                THEN EXTRACT(YEAR FROM loop_date) + 1
                ELSE EXTRACT(YEAR FROM loop_date)
            END
        ) ON CONFLICT (date_value) DO NOTHING;
        
        loop_date := loop_date + INTERVAL '1 day';
        record_count := record_count + 1;
    END LOOP;
    
    RETURN record_count;
END;
$$ LANGUAGE plpgsql;

-- Circular flow component dimension
CREATE TABLE rba_dimensions.dim_circular_flow_component (
    component_key SERIAL PRIMARY KEY,
    component_code CHAR(1) UNIQUE NOT NULL, -- Y, C, S, I, G, T, X, M
    component_name VARCHAR(50) NOT NULL,
    component_description TEXT,
    economic_sector VARCHAR(20) NOT NULL, -- 'Household', 'Business', 'Government', 'External', 'Financial'
    flow_type VARCHAR(15) NOT NULL, -- 'Income', 'Expenditure', 'Leakage', 'Injection'
    accounting_identity_side VARCHAR(10), -- 'Leakage', 'Injection' for S+T+M = I+G+X
    is_core_component BOOLEAN DEFAULT TRUE,
    display_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert core circular flow components
INSERT INTO rba_dimensions.dim_circular_flow_component 
(component_code, component_name, component_description, economic_sector, flow_type, accounting_identity_side, display_order) VALUES
('Y', 'Household Income', 'Money received by households (wages, rent, interest, transfers)', 'Household', 'Income', NULL, 1),
('C', 'Consumption', 'Purchase of goods and services by households from firms', 'Household', 'Expenditure', NULL, 2),
('S', 'Savings', 'Income not spent on consumption, channeled to financial sector', 'Household', 'Leakage', 'Leakage', 3),
('I', 'Investment', 'Expenditure by firms on capital goods, financed through financial sector', 'Business', 'Injection', 'Injection', 4),
('G', 'Government Expenditure', 'Government spending on goods, services, and transfers', 'Government', 'Injection', 'Injection', 5),
('T', 'Taxation', 'Money paid by households and firms to government sector', 'Government', 'Leakage', 'Leakage', 6),
('X', 'Exports', 'Goods and services produced domestically and sold to foreign residents', 'External', 'Injection', 'Injection', 7),
('M', 'Imports', 'Goods and services produced overseas and purchased by domestic residents', 'External', 'Leakage', 'Leakage', 8);

-- Data source dimension for traceability
CREATE TABLE rba_dimensions.dim_data_source (
    source_key SERIAL PRIMARY KEY,
    rba_table_code VARCHAR(10) NOT NULL, -- H1, H2, I1, etc.
    csv_filename VARCHAR(50),
    table_description TEXT,
    data_category VARCHAR(30), -- 'National Accounts', 'International Trade', etc.
    primary_frequency VARCHAR(15),
    update_frequency VARCHAR(25),
    data_provider VARCHAR(10) DEFAULT 'RBA',
    is_primary_source BOOLEAN DEFAULT TRUE,
    coverage_start_date DATE,
    coverage_end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_source_table_code UNIQUE (rba_table_code)
);

-- Insert primary data sources
INSERT INTO rba_dimensions.dim_data_source 
(rba_table_code, csv_filename, table_description, data_category, primary_frequency, update_frequency) VALUES
('H1', 'h1-data.csv', 'GDP & Income', 'National Accounts', 'Quarterly', 'Quarterly with ABS release'),
('H2', 'h2-data.csv', 'Household Finances', 'National Accounts', 'Quarterly', 'Quarterly with ABS release'),
('H3', 'h3-data.csv', 'Business Finances', 'National Accounts', 'Quarterly', 'Quarterly with ABS release'),
('I1', 'i1-data.csv', 'Trade & Balance of Payments', 'International Trade', 'Quarterly', 'Quarterly with ABS release'),
('I3', 'i3-data.csv', 'Exchange Rates', 'Foreign Exchange', 'Daily', 'Daily'),
('D1', 'd1-data.csv', 'Growth in Financial Aggregates', 'Credit & Monetary', 'Monthly', 'Monthly'),
('D2', 'd2-data.csv', 'Lending & Credit Aggregates', 'Credit & Monetary', 'Monthly', 'Monthly'),
('A1', 'a1-data.csv', 'RBA Balance Sheet', 'Central Banking', 'Weekly', 'Weekly'),
('C1', 'c1-data.csv', 'Credit & Charge Cards', 'Payment Systems', 'Monthly', 'Monthly');

-- Unit and measurement dimension
CREATE TABLE rba_dimensions.dim_measurement (
    measurement_key SERIAL PRIMARY KEY,
    unit_type VARCHAR(20) NOT NULL, -- 'Currency', 'Percentage', 'Index', 'Count', 'Ratio'
    unit_description VARCHAR(50) NOT NULL, -- '$ million', 'Per cent', 'Index 2021-22=100', etc.
    unit_short_code VARCHAR(10), -- '$m', '%', 'Index'
    price_basis VARCHAR(25), -- 'Current Prices', 'Chain Volume Measures', 'Nominal'
    adjustment_type VARCHAR(25), -- 'Seasonally Adjusted', 'Original', 'Trend'
    is_real_series BOOLEAN, -- TRUE for chain volume measures
    is_seasonally_adjusted BOOLEAN,
    decimal_places INTEGER DEFAULT 2,
    multiplier DECIMAL(15,2) DEFAULT 1.0, -- For unit conversions
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_measurement_combination UNIQUE (unit_type, price_basis, adjustment_type)
);

-- Insert common measurement types
INSERT INTO rba_dimensions.dim_measurement 
(unit_type, unit_description, unit_short_code, price_basis, adjustment_type, is_real_series, is_seasonally_adjusted, decimal_places) VALUES
('Currency', '$ million', '$m', 'Current Prices', 'Seasonally Adjusted', FALSE, TRUE, 0),
('Currency', '$ million', '$m', 'Chain Volume Measures', 'Seasonally Adjusted', TRUE, TRUE, 0),
('Currency', '$ million', '$m', 'Current Prices', 'Original', FALSE, FALSE, 0),
('Currency', '$ million', '$m', 'Chain Volume Measures', 'Original', TRUE, FALSE, 0),
('Percentage', 'Per cent', '%', 'Current Prices', 'Seasonally Adjusted', FALSE, TRUE, 2),
('Percentage', 'Per cent', '%', 'Current Prices', 'Original', FALSE, FALSE, 2),
('Index', 'Index', 'Index', 'Current Prices', 'Seasonally Adjusted', FALSE, TRUE, 1),
('Index', 'Index', 'Index', 'Chain Volume Measures', 'Seasonally Adjusted', TRUE, TRUE, 1),
('Count', 'Number', 'No.', 'Current Prices', 'Seasonally Adjusted', FALSE, TRUE, 0),
('Ratio', 'Ratio', 'Ratio', 'Current Prices', 'Original', FALSE, FALSE, 4);

-- =====================================================
-- FACT LAYER - Core Measurements
-- =====================================================

-- Core circular flow measurements
CREATE TABLE rba_facts.fact_circular_flow (
    time_key INTEGER NOT NULL REFERENCES rba_dimensions.dim_time(time_key),
    component_key INTEGER NOT NULL REFERENCES rba_dimensions.dim_circular_flow_component(component_key),
    source_key INTEGER NOT NULL REFERENCES rba_dimensions.dim_data_source(source_key),
    measurement_key INTEGER NOT NULL REFERENCES rba_dimensions.dim_measurement(measurement_key),
    series_id VARCHAR(20) NOT NULL,
    value DECIMAL(15,2),
    is_primary_series BOOLEAN DEFAULT TRUE,
    data_quality_flag VARCHAR(10), -- 'Good', 'Estimated', 'Provisional'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_circular_flow PRIMARY KEY (time_key, component_key, source_key, measurement_key, series_id)
);

-- Supporting financial flows and indicators
CREATE TABLE rba_facts.fact_financial_flows (
    time_key INTEGER NOT NULL REFERENCES rba_dimensions.dim_time(time_key),
    source_key INTEGER NOT NULL REFERENCES rba_dimensions.dim_data_source(source_key),
    measurement_key INTEGER NOT NULL REFERENCES rba_dimensions.dim_measurement(measurement_key),
    flow_category VARCHAR(30) NOT NULL, -- 'Credit_Growth', 'Money_Supply', 'Interest_Rate', 'Exchange_Rate'
    flow_subcategory VARCHAR(50), -- 'Housing_Credit', 'Business_Credit', 'M3', 'Cash_Rate', etc.
    series_id VARCHAR(20) NOT NULL,
    value DECIMAL(15,4), -- Higher precision for rates and growth
    is_key_indicator BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_financial_flows PRIMARY KEY (time_key, source_key, flow_category, flow_subcategory, series_id)
);

-- Component relationships and mappings
CREATE TABLE rba_facts.fact_component_mapping (
    mapping_key SERIAL PRIMARY KEY,
    component_key INTEGER NOT NULL REFERENCES rba_dimensions.dim_circular_flow_component(component_key),
    source_key INTEGER NOT NULL REFERENCES rba_dimensions.dim_data_source(source_key),
    series_id VARCHAR(20) NOT NULL,
    series_description TEXT,
    mapping_type VARCHAR(20) NOT NULL, -- 'Primary', 'Secondary', 'Validation', 'Proxy'
    mapping_confidence VARCHAR(10) NOT NULL, -- 'High', 'Medium', 'Low'
    coverage_assessment VARCHAR(15) NOT NULL, -- 'Complete', 'Partial', 'Limited'
    temporal_alignment VARCHAR(15), -- 'Direct', 'Interpolated', 'Aggregated'
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_component_mapping UNIQUE (component_key, source_key, series_id)
);

-- =====================================================
-- INDEXING STRATEGY
-- =====================================================

-- Time dimension indices
CREATE INDEX idx_dim_time_date ON rba_dimensions.dim_time(date_value);
CREATE INDEX idx_dim_time_quarter ON rba_dimensions.dim_time(year, quarter) WHERE quarter IS NOT NULL;
CREATE INDEX idx_dim_time_fiscal ON rba_dimensions.dim_time(fiscal_year);

-- Fact table indices for temporal analysis
CREATE INDEX idx_fact_circular_flow_time ON rba_facts.fact_circular_flow(time_key);
CREATE INDEX idx_fact_circular_flow_component ON rba_facts.fact_circular_flow(component_key);
CREATE INDEX idx_fact_circular_flow_time_component ON rba_facts.fact_circular_flow(time_key, component_key);
CREATE INDEX idx_fact_circular_flow_source ON rba_facts.fact_circular_flow(source_key);

-- Financial flows indices
CREATE INDEX idx_fact_financial_flows_time ON rba_facts.fact_financial_flows(time_key);
CREATE INDEX idx_fact_financial_flows_category ON rba_facts.fact_financial_flows(flow_category);
CREATE INDEX idx_fact_financial_flows_time_category ON rba_facts.fact_financial_flows(time_key, flow_category);

-- Staging table indices for ETL performance
CREATE INDEX idx_h1_staging_period ON rba_staging.h1_gdp_income(period_date);
CREATE INDEX idx_h2_staging_period ON rba_staging.h2_household_finances(period_date);
CREATE INDEX idx_h3_staging_period ON rba_staging.h3_business_finances(period_date);
CREATE INDEX idx_i1_staging_period ON rba_staging.i1_trade_bop(period_date);

-- =====================================================
-- ANALYTICAL VIEWS
-- =====================================================

-- Core circular flow balance validation view
CREATE OR REPLACE VIEW rba_analytics.v_circular_flow_balance AS
WITH quarterly_components AS (
    SELECT 
        t.date_value,
        t.quarter_label,
        c.component_code,
        c.component_name,
        f.value,
        ROW_NUMBER() OVER (PARTITION BY t.date_value, c.component_code ORDER BY f.is_primary_series DESC) as rn
    FROM rba_facts.fact_circular_flow f
    JOIN rba_dimensions.dim_time t ON f.time_key = t.time_key
    JOIN rba_dimensions.dim_circular_flow_component c ON f.component_key = c.component_key
    JOIN rba_dimensions.dim_measurement m ON f.measurement_key = m.measurement_key
    WHERE t.is_quarter_end = TRUE
      AND m.unit_type = 'Currency'
      AND m.price_basis = 'Current Prices'
      AND m.is_seasonally_adjusted = TRUE
),
pivoted_components AS (
    SELECT 
        date_value,
        quarter_label,
        MAX(CASE WHEN component_code = 'Y' THEN value END) as income,
        MAX(CASE WHEN component_code = 'C' THEN value END) as consumption,
        MAX(CASE WHEN component_code = 'S' THEN value END) as savings,
        MAX(CASE WHEN component_code = 'I' THEN value END) as investment,
        MAX(CASE WHEN component_code = 'G' THEN value END) as govt_expenditure,
        MAX(CASE WHEN component_code = 'T' THEN value END) as taxation,
        MAX(CASE WHEN component_code = 'X' THEN value END) as exports,
        MAX(CASE WHEN component_code = 'M' THEN value END) as imports
    FROM quarterly_components
    WHERE rn = 1 -- Take primary series only
    GROUP BY date_value, quarter_label
)
SELECT 
    date_value,
    quarter_label,
    income,
    consumption,
    savings,
    investment,
    govt_expenditure,
    taxation,
    exports,
    imports,
    -- Calculate circular flow identity components
    COALESCE(savings, 0) + COALESCE(taxation, 0) + COALESCE(imports, 0) as total_leakages,
    COALESCE(investment, 0) + COALESCE(govt_expenditure, 0) + COALESCE(exports, 0) as total_injections,
    -- Calculate balance (should be close to zero in equilibrium)
    (COALESCE(savings, 0) + COALESCE(taxation, 0) + COALESCE(imports, 0)) - 
    (COALESCE(investment, 0) + COALESCE(govt_expenditure, 0) + COALESCE(exports, 0)) as circular_flow_balance,
    -- Household accounting identity: Y = C + S + T_household (simplified)
    COALESCE(income, 0) - COALESCE(consumption, 0) - COALESCE(savings, 0) as implied_household_taxes,
    -- GDP from expenditure side: Y = C + I + G + (X - M)
    COALESCE(consumption, 0) + COALESCE(investment, 0) + COALESCE(govt_expenditure, 0) + 
    (COALESCE(exports, 0) - COALESCE(imports, 0)) as gdp_expenditure_approach
FROM pivoted_components
ORDER BY date_value;

-- Household sector flows analysis
CREATE OR REPLACE VIEW rba_analytics.v_household_flows AS
SELECT 
    t.date_value,
    t.quarter_label,
    c.component_code,
    c.component_name,
    f.value,
    s.rba_table_code,
    m.unit_description,
    m.price_basis,
    -- Calculate period-over-period growth rates
    LAG(f.value, 4) OVER (PARTITION BY c.component_code ORDER BY t.date_value) as value_year_ago,
    CASE 
        WHEN LAG(f.value, 4) OVER (PARTITION BY c.component_code ORDER BY t.date_value) > 0
        THEN ((f.value / LAG(f.value, 4) OVER (PARTITION BY c.component_code ORDER BY t.date_value)) - 1) * 100
    END as annual_growth_rate
FROM rba_facts.fact_circular_flow f
JOIN rba_dimensions.dim_time t ON f.time_key = t.time_key
JOIN rba_dimensions.dim_circular_flow_component c ON f.component_key = c.component_key
JOIN rba_dimensions.dim_data_source s ON f.source_key = s.source_key
JOIN rba_dimensions.dim_measurement m ON f.measurement_key = m.measurement_key
WHERE c.economic_sector = 'Household'
  AND t.is_quarter_end = TRUE
  AND m.is_seasonally_adjusted = TRUE
  AND f.is_primary_series = TRUE
ORDER BY t.date_value, c.display_order;

-- External sector flows (Trade balance analysis)
CREATE OR REPLACE VIEW rba_analytics.v_external_sector_flows AS
WITH trade_flows AS (
    SELECT 
        t.date_value,
        t.quarter_label,
        c.component_code,
        f.value,
        m.price_basis
    FROM rba_facts.fact_circular_flow f
    JOIN rba_dimensions.dim_time t ON f.time_key = t.time_key
    JOIN rba_dimensions.dim_circular_flow_component c ON f.component_key = c.component_key
    JOIN rba_dimensions.dim_measurement m ON f.measurement_key = m.measurement_key
    WHERE c.component_code IN ('X', 'M')
      AND t.is_quarter_end = TRUE
      AND m.is_seasonally_adjusted = TRUE
      AND f.is_primary_series = TRUE
)
SELECT 
    date_value,
    quarter_label,
    price_basis,
    MAX(CASE WHEN component_code = 'X' THEN value END) as exports,
    MAX(CASE WHEN component_code = 'M' THEN value END) as imports,
    MAX(CASE WHEN component_code = 'X' THEN value END) - 
    MAX(CASE WHEN component_code = 'M' THEN value END) as trade_balance,
    -- Calculate trade balance as percentage of GDP (requires GDP data)
    CASE 
        WHEN MAX(CASE WHEN component_code = 'X' THEN value END) + 
             MAX(CASE WHEN component_code = 'M' THEN value END) > 0
        THEN (MAX(CASE WHEN component_code = 'X' THEN value END) - 
              MAX(CASE WHEN component_code = 'M' THEN value END)) / 
             (MAX(CASE WHEN component_code = 'X' THEN value END) + 
              MAX(CASE WHEN component_code = 'M' THEN value END)) * 100
    END as trade_balance_ratio
FROM trade_flows
GROUP BY date_value, quarter_label, price_basis
ORDER BY date_value, price_basis;

-- Data quality and coverage assessment view
CREATE OR REPLACE VIEW rba_analytics.v_data_coverage_assessment AS
SELECT 
    c.component_code,
    c.component_name,
    c.economic_sector,
    COUNT(DISTINCT f.source_key) as num_data_sources,
    COUNT(DISTINCT f.series_id) as num_series,
    MIN(t.date_value) as earliest_data,
    MAX(t.date_value) as latest_data,
    COUNT(DISTINCT CASE WHEN f.is_primary_series THEN f.series_id END) as num_primary_series,
    COUNT(DISTINCT CASE WHEN m.is_seasonally_adjusted THEN f.series_id END) as num_seasonally_adjusted_series,
    COUNT(DISTINCT CASE WHEN m.price_basis = 'Chain Volume Measures' THEN f.series_id END) as num_real_series,
    -- Calculate data completeness over last 5 years
    COUNT(CASE WHEN t.date_value >= CURRENT_DATE - INTERVAL '5 years' THEN 1 END) as recent_observations,
    ROUND(
        COUNT(CASE WHEN t.date_value >= CURRENT_DATE - INTERVAL '5 years' THEN 1 END)::DECIMAL / 
        GREATEST(EXTRACT(days FROM CURRENT_DATE - (CURRENT_DATE - INTERVAL '5 years'))::INTEGER / 90, 1) * 100, 
        1
    ) as recent_completeness_pct
FROM rba_facts.fact_circular_flow f
JOIN rba_dimensions.dim_circular_flow_component c ON f.component_key = c.component_key
JOIN rba_dimensions.dim_time t ON f.time_key = t.time_key
JOIN rba_dimensions.dim_measurement m ON f.measurement_key = m.measurement_key
GROUP BY c.component_code, c.component_name, c.economic_sector, c.display_order
ORDER BY c.display_order;

-- =====================================================
-- DATA VALIDATION FUNCTIONS
-- =====================================================

-- Function to validate circular flow identity: S + T + M = I + G + X
CREATE OR REPLACE FUNCTION rba_analytics.validate_circular_flow_identity(
    check_date DATE DEFAULT CURRENT_DATE - INTERVAL '1 quarter'
) RETURNS TABLE (
    validation_date DATE,
    leakages DECIMAL(15,2),
    injections DECIMAL(15,2),
    balance DECIMAL(15,2),
    balance_pct DECIMAL(8,4),
    is_balanced BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        v.date_value,
        v.total_leakages,
        v.total_injections,
        v.circular_flow_balance,
        CASE 
            WHEN v.total_leakages > 0 
            THEN ABS(v.circular_flow_balance) / v.total_leakages * 100 
            ELSE NULL 
        END as balance_percentage,
        ABS(v.circular_flow_balance) <= 0.01 * GREATEST(v.total_leakages, v.total_injections) as is_balanced
    FROM rba_analytics.v_circular_flow_balance v
    WHERE v.date_value = check_date;
END;
$$ LANGUAGE plpgsql;

-- Function to check data freshness
CREATE OR REPLACE FUNCTION rba_analytics.check_data_freshness()
RETURNS TABLE (
    source_table VARCHAR(10),
    latest_data_date DATE,
    days_since_update INTEGER,
    expected_frequency VARCHAR(15),
    is_current BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    WITH source_freshness AS (
        SELECT 
            s.rba_table_code,
            MAX(t.date_value) as latest_date,
            s.primary_frequency,
            CURRENT_DATE - MAX(t.date_value) as days_old
        FROM rba_facts.fact_circular_flow f
        JOIN rba_dimensions.dim_time t ON f.time_key = t.time_key
        JOIN rba_dimensions.dim_data_source s ON f.source_key = s.source_key
        GROUP BY s.rba_table_code, s.primary_frequency
    )
    SELECT 
        rba_table_code,
        latest_date,
        days_old,
        primary_frequency,
        CASE 
            WHEN primary_frequency = 'Daily' AND days_old <= 7 THEN TRUE
            WHEN primary_frequency = 'Weekly' AND days_old <= 14 THEN TRUE
            WHEN primary_frequency = 'Monthly' AND days_old <= 45 THEN TRUE
            WHEN primary_frequency = 'Quarterly' AND days_old <= 120 THEN TRUE
            ELSE FALSE
        END as is_current
    FROM source_freshness
    ORDER BY days_old DESC;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- ETL HELPER FUNCTIONS
-- =====================================================

-- Function to load data from staging to fact tables
CREATE OR REPLACE FUNCTION rba_facts.load_circular_flow_data(
    source_table_code VARCHAR(10),
    component_mapping JSONB DEFAULT NULL
) RETURNS INTEGER AS $$
DECLARE
    records_processed INTEGER := 0;
    staging_table TEXT;
    sql_query TEXT;
BEGIN
    -- Map source table code to staging table
    staging_table := CASE source_table_code
        WHEN 'H1' THEN 'rba_staging.h1_gdp_income'
        WHEN 'H2' THEN 'rba_staging.h2_household_finances'
        WHEN 'H3' THEN 'rba_staging.h3_business_finances'
        WHEN 'I1' THEN 'rba_staging.i1_trade_bop'
        WHEN 'D1' THEN 'rba_staging.d1_financial_aggregates'
        WHEN 'D2' THEN 'rba_staging.d2_lending_credit'
        WHEN 'A1' THEN 'rba_staging.a1_rba_balance_sheet'
        WHEN 'I3' THEN 'rba_staging.i3_exchange_rates'
        WHEN 'C1' THEN 'rba_staging.c1_credit_cards'
        ELSE NULL
    END;
    
    IF staging_table IS NULL THEN
        RAISE EXCEPTION 'Unknown source table code: %', source_table_code;
    END IF;
    
    -- This is a template - actual implementation would require
    -- detailed series mapping based on component_mapping parameter
    RAISE NOTICE 'ETL function template for source: %, staging table: %', source_table_code, staging_table;
    
    RETURN records_processed;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- PARTITIONING SETUP (for large datasets)
-- =====================================================

-- Create partitioned fact table for very large datasets
CREATE TABLE rba_facts.fact_circular_flow_partitioned (
    LIKE rba_facts.fact_circular_flow INCLUDING ALL
) PARTITION BY RANGE (time_key);

-- Create yearly partitions (example for 2020-2025)
CREATE TABLE rba_facts.fact_circular_flow_2020 PARTITION OF rba_facts.fact_circular_flow_partitioned
FOR VALUES FROM (
    (SELECT time_key FROM rba_dimensions.dim_time WHERE date_value = '2020-01-01' LIMIT 1)
) TO (
    (SELECT time_key FROM rba_dimensions.dim_time WHERE date_value = '2021-01-01' LIMIT 1)
);

-- =====================================================
-- GRANTS AND PERMISSIONS
-- =====================================================

-- Create roles for different access levels
CREATE ROLE rba_readonly;
CREATE ROLE rba_analyst;
CREATE ROLE rba_etl_user;

-- Grant permissions
GRANT USAGE ON SCHEMA rba_dimensions, rba_facts, rba_analytics TO rba_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA rba_dimensions, rba_facts, rba_analytics TO rba_readonly;

GRANT rba_readonly TO rba_analyst;
GRANT USAGE ON SCHEMA rba_staging TO rba_etl_user;
GRANT ALL ON ALL TABLES IN SCHEMA rba_staging TO rba_etl_user;
GRANT INSERT, UPDATE ON ALL TABLES IN SCHEMA rba_facts TO rba_etl_user;

-- =====================================================
-- INITIALIZATION DATA
-- =====================================================

-- Populate time dimension for typical analysis period (2000-2030)
SELECT rba_dimensions.populate_time_dimension('2000-01-01', '2030-12-31');

-- Insert sample component mappings (would be populated based on detailed analysis)
INSERT INTO rba_facts.fact_component_mapping 
(component_key, source_key, series_id, series_description, mapping_type, mapping_confidence, coverage_assessment, notes) 
SELECT 
    c.component_key,
    s.source_key,
    'SAMPLE_SERIES_' || c.component_code || '_' || s.rba_table_code,
    'Sample mapping for ' || c.component_name || ' from ' || s.table_description,
    'Primary',
    'High',
    'Complete',
    'Sample mapping - to be replaced with actual series mappings'
FROM rba_dimensions.dim_circular_flow_component c
CROSS JOIN rba_dimensions.dim_data_source s
WHERE (c.component_code = 'Y' AND s.rba_table_code IN ('H1', 'H2'))
   OR (c.component_code = 'C' AND s.rba_table_code = 'H2')
   OR (c.component_code = 'S' AND s.rba_table_code = 'H2')
   OR (c.component_code = 'I' AND s.rba_table_code IN ('H1', 'H3'))
   OR (c.component_code = 'G' AND s.rba_table_code = 'H1')
   OR (c.component_code = 'T' AND s.rba_table_code = 'A1')
   OR (c.component_code = 'X' AND s.rba_table_code = 'I1')
   OR (c.component_code = 'M' AND s.rba_table_code = 'I1');

-- =====================================================
-- MAINTENANCE PROCEDURES
-- =====================================================

-- Create maintenance function for statistics updates
CREATE OR REPLACE FUNCTION rba_analytics.update_table_statistics()
RETURNS VOID AS $$
BEGIN
    -- Update statistics for all fact tables
    ANALYZE rba_facts.fact_circular_flow;
    ANALYZE rba_facts.fact_financial_flows;
    ANALYZE rba_facts.fact_component_mapping;
    
    -- Update statistics for dimension tables
    ANALYZE rba_dimensions.dim_time;
    ANALYZE rba_dimensions.dim_circular_flow_component;
    ANALYZE rba_dimensions.dim_data_source;
    ANALYZE rba_dimensions.dim_measurement;
    
    RAISE NOTICE 'Table statistics updated at %', CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- COMMENTS AND DOCUMENTATION
-- =====================================================

COMMENT ON SCHEMA rba_staging IS 'Staging area for raw CSV imports from RBA statistical tables';
COMMENT ON SCHEMA rba_dimensions IS 'Dimension tables for circular flow analysis reference data';
COMMENT ON SCHEMA rba_facts IS 'Fact tables containing circular flow measurements and relationships';
COMMENT ON SCHEMA rba_analytics IS 'Analytical views and functions for circular flow modeling';

COMMENT ON TABLE rba_facts.fact_circular_flow IS 'Core fact table mapping circular flow components to time series measurements';
COMMENT ON VIEW rba_analytics.v_circular_flow_balance IS 'Validates circular flow identity: S + T + M = I + G + X';

COMMENT ON FUNCTION rba_analytics.validate_circular_flow_identity IS 'Validates macroeconomic circular flow equilibrium condition';
COMMENT ON FUNCTION rba_analytics.check_data_freshness IS 'Monitors data currency for each source table';

-- =====================================================
-- COMPLETION MESSAGE
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'RBA Circular Flow Database Schema Created Successfully';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Schemas created: staging, dimensions, facts, analytics';
    RAISE NOTICE 'Core tables: % staging tables, % dimension tables, % fact tables', 
        (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'rba_staging'),
        (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'rba_dimensions'),
        (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'rba_facts');
    RAISE NOTICE 'Analytical views: % views created',
        (SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'rba_analytics');
    RAISE NOTICE 'Time dimension populated: % to %',
        (SELECT MIN(date_value) FROM rba_dimensions.dim_time),
        (SELECT MAX(date_value) FROM rba_dimensions.dim_time);
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '1. Load CSV data into staging tables';
    RAISE NOTICE '2. Map series to components using fact_component_mapping';
    RAISE NOTICE '3. Execute ETL processes to populate fact tables';
    RAISE NOTICE '4. Validate circular flow identity using analytical views';
    RAISE NOTICE '========================================';
END;
$$;
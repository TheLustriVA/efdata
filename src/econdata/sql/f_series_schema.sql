-- F-Series Interest Rates Schema
-- Date: June 2, 2025
-- Author: Claude & Kieran
-- Purpose: Store and process RBA F-series interest rate data for circular flow model

-- =====================================================
-- STAGING TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS rba_staging.f_series_rates (
    id SERIAL PRIMARY KEY,
    
    -- Source metadata
    table_code VARCHAR(10) NOT NULL,  -- F1, F4, F5, etc.
    table_name VARCHAR(255) NOT NULL,
    source_file VARCHAR(255) NOT NULL,
    extraction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Series identification
    series_id VARCHAR(50) NOT NULL,    -- e.g., FIRMMCRTD
    series_title VARCHAR(500),         -- Full descriptive title
    series_description TEXT,           -- Detailed description
    
    -- Time dimension
    observation_date DATE NOT NULL,
    frequency VARCHAR(20),             -- Daily, Monthly, Quarterly
    
    -- Measures
    value NUMERIC(10,4),              -- Interest rate value
    unit VARCHAR(50),                 -- Usually "Per cent per annum"
    
    -- Data characteristics
    type VARCHAR(20),                 -- Original, Seasonally Adjusted
    source_org VARCHAR(50),           -- RBA, ASX, FENICS, etc.
    publication_date DATE,
    
    -- Processing metadata
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_f_series_observation UNIQUE (
        table_code, series_id, observation_date
    )
);

-- Indexes for efficient querying
CREATE INDEX idx_f_series_table ON rba_staging.f_series_rates(table_code);
CREATE INDEX idx_f_series_date ON rba_staging.f_series_rates(observation_date);
CREATE INDEX idx_f_series_processed ON rba_staging.f_series_rates(processed);
CREATE INDEX idx_f_series_series_id ON rba_staging.f_series_rates(series_id);

-- =====================================================
-- DIMENSION TABLES
-- =====================================================

-- Interest rate type dimension
CREATE TABLE IF NOT EXISTS rba_dimensions.dim_interest_rate_type (
    rate_type_key SERIAL PRIMARY KEY,
    rate_code VARCHAR(50) UNIQUE NOT NULL,
    rate_name VARCHAR(255) NOT NULL,
    rate_category VARCHAR(100),        -- 'policy', 'deposit', 'lending', 'market'
    rate_subcategory VARCHAR(100),     -- 'housing', 'business', 'personal', etc.
    instrument_type VARCHAR(100),      -- 'cash_rate', 'term_deposit', 'mortgage', etc.
    term_structure VARCHAR(50),        -- 'overnight', '1-month', '3-month', 'variable', 'fixed'
    borrower_type VARCHAR(50),         -- 'owner-occupier', 'investor', 'business', 'personal'
    table_source VARCHAR(10),          -- F1, F4, F5, etc.
    circular_flow_component CHAR(1),   -- 'S' for deposit rates, 'I' for lending rates
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert key rate types (initial set for circular flow)
INSERT INTO rba_dimensions.dim_interest_rate_type 
    (rate_code, rate_name, rate_category, rate_subcategory, instrument_type, term_structure, table_source, circular_flow_component)
VALUES
    -- Policy rates (F1)
    ('FIRMMCRTD', 'Cash Rate Target', 'policy', 'monetary_policy', 'cash_rate', 'overnight', 'F1', NULL),
    ('FIRMMCRID', 'Interbank Overnight Cash Rate', 'market', 'money_market', 'cash_rate', 'overnight', 'F1', NULL),
    
    -- Deposit rates (F4) - affect Savings (S)
    ('FRDIRTAB5K', 'Transaction Accounts - Banks', 'deposit', 'transaction', 'transaction_account', 'at_call', 'F4', 'S'),
    ('FRDIRSAB10K', 'Bonus Savings Accounts', 'deposit', 'savings', 'savings_account', 'at_call', 'F4', 'S'),
    ('FRDIRBTD10K1M', 'Term Deposits - 1 month', 'deposit', 'term_deposit', 'term_deposit', '1-month', 'F4', 'S'),
    ('FRDIRBTD10K3M', 'Term Deposits - 3 months', 'deposit', 'term_deposit', 'term_deposit', '3-month', 'F4', 'S'),
    ('FRDIRBTD10K6M', 'Term Deposits - 6 months', 'deposit', 'term_deposit', 'term_deposit', '6-month', 'F4', 'S'),
    ('FRDIRBTD10K1Y', 'Term Deposits - 1 year', 'deposit', 'term_deposit', 'term_deposit', '1-year', 'F4', 'S'),
    
    -- Lending rates (F5) - affect Investment (I)
    ('FILRHLBVS', 'Housing - Standard Variable - Owner-occupier', 'lending', 'housing', 'mortgage', 'variable', 'F5', 'I'),
    ('FILRHLBVD', 'Housing - Discounted Variable - Owner-occupier', 'lending', 'housing', 'mortgage', 'variable', 'F5', 'I'),
    ('FILRHLBVSI', 'Housing - Standard Variable - Investor', 'lending', 'housing', 'mortgage', 'variable', 'F5', 'I'),
    ('FILRHLBVDI', 'Housing - Discounted Variable - Investor', 'lending', 'housing', 'mortgage', 'variable', 'F5', 'I'),
    ('FILRSBVRT', 'Small Business - Variable Term Loan', 'lending', 'business', 'business_loan', 'variable', 'F5', 'I'),
    ('FILRSBVOO', 'Small Business - Variable Overdraft', 'lending', 'business', 'overdraft', 'variable', 'F5', 'I'),
    ('FILRPLRCCS', 'Credit Cards - Standard Rate', 'lending', 'personal', 'credit_card', 'variable', 'F5', 'C')
ON CONFLICT (rate_code) DO NOTHING;

-- =====================================================
-- FACT TABLE
-- =====================================================

-- Interest rate observations fact table
CREATE TABLE IF NOT EXISTS rba_facts.fact_interest_rates (
    id SERIAL PRIMARY KEY,
    
    -- Dimensions
    time_key INTEGER NOT NULL REFERENCES rba_dimensions.dim_time(time_key),
    rate_type_key INTEGER NOT NULL REFERENCES rba_dimensions.dim_interest_rate_type(rate_type_key),
    source_key INTEGER NOT NULL REFERENCES rba_dimensions.dim_data_source(source_key),
    measurement_key INTEGER NOT NULL REFERENCES rba_dimensions.dim_measurement(measurement_key),
    
    -- Measures
    rate_value NUMERIC(10,4) NOT NULL,      -- Interest rate in percentage
    rate_basis_points INTEGER,              -- Rate in basis points (rate_value * 100)
    
    -- Derived measures
    spread_to_cash_rate NUMERIC(10,4),      -- Spread over cash rate
    real_rate NUMERIC(10,4),                -- Nominal rate minus inflation (if available)
    
    -- Metadata
    observation_frequency VARCHAR(20),
    is_interpolated BOOLEAN DEFAULT FALSE,
    data_quality_flag VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_rate_observation UNIQUE (
        time_key, rate_type_key, source_key
    )
);

-- Indexes for performance
CREATE INDEX idx_rate_facts_time ON rba_facts.fact_interest_rates(time_key);
CREATE INDEX idx_rate_facts_type ON rba_facts.fact_interest_rates(rate_type_key);
CREATE INDEX idx_rate_facts_value ON rba_facts.fact_interest_rates(rate_value);

-- =====================================================
-- ANALYTICS VIEWS
-- =====================================================

-- View for deposit rates affecting savings decisions
CREATE OR REPLACE VIEW rba_analytics.deposit_rates_summary AS
SELECT 
    dt.date_value,
    dt.year,
    dt.quarter,
    irt.rate_category,
    irt.rate_subcategory,
    irt.term_structure,
    AVG(fir.rate_value) as avg_rate,
    MAX(fir.rate_value) as max_rate,
    MIN(fir.rate_value) as min_rate
FROM rba_facts.fact_interest_rates fir
JOIN rba_dimensions.dim_time dt ON fir.time_key = dt.time_key
JOIN rba_dimensions.dim_interest_rate_type irt ON fir.rate_type_key = irt.rate_type_key
WHERE irt.circular_flow_component = 'S'
GROUP BY dt.date_value, dt.year, dt.quarter, irt.rate_category, irt.rate_subcategory, irt.term_structure;

-- View for lending rates affecting investment decisions
CREATE OR REPLACE VIEW rba_analytics.lending_rates_summary AS
SELECT 
    dt.date_value,
    dt.year,
    dt.quarter,
    irt.rate_category,
    irt.rate_subcategory,
    irt.borrower_type,
    AVG(fir.rate_value) as avg_rate,
    MAX(fir.rate_value) as max_rate,
    MIN(fir.rate_value) as min_rate
FROM rba_facts.fact_interest_rates fir
JOIN rba_dimensions.dim_time dt ON fir.time_key = dt.time_key
JOIN rba_dimensions.dim_interest_rate_type irt ON fir.rate_type_key = irt.rate_type_key
WHERE irt.circular_flow_component = 'I'
GROUP BY dt.date_value, dt.year, dt.quarter, irt.rate_category, irt.rate_subcategory, irt.borrower_type;

-- View for S-I spread analysis
CREATE OR REPLACE VIEW rba_analytics.savings_investment_spread AS
WITH deposit_rates AS (
    SELECT 
        dt.date_value,
        AVG(fir.rate_value) as avg_deposit_rate
    FROM rba_facts.fact_interest_rates fir
    JOIN rba_dimensions.dim_time dt ON fir.time_key = dt.time_key
    JOIN rba_dimensions.dim_interest_rate_type irt ON fir.rate_type_key = irt.rate_type_key
    WHERE irt.circular_flow_component = 'S'
      AND irt.rate_subcategory = 'term_deposit'
    GROUP BY dt.date_value
),
lending_rates AS (
    SELECT 
        dt.date_value,
        AVG(fir.rate_value) as avg_lending_rate
    FROM rba_facts.fact_interest_rates fir
    JOIN rba_dimensions.dim_time dt ON fir.time_key = dt.time_key
    JOIN rba_dimensions.dim_interest_rate_type irt ON fir.rate_type_key = irt.rate_type_key
    WHERE irt.circular_flow_component = 'I'
      AND irt.rate_subcategory IN ('housing', 'business')
    GROUP BY dt.date_value
)
SELECT 
    d.date_value,
    d.avg_deposit_rate,
    l.avg_lending_rate,
    l.avg_lending_rate - d.avg_deposit_rate as lending_deposit_spread
FROM deposit_rates d
JOIN lending_rates l ON d.date_value = l.date_value;

-- =====================================================
-- DATA QUALITY VALIDATION
-- =====================================================

-- Function to validate F-series data quality
CREATE OR REPLACE FUNCTION rba_staging.validate_f_series_data()
RETURNS TABLE(
    check_name TEXT,
    status TEXT,
    details TEXT
) 
LANGUAGE plpgsql
AS $$
BEGIN
    -- Check for negative interest rates (unusual but possible)
    RETURN QUERY
    SELECT 
        'Negative Interest Rates'::TEXT,
        CASE 
            WHEN COUNT(*) = 0 THEN 'PASS'::TEXT
            ELSE 'WARNING'::TEXT
        END,
        'Found ' || COUNT(*) || ' negative rate observations'::TEXT
    FROM rba_staging.f_series_rates
    WHERE value < 0;
    
    -- Check for extreme rates (>50%)
    RETURN QUERY
    SELECT 
        'Extreme Interest Rates'::TEXT,
        CASE 
            WHEN COUNT(*) = 0 THEN 'PASS'::TEXT
            ELSE 'WARNING'::TEXT
        END,
        'Found ' || COUNT(*) || ' rates above 50%'::TEXT
    FROM rba_staging.f_series_rates
    WHERE value > 50;
    
    -- Check temporal coverage
    RETURN QUERY
    SELECT 
        'Temporal Coverage'::TEXT,
        'INFO'::TEXT,
        'Data spans from ' || MIN(observation_date) || ' to ' || MAX(observation_date) || 
        ' (' || COUNT(DISTINCT observation_date) || ' unique dates)'::TEXT
    FROM rba_staging.f_series_rates;
    
    -- Check series completeness
    RETURN QUERY
    SELECT 
        'Series Coverage'::TEXT,
        'INFO'::TEXT,
        'Found ' || COUNT(DISTINCT series_id) || ' unique series across ' || 
        COUNT(DISTINCT table_code) || ' F-tables'::TEXT
    FROM rba_staging.f_series_rates;
    
    -- Check for data gaps in key series
    RETURN QUERY
    WITH cash_rate_gaps AS (
        SELECT 
            observation_date,
            LEAD(observation_date) OVER (ORDER BY observation_date) as next_date,
            LEAD(observation_date) OVER (ORDER BY observation_date) - observation_date as gap_days
        FROM rba_staging.f_series_rates
        WHERE series_id = 'FIRMMCRTD'  -- Cash rate target
    )
    SELECT 
        'Cash Rate Continuity'::TEXT,
        CASE 
            WHEN MAX(gap_days) <= 5 THEN 'PASS'::TEXT  -- Allow weekends/holidays
            ELSE 'WARNING'::TEXT
        END,
        'Maximum gap in cash rate series: ' || COALESCE(MAX(gap_days)::TEXT, '0') || ' days'::TEXT
    FROM cash_rate_gaps
    WHERE next_date IS NOT NULL;
END;
$$;
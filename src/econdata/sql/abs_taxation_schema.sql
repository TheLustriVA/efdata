-- ABS Taxation Data Schema
-- This schema extends the existing RBA circular flow model to include
-- taxation (T) and government spending (G) components from ABS sources

-- Create schema for ABS data if not exists
CREATE SCHEMA IF NOT EXISTS abs_staging;
CREATE SCHEMA IF NOT EXISTS abs_dimensions;

-- =====================================================
-- STAGING TABLES
-- =====================================================

-- Main staging table for Government Finance Statistics
CREATE TABLE IF NOT EXISTS abs_staging.government_finance_statistics (
    id SERIAL PRIMARY KEY,
    
    -- Source metadata
    source_file VARCHAR(255) NOT NULL,
    sheet_name VARCHAR(255),
    extraction_timestamp TIMESTAMP NOT NULL,
    file_checksum VARCHAR(64),
    
    -- Time dimension
    reference_period DATE NOT NULL,
    period_type VARCHAR(20) CHECK (period_type IN ('annual', 'quarterly', 'monthly')),
    
    -- Government dimension
    level_of_government VARCHAR(50) NOT NULL,
    government_entity VARCHAR(255),
    
    -- Revenue classification
    revenue_type VARCHAR(255) NOT NULL,
    tax_category VARCHAR(50),
    gfs_code VARCHAR(20),  -- Government Finance Statistics classification code
    cofog_code VARCHAR(20), -- Classification of Functions of Government
    
    -- Measures
    amount NUMERIC(20, 2) NOT NULL,
    unit VARCHAR(50) DEFAULT 'AUD millions',
    
    -- Data quality indicators
    seasonally_adjusted BOOLEAN DEFAULT FALSE,
    trend_adjusted BOOLEAN DEFAULT FALSE,
    interpolated BOOLEAN DEFAULT FALSE,
    interpolation_method VARCHAR(50),
    data_quality VARCHAR(20) CHECK (data_quality IN ('final', 'revised', 'preliminary', 'estimated')),
    
    -- Processing metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE,
    
    -- Constraints
    CONSTRAINT unique_gfs_record UNIQUE (
        source_file, reference_period, level_of_government, 
        revenue_type, seasonally_adjusted
    )
);

-- Index for efficient querying
CREATE INDEX idx_gfs_period ON abs_staging.government_finance_statistics(reference_period);
CREATE INDEX idx_gfs_gov_level ON abs_staging.government_finance_statistics(level_of_government);
CREATE INDEX idx_gfs_category ON abs_staging.government_finance_statistics(tax_category);
CREATE INDEX idx_gfs_processed ON abs_staging.government_finance_statistics(processed);

-- Staging table for Treasury Monthly Financial Statements
CREATE TABLE IF NOT EXISTS abs_staging.treasury_financial_statements (
    id SERIAL PRIMARY KEY,
    
    -- Source metadata
    source_file VARCHAR(255) NOT NULL,
    report_month DATE NOT NULL,
    extraction_timestamp TIMESTAMP NOT NULL,
    
    -- Classification
    statement_type VARCHAR(50), -- 'revenue', 'expense', 'balance'
    line_item VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    subcategory VARCHAR(100),
    
    -- Measures
    budget_estimate NUMERIC(20, 2),
    actual_amount NUMERIC(20, 2),
    variance_amount NUMERIC(20, 2),
    variance_percent NUMERIC(10, 2),
    
    -- Year-to-date figures
    ytd_budget NUMERIC(20, 2),
    ytd_actual NUMERIC(20, 2),
    ytd_variance NUMERIC(20, 2),
    
    -- Metadata
    unit VARCHAR(50) DEFAULT 'AUD millions',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE
);

-- =====================================================
-- DIMENSION TABLES
-- =====================================================

-- Tax type dimension with hierarchical structure
CREATE TABLE IF NOT EXISTS abs_dimensions.tax_type (
    id SERIAL PRIMARY KEY,
    tax_code VARCHAR(20) UNIQUE NOT NULL,
    tax_name VARCHAR(255) NOT NULL,
    tax_category VARCHAR(50),
    parent_code VARCHAR(20),
    gfs_code VARCHAR(20),
    description TEXT,
    effective_from DATE,
    effective_to DATE,
    is_active BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (parent_code) REFERENCES abs_dimensions.tax_type(tax_code)
);

-- Insert standard tax categories
INSERT INTO abs_dimensions.tax_type (tax_code, tax_name, tax_category, description) VALUES
    ('INCOME_TOTAL', 'Total Income Tax', 'income_tax', 'All income taxes including personal and corporate'),
    ('INCOME_PERSONAL', 'Personal Income Tax', 'income_tax', 'Tax on individual income'),
    ('INCOME_CORPORATE', 'Corporate Income Tax', 'income_tax', 'Tax on company profits'),
    ('GST', 'Goods and Services Tax', 'gst', 'Value added tax on goods and services'),
    ('EXCISE_TOTAL', 'Total Excise and Customs', 'excise', 'All excise and customs duties'),
    ('EXCISE_FUEL', 'Fuel Excise', 'excise', 'Excise on petroleum products'),
    ('EXCISE_ALCOHOL', 'Alcohol Excise', 'excise', 'Excise on alcoholic beverages'),
    ('EXCISE_TOBACCO', 'Tobacco Excise', 'excise', 'Excise on tobacco products'),
    ('CUSTOMS', 'Customs Duties', 'excise', 'Import duties'),
    ('PAYROLL', 'Payroll Tax', 'payroll', 'State tax on wages'),
    ('PROPERTY_TOTAL', 'Total Property Taxes', 'property', 'All property-related taxes'),
    ('LAND_TAX', 'Land Tax', 'property', 'Tax on land ownership'),
    ('STAMP_DUTY', 'Stamp Duties', 'property', 'Transaction taxes'),
    ('OTHER', 'Other Taxes', 'other', 'Miscellaneous taxes and levies')
ON CONFLICT (tax_code) DO NOTHING;

-- Government level dimension
CREATE TABLE IF NOT EXISTS abs_dimensions.government_level (
    id SERIAL PRIMARY KEY,
    level_code VARCHAR(20) UNIQUE NOT NULL,
    level_name VARCHAR(100) NOT NULL,
    level_type VARCHAR(50),
    parent_level VARCHAR(20),
    description TEXT,
    
    FOREIGN KEY (parent_level) REFERENCES abs_dimensions.government_level(level_code)
);

-- Insert government levels
INSERT INTO abs_dimensions.government_level (level_code, level_name, level_type) VALUES
    ('TOTAL', 'All Levels of Government', 'consolidated'),
    ('COMMONWEALTH', 'Commonwealth Government', 'federal'),
    ('STATE_TOTAL', 'All State Governments', 'state'),
    ('STATE_NSW', 'New South Wales', 'state'),
    ('STATE_VIC', 'Victoria', 'state'),
    ('STATE_QLD', 'Queensland', 'state'),
    ('STATE_WA', 'Western Australia', 'state'),
    ('STATE_SA', 'South Australia', 'state'),
    ('STATE_TAS', 'Tasmania', 'state'),
    ('STATE_ACT', 'Australian Capital Territory', 'territory'),
    ('STATE_NT', 'Northern Territory', 'territory'),
    ('LOCAL', 'Local Government', 'local')
ON CONFLICT (level_code) DO NOTHING;

-- =====================================================
-- FACT TABLE
-- =====================================================

-- Taxation facts table linking to circular flow
CREATE TABLE IF NOT EXISTS rba_facts.taxation_revenue (
    id SERIAL PRIMARY KEY,
    
    -- Dimensions
    date_id INTEGER NOT NULL REFERENCES rba_dimensions.date(id),
    tax_type_id INTEGER NOT NULL REFERENCES abs_dimensions.tax_type(id),
    government_level_id INTEGER NOT NULL REFERENCES abs_dimensions.government_level(id),
    data_source_id INTEGER NOT NULL REFERENCES rba_dimensions.data_source(id),
    
    -- Measures
    revenue_amount NUMERIC(20, 2) NOT NULL,
    revenue_amount_sa NUMERIC(20, 2), -- Seasonally adjusted
    revenue_amount_trend NUMERIC(20, 2), -- Trend
    
    -- Proportions and ratios
    share_of_total_tax NUMERIC(10, 4),
    share_of_gdp NUMERIC(10, 4),
    year_on_year_growth NUMERIC(10, 4),
    
    -- Metadata
    interpolated BOOLEAN DEFAULT FALSE,
    data_quality VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_tax_fact UNIQUE (
        date_id, tax_type_id, government_level_id, data_source_id
    )
);

-- Indexes for performance
CREATE INDEX idx_tax_facts_date ON rba_facts.taxation_revenue(date_id);
CREATE INDEX idx_tax_facts_type ON rba_facts.taxation_revenue(tax_type_id);
CREATE INDEX idx_tax_facts_level ON rba_facts.taxation_revenue(government_level_id);

-- =====================================================
-- ETL PROCEDURES
-- =====================================================

-- Function to process staged GFS data into fact table
CREATE OR REPLACE FUNCTION abs_staging.process_gfs_to_facts()
RETURNS INTEGER AS $$
DECLARE
    processed_count INTEGER := 0;
    v_date_id INTEGER;
    v_tax_type_id INTEGER;
    v_gov_level_id INTEGER;
    v_source_id INTEGER;
BEGIN
    -- Process each unprocessed staging record
    FOR r IN 
        SELECT * FROM abs_staging.government_finance_statistics 
        WHERE processed = FALSE 
        ORDER BY reference_period, level_of_government, revenue_type
    LOOP
        -- Get or create dimension IDs
        SELECT id INTO v_date_id FROM rba_dimensions.date 
        WHERE date = r.reference_period;
        
        IF v_date_id IS NULL THEN
            INSERT INTO rba_dimensions.date (date, year, quarter, month, financial_year)
            VALUES (
                r.reference_period,
                EXTRACT(YEAR FROM r.reference_period),
                EXTRACT(QUARTER FROM r.reference_period),
                EXTRACT(MONTH FROM r.reference_period),
                CASE 
                    WHEN EXTRACT(MONTH FROM r.reference_period) >= 7 
                    THEN EXTRACT(YEAR FROM r.reference_period) + 1
                    ELSE EXTRACT(YEAR FROM r.reference_period)
                END
            )
            RETURNING id INTO v_date_id;
        END IF;
        
        -- Get tax type ID
        SELECT id INTO v_tax_type_id FROM abs_dimensions.tax_type 
        WHERE tax_category = r.tax_category
        LIMIT 1;
        
        -- Get government level ID
        SELECT id INTO v_gov_level_id FROM abs_dimensions.government_level 
        WHERE level_name = r.level_of_government
        OR level_code = UPPER(REPLACE(r.level_of_government, ' ', '_'));
        
        -- Get data source ID
        SELECT id INTO v_source_id FROM rba_dimensions.data_source 
        WHERE source_name = 'ABS_GFS';
        
        IF v_source_id IS NULL THEN
            INSERT INTO rba_dimensions.data_source (source_code, source_name, source_type)
            VALUES ('ABS_GFS', 'ABS Government Finance Statistics', 'External')
            RETURNING id INTO v_source_id;
        END IF;
        
        -- Insert or update fact
        INSERT INTO rba_facts.taxation_revenue (
            date_id, tax_type_id, government_level_id, data_source_id,
            revenue_amount, revenue_amount_sa, interpolated, data_quality
        ) VALUES (
            v_date_id, v_tax_type_id, v_gov_level_id, v_source_id,
            r.amount, 
            CASE WHEN r.seasonally_adjusted THEN r.amount ELSE NULL END,
            r.interpolated,
            r.data_quality
        )
        ON CONFLICT (date_id, tax_type_id, government_level_id, data_source_id)
        DO UPDATE SET
            revenue_amount = EXCLUDED.revenue_amount,
            revenue_amount_sa = EXCLUDED.revenue_amount_sa,
            interpolated = EXCLUDED.interpolated,
            data_quality = EXCLUDED.data_quality,
            updated_at = CURRENT_TIMESTAMP;
        
        -- Mark as processed
        UPDATE abs_staging.government_finance_statistics 
        SET processed = TRUE 
        WHERE id = r.id;
        
        processed_count := processed_count + 1;
    END LOOP;
    
    RETURN processed_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- INTEGRATION WITH CIRCULAR FLOW
-- =====================================================

-- View to aggregate taxation data for circular flow T component
CREATE OR REPLACE VIEW rba_analytics.taxation_component AS
SELECT 
    d.date,
    d.financial_year,
    d.quarter,
    gl.level_name as government_level,
    SUM(tr.revenue_amount) as total_tax_revenue,
    SUM(tr.revenue_amount_sa) as total_tax_revenue_sa,
    SUM(CASE WHEN tt.tax_category = 'income_tax' THEN tr.revenue_amount END) as income_tax,
    SUM(CASE WHEN tt.tax_category = 'gst' THEN tr.revenue_amount END) as gst,
    SUM(CASE WHEN tt.tax_category = 'excise' THEN tr.revenue_amount END) as excise_customs,
    SUM(CASE WHEN tt.tax_category = 'payroll' THEN tr.revenue_amount END) as payroll_tax,
    SUM(CASE WHEN tt.tax_category = 'property' THEN tr.revenue_amount END) as property_taxes,
    SUM(tr.share_of_gdp) as tax_to_gdp_ratio
FROM rba_facts.taxation_revenue tr
JOIN rba_dimensions.date d ON tr.date_id = d.id
JOIN abs_dimensions.tax_type tt ON tr.tax_type_id = tt.id
JOIN abs_dimensions.government_level gl ON tr.government_level_id = gl.id
GROUP BY d.date, d.financial_year, d.quarter, gl.level_name;

-- Update circular flow fact table with taxation data
CREATE OR REPLACE FUNCTION rba_analytics.update_circular_flow_taxation()
RETURNS VOID AS $$
BEGIN
    -- Insert or update T component in circular flow
    INSERT INTO rba_analytics.circular_flow (
        date, frequency, component, value, data_source_id
    )
    SELECT 
        date,
        CASE 
            WHEN date_trunc('quarter', date) = date THEN 'Quarterly'::rba_dimensions.frequency_type
            WHEN date_trunc('year', date) = date THEN 'Annual'::rba_dimensions.frequency_type
            ELSE 'Monthly'::rba_dimensions.frequency_type
        END,
        'T',
        total_tax_revenue,
        (SELECT id FROM rba_dimensions.data_source WHERE source_code = 'ABS_GFS')
    FROM rba_analytics.taxation_component
    WHERE government_level = 'All Levels of Government'
    ON CONFLICT (date, frequency, component)
    DO UPDATE SET 
        value = EXCLUDED.value,
        updated_at = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- DATA QUALITY AND VALIDATION
-- =====================================================

-- Check for data quality issues
CREATE OR REPLACE VIEW abs_staging.data_quality_checks AS
SELECT 
    'Missing periods' as check_type,
    COUNT(*) as issue_count,
    STRING_AGG(DISTINCT reference_period::TEXT, ', ') as details
FROM (
    SELECT generate_series(
        MIN(reference_period), 
        MAX(reference_period), 
        '3 months'::interval
    )::DATE as expected_period
    FROM abs_staging.government_finance_statistics
) expected
LEFT JOIN abs_staging.government_finance_statistics actual
ON expected.expected_period = actual.reference_period
WHERE actual.reference_period IS NULL

UNION ALL

SELECT 
    'Duplicate records' as check_type,
    COUNT(*) - COUNT(DISTINCT (reference_period, level_of_government, revenue_type)) as issue_count,
    'Check staging table for duplicates' as details
FROM abs_staging.government_finance_statistics

UNION ALL

SELECT 
    'Negative values' as check_type,
    COUNT(*) as issue_count,
    STRING_AGG(revenue_type || ' (' || amount::TEXT || ')', ', ' LIMIT 5) as details
FROM abs_staging.government_finance_statistics
WHERE amount < 0 AND revenue_type NOT LIKE '%refund%';

-- Grant permissions
GRANT USAGE ON SCHEMA abs_staging TO econcell_app;
GRANT USAGE ON SCHEMA abs_dimensions TO econcell_app;
GRANT SELECT ON ALL TABLES IN SCHEMA abs_staging TO econcell_app;
GRANT SELECT ON ALL TABLES IN SCHEMA abs_dimensions TO econcell_app;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA abs_staging TO econcell_app;
-- ABS Government Expenditure Schema
-- This schema extends the taxation schema to include government expenditure (G component)
-- for the circular flow model from ABS Government Finance Statistics

-- Ensure schemas exist
CREATE SCHEMA IF NOT EXISTS abs_staging;
CREATE SCHEMA IF NOT EXISTS abs_dimensions;
CREATE SCHEMA IF NOT EXISTS rba_facts;
CREATE SCHEMA IF NOT EXISTS rba_dimensions;
CREATE SCHEMA IF NOT EXISTS rba_analytics;

-- =====================================================
-- STAGING TABLE FOR EXPENDITURE
-- =====================================================

-- Main staging table for Government Expenditure data
CREATE TABLE IF NOT EXISTS abs_staging.government_expenditure (
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
    
    -- Expenditure classification
    expenditure_type VARCHAR(255) NOT NULL,
    expenditure_category VARCHAR(50),
    cofog_code VARCHAR(20), -- Classification of Functions of Government
    gfs_code VARCHAR(20),   -- Government Finance Statistics classification code
    
    -- Expenditure type flags
    is_current_expenditure BOOLEAN DEFAULT TRUE,
    is_capital_expenditure BOOLEAN DEFAULT FALSE,
    is_transfer_payment BOOLEAN DEFAULT FALSE,
    
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
    CONSTRAINT unique_expenditure_record UNIQUE (
        source_file, reference_period, level_of_government, 
        expenditure_type, seasonally_adjusted
    )
);

-- Indexes for efficient querying
CREATE INDEX idx_exp_period ON abs_staging.government_expenditure(reference_period);
CREATE INDEX idx_exp_gov_level ON abs_staging.government_expenditure(level_of_government);
CREATE INDEX idx_exp_category ON abs_staging.government_expenditure(expenditure_category);
CREATE INDEX idx_exp_cofog ON abs_staging.government_expenditure(cofog_code);
CREATE INDEX idx_exp_processed ON abs_staging.government_expenditure(processed);

-- =====================================================
-- DIMENSION TABLES
-- =====================================================

-- COFOG (Classification of Functions of Government) dimension
CREATE TABLE IF NOT EXISTS abs_dimensions.cofog_classification (
    id SERIAL PRIMARY KEY,
    cofog_code VARCHAR(20) UNIQUE NOT NULL,
    cofog_name VARCHAR(255) NOT NULL,
    cofog_level INTEGER NOT NULL CHECK (cofog_level IN (1, 2, 3)),
    parent_code VARCHAR(20),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (parent_code) REFERENCES abs_dimensions.cofog_classification(cofog_code)
);

-- Insert standard COFOG categories (Level 1 and some Level 2)
INSERT INTO abs_dimensions.cofog_classification (cofog_code, cofog_name, cofog_level, description) VALUES
    -- Level 1 COFOG codes
    ('01', 'General public services', 1, 'Executive and legislative organs, financial and fiscal affairs, external affairs'),
    ('02', 'Defence', 1, 'Military defence, civil defence, foreign military aid'),
    ('03', 'Public order and safety', 1, 'Police services, fire protection, law courts, prisons'),
    ('04', 'Economic affairs', 1, 'General economic, commercial and labour affairs, agriculture, energy, transport'),
    ('05', 'Environmental protection', 1, 'Waste management, water waste management, pollution abatement'),
    ('06', 'Housing and community amenities', 1, 'Housing development, community development, water supply'),
    ('07', 'Health', 1, 'Medical products, outpatient services, hospital services, public health'),
    ('08', 'Recreation, culture and religion', 1, 'Recreational and sporting services, cultural services, broadcasting'),
    ('09', 'Education', 1, 'Pre-primary, primary, secondary, tertiary education'),
    ('10', 'Social protection', 1, 'Sickness and disability, old age, family and children, unemployment'),
    
    -- Level 2 examples for Health
    ('07.1', 'Medical products, appliances and equipment', 2, 'Pharmaceutical products, therapeutic appliances'),
    ('07.2', 'Outpatient services', 2, 'General medical services, specialized medical services'),
    ('07.3', 'Hospital services', 2, 'General hospital services, specialized hospital services'),
    ('07.4', 'Public health services', 2, 'Public health services'),
    
    -- Level 2 examples for Education
    ('09.1', 'Pre-primary and primary education', 2, 'Pre-primary education, primary education'),
    ('09.2', 'Secondary education', 2, 'Lower secondary, upper secondary education'),
    ('09.3', 'Post-secondary non-tertiary education', 2, 'Post-secondary non-tertiary education'),
    ('09.4', 'Tertiary education', 2, 'First stage tertiary, second stage tertiary'),
    
    -- Level 2 examples for Social Protection
    ('10.1', 'Sickness and disability', 2, 'Sickness benefits, disability benefits'),
    ('10.2', 'Old age', 2, 'Old age pensions'),
    ('10.3', 'Survivors', 2, 'Survivors benefits'),
    ('10.4', 'Family and children', 2, 'Family allowances, maternity benefits'),
    ('10.5', 'Unemployment', 2, 'Unemployment compensation')
ON CONFLICT (cofog_code) DO NOTHING;

-- Expenditure type dimension
CREATE TABLE IF NOT EXISTS abs_dimensions.expenditure_type (
    id SERIAL PRIMARY KEY,
    exp_code VARCHAR(20) UNIQUE NOT NULL,
    exp_name VARCHAR(255) NOT NULL,
    exp_category VARCHAR(50),
    parent_code VARCHAR(20),
    gfs_code VARCHAR(20),
    description TEXT,
    is_current BOOLEAN DEFAULT TRUE,
    is_capital BOOLEAN DEFAULT FALSE,
    is_transfer BOOLEAN DEFAULT FALSE,
    effective_from DATE,
    effective_to DATE,
    is_active BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (parent_code) REFERENCES abs_dimensions.expenditure_type(exp_code)
);

-- Insert standard expenditure types
INSERT INTO abs_dimensions.expenditure_type (exp_code, exp_name, exp_category, is_current, is_capital, is_transfer, description) VALUES
    -- Current expenditure
    ('EMP_COMP', 'Employee Compensation', 'employee_expenses', TRUE, FALSE, FALSE, 'Wages, salaries and in-kind benefits'),
    ('GOODS_SERV', 'Use of Goods and Services', 'goods_services', TRUE, FALSE, FALSE, 'Intermediate consumption'),
    ('INTEREST', 'Interest Payments', 'interest_payments', TRUE, FALSE, FALSE, 'Interest on government debt'),
    ('SUBSIDIES', 'Subsidies', 'grants_subsidies', TRUE, FALSE, TRUE, 'Subsidies to corporations'),
    ('GRANTS', 'Grants', 'grants_subsidies', TRUE, FALSE, TRUE, 'Grants to other governments'),
    ('SOCIAL_BEN', 'Social Benefits', 'social_protection', TRUE, FALSE, TRUE, 'Social assistance and insurance benefits'),
    ('OTHER_CUR', 'Other Current Expenses', 'other_expenditure', TRUE, FALSE, FALSE, 'Other current expenditures'),
    
    -- Capital expenditure
    ('FIXED_CAP', 'Fixed Capital Formation', 'capital_expenditure', FALSE, TRUE, FALSE, 'Acquisition of fixed assets'),
    ('INV_GRANTS', 'Capital Grants', 'capital_expenditure', FALSE, TRUE, TRUE, 'Capital transfers to other sectors'),
    ('OTHER_CAP', 'Other Capital Expenses', 'capital_expenditure', FALSE, TRUE, FALSE, 'Other capital expenditures'),
    
    -- Totals
    ('TOTAL_CUR', 'Total Current Expenditure', 'total_expenditure', TRUE, FALSE, FALSE, 'Sum of all current expenditures'),
    ('TOTAL_CAP', 'Total Capital Expenditure', 'total_expenditure', FALSE, TRUE, FALSE, 'Sum of all capital expenditures'),
    ('TOTAL_EXP', 'Total Expenditure', 'total_expenditure', FALSE, FALSE, FALSE, 'Sum of current and capital expenditures')
ON CONFLICT (exp_code) DO NOTHING;

-- =====================================================
-- FACT TABLE
-- =====================================================

-- Government expenditure facts table
CREATE TABLE IF NOT EXISTS rba_facts.government_expenditure (
    id SERIAL PRIMARY KEY,
    
    -- Dimensions
    date_id INTEGER NOT NULL REFERENCES rba_dimensions.date(id),
    expenditure_type_id INTEGER NOT NULL REFERENCES abs_dimensions.expenditure_type(id),
    cofog_id INTEGER REFERENCES abs_dimensions.cofog_classification(id),
    government_level_id INTEGER NOT NULL REFERENCES abs_dimensions.government_level(id),
    data_source_id INTEGER NOT NULL REFERENCES rba_dimensions.data_source(id),
    
    -- Measures
    expenditure_amount NUMERIC(20, 2) NOT NULL,
    expenditure_amount_sa NUMERIC(20, 2), -- Seasonally adjusted
    expenditure_amount_trend NUMERIC(20, 2), -- Trend
    
    -- Proportions and ratios
    share_of_total_exp NUMERIC(10, 4),
    share_of_gdp NUMERIC(10, 4),
    year_on_year_growth NUMERIC(10, 4),
    
    -- Expenditure type flags (denormalized for performance)
    is_current BOOLEAN DEFAULT TRUE,
    is_capital BOOLEAN DEFAULT FALSE,
    is_transfer BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    interpolated BOOLEAN DEFAULT FALSE,
    data_quality VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_exp_fact UNIQUE (
        date_id, expenditure_type_id, government_level_id, data_source_id, cofog_id
    )
);

-- Indexes for performance
CREATE INDEX idx_exp_facts_date ON rba_facts.government_expenditure(date_id);
CREATE INDEX idx_exp_facts_type ON rba_facts.government_expenditure(expenditure_type_id);
CREATE INDEX idx_exp_facts_cofog ON rba_facts.government_expenditure(cofog_id);
CREATE INDEX idx_exp_facts_level ON rba_facts.government_expenditure(government_level_id);
CREATE INDEX idx_exp_facts_current ON rba_facts.government_expenditure(is_current);
CREATE INDEX idx_exp_facts_capital ON rba_facts.government_expenditure(is_capital);

-- =====================================================
-- ETL PROCEDURES
-- =====================================================

-- Function to process staged expenditure data into fact table
CREATE OR REPLACE FUNCTION abs_staging.process_expenditure_to_facts()
RETURNS INTEGER AS $$
DECLARE
    processed_count INTEGER := 0;
    v_date_id INTEGER;
    v_exp_type_id INTEGER;
    v_cofog_id INTEGER;
    v_gov_level_id INTEGER;
    v_source_id INTEGER;
    v_is_current BOOLEAN;
    v_is_capital BOOLEAN;
    v_is_transfer BOOLEAN;
    r RECORD;
BEGIN
    -- Process each unprocessed staging record
    FOR r IN 
        SELECT * FROM abs_staging.government_expenditure 
        WHERE processed = FALSE 
        ORDER BY reference_period, level_of_government, expenditure_type
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
        
        -- Get expenditure type ID
        SELECT id, is_current, is_capital, is_transfer 
        INTO v_exp_type_id, v_is_current, v_is_capital, v_is_transfer
        FROM abs_dimensions.expenditure_type 
        WHERE exp_category = r.expenditure_category
        OR exp_name = r.expenditure_type
        LIMIT 1;
        
        -- Get COFOG ID if code exists
        IF r.cofog_code IS NOT NULL THEN
            SELECT id INTO v_cofog_id FROM abs_dimensions.cofog_classification 
            WHERE cofog_code = r.cofog_code;
        END IF;
        
        -- Get government level ID
        SELECT id INTO v_gov_level_id FROM abs_dimensions.government_level 
        WHERE level_name = r.level_of_government
        OR level_code = UPPER(REPLACE(r.level_of_government, ' ', '_'));
        
        -- Get data source ID
        SELECT id INTO v_source_id FROM rba_dimensions.data_source 
        WHERE source_name = 'ABS_GFS';
        
        -- Insert or update fact
        INSERT INTO rba_facts.government_expenditure (
            date_id, expenditure_type_id, cofog_id, government_level_id, data_source_id,
            expenditure_amount, expenditure_amount_sa, 
            is_current, is_capital, is_transfer,
            interpolated, data_quality
        ) VALUES (
            v_date_id, v_exp_type_id, v_cofog_id, v_gov_level_id, v_source_id,
            r.amount, 
            CASE WHEN r.seasonally_adjusted THEN r.amount ELSE NULL END,
            COALESCE(v_is_current, r.is_current_expenditure),
            COALESCE(v_is_capital, r.is_capital_expenditure),
            COALESCE(v_is_transfer, r.is_transfer_payment),
            r.interpolated,
            r.data_quality
        )
        ON CONFLICT (date_id, expenditure_type_id, government_level_id, data_source_id, cofog_id)
        DO UPDATE SET
            expenditure_amount = EXCLUDED.expenditure_amount,
            expenditure_amount_sa = EXCLUDED.expenditure_amount_sa,
            interpolated = EXCLUDED.interpolated,
            data_quality = EXCLUDED.data_quality,
            updated_at = CURRENT_TIMESTAMP;
        
        -- Mark as processed
        UPDATE abs_staging.government_expenditure 
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

-- View to aggregate expenditure data for circular flow G component
CREATE OR REPLACE VIEW rba_analytics.government_expenditure_component AS
SELECT 
    d.date,
    d.financial_year,
    d.quarter,
    gl.level_name as government_level,
    SUM(ge.expenditure_amount) as total_expenditure,
    SUM(ge.expenditure_amount_sa) as total_expenditure_sa,
    SUM(CASE WHEN ge.is_current THEN ge.expenditure_amount END) as current_expenditure,
    SUM(CASE WHEN ge.is_capital THEN ge.expenditure_amount END) as capital_expenditure,
    SUM(CASE WHEN ge.is_transfer THEN ge.expenditure_amount END) as transfer_payments,
    -- COFOG breakdown
    SUM(CASE WHEN c.cofog_code = '07' THEN ge.expenditure_amount END) as health_expenditure,
    SUM(CASE WHEN c.cofog_code = '09' THEN ge.expenditure_amount END) as education_expenditure,
    SUM(CASE WHEN c.cofog_code = '10' THEN ge.expenditure_amount END) as social_protection_expenditure,
    SUM(CASE WHEN c.cofog_code = '02' THEN ge.expenditure_amount END) as defence_expenditure,
    SUM(ge.share_of_gdp) as expenditure_to_gdp_ratio
FROM rba_facts.government_expenditure ge
JOIN rba_dimensions.date d ON ge.date_id = d.id
JOIN abs_dimensions.expenditure_type et ON ge.expenditure_type_id = et.id
JOIN abs_dimensions.government_level gl ON ge.government_level_id = gl.id
LEFT JOIN abs_dimensions.cofog_classification c ON ge.cofog_id = c.id
GROUP BY d.date, d.financial_year, d.quarter, gl.level_name;

-- Update circular flow fact table with government expenditure data
CREATE OR REPLACE FUNCTION rba_analytics.update_circular_flow_expenditure()
RETURNS VOID AS $$
BEGIN
    -- Insert or update G component in circular flow
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
        'G',
        total_expenditure,
        (SELECT id FROM rba_dimensions.data_source WHERE source_code = 'ABS_GFS')
    FROM rba_analytics.government_expenditure_component
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

-- View to check expenditure data quality
CREATE OR REPLACE VIEW abs_staging.expenditure_quality_checks AS
SELECT 
    'Missing COFOG codes' as check_type,
    COUNT(*) as issue_count,
    (SELECT STRING_AGG(DISTINCT expenditure_type, ', ') 
     FROM (SELECT DISTINCT expenditure_type 
           FROM abs_staging.government_expenditure 
           WHERE cofog_code IS NULL 
           AND expenditure_category NOT IN ('total_expenditure', 'other_expenditure')
           LIMIT 5) t) as details
FROM abs_staging.government_expenditure
WHERE cofog_code IS NULL AND expenditure_category NOT IN ('total_expenditure', 'other_expenditure')

UNION ALL

SELECT 
    'Negative expenditures' as check_type,
    COUNT(*) as issue_count,
    (SELECT STRING_AGG(expenditure_type || ' (' || amount::TEXT || ')', ', ')
     FROM (SELECT expenditure_type, amount
           FROM abs_staging.government_expenditure
           WHERE amount < 0
           LIMIT 5) t) as details
FROM abs_staging.government_expenditure
WHERE amount < 0

UNION ALL

SELECT 
    'Missing categorization' as check_type,
    COUNT(*) as issue_count,
    (SELECT STRING_AGG(DISTINCT expenditure_type, ', ')
     FROM (SELECT DISTINCT expenditure_type
           FROM abs_staging.government_expenditure
           WHERE expenditure_category IS NULL
           LIMIT 5) t) as details
FROM abs_staging.government_expenditure
WHERE expenditure_category IS NULL;

-- Function to validate G component completeness
CREATE OR REPLACE FUNCTION rba_analytics.validate_g_component()
RETURNS TABLE (
    check_name VARCHAR,
    status VARCHAR,
    details TEXT
) AS $$
BEGIN
    -- Check total expenditure coverage
    RETURN QUERY
    SELECT 
        'Total Expenditure Coverage'::VARCHAR,
        CASE 
            WHEN COUNT(DISTINCT date) > 100 THEN 'PASS'::VARCHAR
            ELSE 'FAIL'::VARCHAR
        END,
        'Found ' || COUNT(DISTINCT date) || ' periods with expenditure data'::TEXT
    FROM rba_analytics.government_expenditure_component
    WHERE total_expenditure > 0;
    
    -- Check COFOG breakdown completeness
    RETURN QUERY
    SELECT 
        'COFOG Category Coverage'::VARCHAR,
        CASE 
            WHEN COUNT(DISTINCT cofog_code) >= 10 THEN 'PASS'::VARCHAR
            ELSE 'WARNING'::VARCHAR
        END,
        'Found ' || COUNT(DISTINCT cofog_code) || ' COFOG categories'::TEXT
    FROM abs_dimensions.cofog_classification c
    JOIN rba_facts.government_expenditure ge ON c.id = ge.cofog_id;
    
    -- Check government level breakdown
    RETURN QUERY
    SELECT 
        'Government Level Coverage'::VARCHAR,
        CASE 
            WHEN COUNT(DISTINCT government_level) >= 3 THEN 'PASS'::VARCHAR
            ELSE 'WARNING'::VARCHAR
        END,
        'Found data for: ' || STRING_AGG(DISTINCT government_level, ', ')::TEXT
    FROM rba_analytics.government_expenditure_component;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (commented out - uncomment if econcell_app user exists)
-- GRANT USAGE ON SCHEMA abs_staging TO econcell_app;
-- GRANT USAGE ON SCHEMA abs_dimensions TO econcell_app;
-- GRANT SELECT ON ALL TABLES IN SCHEMA abs_staging TO econcell_app;
-- GRANT SELECT ON ALL TABLES IN SCHEMA abs_dimensions TO econcell_app;
-- GRANT SELECT ON ALL TABLES IN SCHEMA rba_facts TO econcell_app;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA abs_staging TO econcell_app;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA rba_analytics TO econcell_app;
-- Simplified ABS Government Expenditure Schema
-- This version works with existing table structures

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
CREATE INDEX IF NOT EXISTS idx_exp_period ON abs_staging.government_expenditure(reference_period);
CREATE INDEX IF NOT EXISTS idx_exp_gov_level ON abs_staging.government_expenditure(level_of_government);
CREATE INDEX IF NOT EXISTS idx_exp_category ON abs_staging.government_expenditure(expenditure_category);
CREATE INDEX IF NOT EXISTS idx_exp_cofog ON abs_staging.government_expenditure(cofog_code);
CREATE INDEX IF NOT EXISTS idx_exp_processed ON abs_staging.government_expenditure(processed);

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

-- Insert standard COFOG categories (Level 1)
INSERT INTO abs_dimensions.cofog_classification (cofog_code, cofog_name, cofog_level, description) VALUES
    ('01', 'General public services', 1, 'Executive and legislative organs, financial and fiscal affairs, external affairs'),
    ('02', 'Defence', 1, 'Military defence, civil defence, foreign military aid'),
    ('03', 'Public order and safety', 1, 'Police services, fire protection, law courts, prisons'),
    ('04', 'Economic affairs', 1, 'General economic, commercial and labour affairs, agriculture, energy, transport'),
    ('05', 'Environmental protection', 1, 'Waste management, water waste management, pollution abatement'),
    ('06', 'Housing and community amenities', 1, 'Housing development, community development, water supply'),
    ('07', 'Health', 1, 'Medical products, outpatient services, hospital services, public health'),
    ('08', 'Recreation, culture and religion', 1, 'Recreational and sporting services, cultural services, broadcasting'),
    ('09', 'Education', 1, 'Pre-primary, primary, secondary, tertiary education'),
    ('10', 'Social protection', 1, 'Sickness and disability, old age, family and children, unemployment')
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
-- ANALYTICS VIEWS
-- =====================================================

-- Simple view to aggregate expenditure data by period and government level
CREATE OR REPLACE VIEW abs_staging.expenditure_summary AS
SELECT 
    reference_period,
    level_of_government,
    expenditure_category,
    cofog_code,
    SUM(amount) as total_amount,
    SUM(CASE WHEN is_current_expenditure THEN amount ELSE 0 END) as current_amount,
    SUM(CASE WHEN is_capital_expenditure THEN amount ELSE 0 END) as capital_amount,
    SUM(CASE WHEN is_transfer_payment THEN amount ELSE 0 END) as transfer_amount,
    COUNT(*) as record_count
FROM abs_staging.government_expenditure
GROUP BY reference_period, level_of_government, expenditure_category, cofog_code;

-- View to check data quality
CREATE OR REPLACE VIEW abs_staging.expenditure_quality_summary AS
SELECT 
    COUNT(*) as total_records,
    COUNT(DISTINCT reference_period) as unique_periods,
    COUNT(DISTINCT level_of_government) as unique_gov_levels,
    COUNT(DISTINCT expenditure_category) as unique_categories,
    COUNT(DISTINCT cofog_code) as unique_cofog_codes,
    SUM(CASE WHEN amount < 0 THEN 1 ELSE 0 END) as negative_amounts,
    SUM(CASE WHEN cofog_code IS NULL THEN 1 ELSE 0 END) as missing_cofog,
    SUM(CASE WHEN interpolated THEN 1 ELSE 0 END) as interpolated_records
FROM abs_staging.government_expenditure;
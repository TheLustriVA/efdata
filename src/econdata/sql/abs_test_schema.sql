-- Test Schema for ABS Spider Dry-Run Testing
-- This creates a separate schema for testing without affecting production data

-- Create test schemas
CREATE SCHEMA IF NOT EXISTS abs_staging_test;
CREATE SCHEMA IF NOT EXISTS abs_dimensions_test;

-- Create test user with limited permissions (optional)
-- Note: Using existing user with test schema permissions is also fine
-- CREATE USER IF NOT EXISTS econcell_test WITH PASSWORD 'test_only_password';
-- GRANT USAGE ON SCHEMA abs_staging_test, abs_dimensions_test TO econcell_test;
-- GRANT CREATE, SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA abs_staging_test TO econcell_test;
-- GRANT CREATE, SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA abs_dimensions_test TO econcell_test;

-- Copy table structures from production schemas
CREATE TABLE IF NOT EXISTS abs_staging_test.government_finance_statistics 
    (LIKE abs_staging.government_finance_statistics INCLUDING ALL);

-- Copy dimension tables
CREATE TABLE IF NOT EXISTS abs_dimensions_test.tax_type 
    (LIKE abs_dimensions.tax_type INCLUDING ALL);

CREATE TABLE IF NOT EXISTS abs_dimensions_test.government_level 
    (LIKE abs_dimensions.government_level INCLUDING ALL);

-- Insert reference data into test dimensions
INSERT INTO abs_dimensions_test.tax_type 
SELECT * FROM abs_dimensions.tax_type
ON CONFLICT (tax_code) DO NOTHING;

INSERT INTO abs_dimensions_test.government_level 
SELECT * FROM abs_dimensions.government_level
ON CONFLICT (level_code) DO NOTHING;

-- Create test-specific views for validation
CREATE OR REPLACE VIEW abs_staging_test.test_summary AS
SELECT 
    COUNT(*) as total_records,
    COUNT(DISTINCT reference_period) as unique_periods,
    COUNT(DISTINCT level_of_government) as gov_levels,
    COUNT(DISTINCT tax_category) as tax_categories,
    MIN(reference_period) as earliest_period,
    MAX(reference_period) as latest_period,
    SUM(amount) as total_amount,
    AVG(amount) as avg_amount
FROM abs_staging_test.government_finance_statistics;

-- Function to clean test data
CREATE OR REPLACE FUNCTION abs_staging_test.clean_test_data()
RETURNS void AS $$
BEGIN
    TRUNCATE TABLE abs_staging_test.government_finance_statistics;
    RAISE NOTICE 'Test data cleaned from abs_staging_test schema';
END;
$$ LANGUAGE plpgsql;

-- Function to validate test results
CREATE OR REPLACE FUNCTION abs_staging_test.validate_test_results()
RETURNS TABLE(
    check_name TEXT,
    result BOOLEAN,
    details TEXT
) AS $$
BEGIN
    -- Check 1: Records were inserted
    RETURN QUERY
    SELECT 
        'Records inserted'::TEXT,
        (SELECT COUNT(*) FROM abs_staging_test.government_finance_statistics) > 0,
        'Count: ' || (SELECT COUNT(*) FROM abs_staging_test.government_finance_statistics)::TEXT;
    
    -- Check 2: No production data affected
    RETURN QUERY
    SELECT 
        'No production impact'::TEXT,
        (SELECT COUNT(*) FROM abs_staging.government_finance_statistics 
         WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '5 minutes') = 0,
        'Recent production records: ' || 
        (SELECT COUNT(*) FROM abs_staging.government_finance_statistics 
         WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '5 minutes')::TEXT;
    
    -- Check 3: Data quality
    RETURN QUERY
    SELECT 
        'Valid amounts'::TEXT,
        NOT EXISTS (
            SELECT 1 FROM abs_staging_test.government_finance_statistics 
            WHERE amount IS NULL OR amount < -1000000 OR amount > 1000000000
        ),
        'All amounts within expected range';
    
    -- Check 4: Required fields present
    RETURN QUERY
    SELECT 
        'Required fields'::TEXT,
        NOT EXISTS (
            SELECT 1 FROM abs_staging_test.government_finance_statistics 
            WHERE reference_period IS NULL 
               OR level_of_government IS NULL 
               OR revenue_type IS NULL
        ),
        'All required fields populated';
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT USAGE ON SCHEMA abs_staging_test TO econcell_app;
GRANT USAGE ON SCHEMA abs_dimensions_test TO econcell_app;
GRANT ALL ON ALL TABLES IN SCHEMA abs_staging_test TO econcell_app;
GRANT ALL ON ALL TABLES IN SCHEMA abs_dimensions_test TO econcell_app;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA abs_staging_test TO econcell_app;

-- Usage instructions
COMMENT ON SCHEMA abs_staging_test IS 'Test schema for ABS spider dry-run testing. Use abs_staging_test.clean_test_data() to reset between tests.';
COMMENT ON FUNCTION abs_staging_test.validate_test_results() IS 'Run after test to validate results: SELECT * FROM abs_staging_test.validate_test_results();';
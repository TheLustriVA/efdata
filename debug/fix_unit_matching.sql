-- Fix unit matching issues by updating measurements to handle variations

-- First, let's see what variations exist
SELECT DISTINCT 
    '''' || unit || '''' as quoted_unit,
    LENGTH(unit) as unit_length,
    unit LIKE '% ' as has_trailing_space
FROM (
    SELECT DISTINCT unit FROM rba_staging.h1_gdp_income WHERE extract_date = '2025-05-27'
    UNION
    SELECT DISTINCT unit FROM rba_staging.h2_household_finances WHERE extract_date = '2025-05-27'
    UNION
    SELECT DISTINCT unit FROM rba_staging.h3_business_finances WHERE extract_date = '2025-05-27'
) all_units
ORDER BY unit;

-- Add measurements with exact matches for RBA data
INSERT INTO rba_dimensions.dim_measurement 
(unit_type, unit_description, unit_short_code, price_basis, adjustment_type, is_real_series, is_seasonally_adjusted, decimal_places)
VALUES
-- Handle variations with spaces
('Currency', '$ million', '$m', 'Current Prices', 'Seasonally adjusted', FALSE, TRUE, 0),
('Percentage', 'Per cent ', '%', 'Current Prices', 'Seasonally adjusted', FALSE, TRUE, 2),
('Index', 'Index', 'Index', 'Current Prices', 'Seasonally adjusted', FALSE, TRUE, 1),
-- Add chain volume versions
('Currency', '$ million', '$m', 'Chain volume measures', 'Seasonally adjusted', TRUE, TRUE, 0),
('Index', 'Index', 'Index', 'Chain volume measures', 'Seasonally adjusted', TRUE, TRUE, 1)
ON CONFLICT (unit_type, price_basis, adjustment_type) DO NOTHING;

-- Show what we have now
SELECT 
    measurement_key,
    unit_type,
    '''' || unit_description || '''' as quoted_unit_desc,
    price_basis,
    adjustment_type
FROM rba_dimensions.dim_measurement
ORDER BY unit_type, unit_description;
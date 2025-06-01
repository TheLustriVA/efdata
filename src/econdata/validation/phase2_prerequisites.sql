-- Phase 2 Prerequisites: Setup for Taxation ETL
-- Date: June 1, 2025
-- Author: Claude & Kieran
-- Purpose: Create necessary dimension entries for ABS data

-- ============================================
-- Create ABS data source entry
-- ============================================
INSERT INTO rba_dimensions.dim_data_source (
    rba_table_code,
    csv_filename,
    table_description,
    data_category,
    primary_frequency,
    update_frequency,
    data_provider,
    is_primary_source,
    coverage_start_date
)
VALUES (
    'ABS',
    'abs_government_finance_statistics.xlsx',
    'Australian Bureau of Statistics - Government Finance Statistics',
    'Government Finance',
    'Annual',
    'Annual',
    'ABS',
    true,
    '2015-06-30'
) ON CONFLICT (rba_table_code) DO UPDATE
SET 
    table_description = EXCLUDED.table_description,
    data_provider = EXCLUDED.data_provider,
    data_category = EXCLUDED.data_category;

-- Verify the source was created
SELECT source_key, rba_table_code, data_provider, table_description
FROM rba_dimensions.dim_data_source
WHERE data_provider = 'ABS';

-- ============================================
-- Check measurement units for millions
-- ============================================
SELECT * FROM rba_dimensions.dim_measurement 
WHERE unit_type ILIKE '%million%' 
   OR unit_description ILIKE '%million%'
   OR unit_type = '$m';

-- If no millions unit exists, create one
INSERT INTO rba_dimensions.dim_measurement (
    unit_type,
    unit_description,
    unit_short_code,
    price_basis,
    adjustment_type,
    is_real_series,
    is_seasonally_adjusted,
    decimal_places,
    multiplier
)
SELECT 
    '$m',
    'Millions of dollars',
    'M',
    'Current',
    'Original',
    false,
    false,
    2,
    1000000.0
WHERE NOT EXISTS (
    SELECT 1 FROM rba_dimensions.dim_measurement 
    WHERE unit_type = '$m' OR unit_description ILIKE '%millions%'
);

-- ============================================
-- Update tax category in staging if needed
-- ============================================
-- First check what we have
SELECT DISTINCT tax_category, COUNT(*) 
FROM abs_staging.government_finance_statistics 
GROUP BY tax_category;

-- If it's 'Other Tax' when we expect 'Taxation revenue', we can update it
-- But let's leave it as is since that's what the data contains

-- ============================================
-- Final validation check
-- ============================================
WITH validation_checks AS (
    -- Check ABS source exists
    SELECT 'ABS Source' as check_name,
           CASE WHEN COUNT(*) > 0 THEN '✅ PASS' ELSE '❌ FAIL' END as status,
           COUNT(*) as count
    FROM rba_dimensions.dim_data_source
    WHERE data_provider = 'ABS'
    
    UNION ALL
    
    -- Check measurement unit exists
    SELECT 'Millions Unit' as check_name,
           CASE WHEN COUNT(*) > 0 THEN '✅ PASS' ELSE '❌ FAIL' END as status,
           COUNT(*) as count
    FROM rba_dimensions.dim_measurement
    WHERE unit_type = '$m' OR unit_description ILIKE '%million%'
    
    UNION ALL
    
    -- Check government levels mapped
    SELECT 'Government Mappings' as check_name,
           CASE WHEN COUNT(*) = 0 THEN '✅ PASS' ELSE '❌ FAIL' END as status,
           COUNT(*) as unmapped_count
    FROM (
        SELECT DISTINCT gfs.level_of_government
        FROM abs_staging.government_finance_statistics gfs
        LEFT JOIN abs_dimensions.government_level gl 
            ON gfs.level_of_government = gl.level_name
        WHERE gl.id IS NULL
          AND gfs.level_of_government != 'Total'
    ) unmapped
    
    UNION ALL
    
    -- Check date dimension coverage
    SELECT 'Date Coverage' as check_name,
           CASE WHEN COUNT(*) = 0 THEN '✅ PASS' ELSE '❌ FAIL' END as status,
           COUNT(*) as missing_dates
    FROM (
        SELECT DISTINCT gfs.reference_period
        FROM abs_staging.government_finance_statistics gfs
        LEFT JOIN rba_dimensions.dim_time dt 
            ON gfs.reference_period = dt.date_value
        WHERE dt.time_key IS NULL
    ) missing
)
SELECT * FROM validation_checks ORDER BY check_name;
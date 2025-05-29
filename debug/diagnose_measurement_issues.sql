-- Diagnostic queries to identify measurement matching issues

-- 1. Check all unique unit/adjustment combinations in staging data
\echo 'UNIQUE UNIT/ADJUSTMENT COMBINATIONS IN STAGING DATA:'
SELECT DISTINCT 
    CASE 
        WHEN table_name LIKE '%h1%' THEN 'h1-data.csv'
        WHEN table_name LIKE '%h2%' THEN 'h2-data.csv'
        WHEN table_name LIKE '%h3%' THEN 'h3-data.csv'
        WHEN table_name LIKE '%i1%' THEN 'i1-data.csv'
        WHEN table_name LIKE '%d1%' THEN 'd1-data.csv'
        WHEN table_name LIKE '%d2%' THEN 'd2-data.csv'
        WHEN table_name LIKE '%a1%' THEN 'a1-data.csv'
        WHEN table_name LIKE '%i3%' THEN 'i3-data.csv'
        WHEN table_name LIKE '%c1%' THEN 'c1-data.csv'
    END as source_file,
    unit,
    adjustment_type,
    COUNT(*) as row_count
FROM (
    SELECT 'h1_gdp_income' as table_name, unit, adjustment_type FROM rba_staging.h1_gdp_income WHERE extract_date = CURRENT_DATE
    UNION ALL
    SELECT 'h2_household_finances', unit, adjustment_type FROM rba_staging.h2_household_finances WHERE extract_date = CURRENT_DATE
    UNION ALL
    SELECT 'h3_business_finances', unit, adjustment_type FROM rba_staging.h3_business_finances WHERE extract_date = CURRENT_DATE
    UNION ALL
    SELECT 'i1_trade_bop', unit, adjustment_type FROM rba_staging.i1_trade_bop WHERE extract_date = CURRENT_DATE
    UNION ALL
    SELECT 'd1_financial_aggregates', unit, adjustment_type FROM rba_staging.d1_financial_aggregates WHERE extract_date = CURRENT_DATE
    UNION ALL
    SELECT 'd2_lending_credit', unit, adjustment_type FROM rba_staging.d2_lending_credit WHERE extract_date = CURRENT_DATE
    UNION ALL
    SELECT 'a1_rba_balance_sheet', unit, adjustment_type FROM rba_staging.a1_rba_balance_sheet WHERE extract_date = CURRENT_DATE
    UNION ALL
    SELECT 'i3_exchange_rates', unit, adjustment_type FROM rba_staging.i3_exchange_rates WHERE extract_date = CURRENT_DATE
    UNION ALL
    SELECT 'c1_credit_cards', unit, adjustment_type FROM rba_staging.c1_credit_cards WHERE extract_date = CURRENT_DATE
) staging_data
GROUP BY source_file, unit, adjustment_type
ORDER BY source_file, unit, adjustment_type;

-- 2. Show which unit/adjustment combinations don't have matches
\echo '\nUNMATCHED UNIT/ADJUSTMENT COMBINATIONS:'
WITH staging_units AS (
    SELECT DISTINCT unit, adjustment_type
    FROM (
        SELECT unit, adjustment_type FROM rba_staging.h1_gdp_income WHERE extract_date = CURRENT_DATE
        UNION ALL
        SELECT unit, adjustment_type FROM rba_staging.h2_household_finances WHERE extract_date = CURRENT_DATE
        UNION ALL
        SELECT unit, adjustment_type FROM rba_staging.h3_business_finances WHERE extract_date = CURRENT_DATE
        -- Add other tables as needed
    ) s
)
SELECT 
    su.unit as staging_unit,
    su.adjustment_type as staging_adjustment,
    m.measurement_key,
    m.unit_description as dim_unit_desc,
    m.adjustment_type as dim_adjustment
FROM staging_units su
LEFT JOIN rba_dimensions.dim_measurement m ON
    m.unit_description LIKE CONCAT('%', su.unit, '%') AND
    m.adjustment_type = su.adjustment_type
WHERE m.measurement_key IS NULL
ORDER BY su.unit, su.adjustment_type;

-- 3. Show current measurements for comparison
\echo '\nCURRENT MEASUREMENT DIMENSIONS:'
SELECT 
    measurement_key,
    unit_type,
    unit_description,
    price_basis,
    adjustment_type
FROM rba_dimensions.dim_measurement
ORDER BY unit_type, unit_description, price_basis, adjustment_type;

-- 4. Suggest missing measurements based on staging data
\echo '\nSUGGESTED NEW MEASUREMENTS TO ADD:'
WITH needed_measurements AS (
    SELECT DISTINCT
        CASE 
            WHEN unit LIKE '%$%' THEN 'Currency'
            WHEN unit LIKE '%percent%' OR unit LIKE '%per cent%' OR unit = '%' THEN 'Percentage'
            WHEN unit LIKE '%Index%' OR unit = 'Index' THEN 'Index'
            WHEN unit LIKE '%Number%' OR unit = 'No.' THEN 'Count'
            ELSE 'Other'
        END as unit_type,
        unit as unit_description,
        unit as unit_short_code,
        'Current Prices' as price_basis,
        adjustment_type,
        FALSE as is_real_series,
        CASE WHEN adjustment_type = 'Seasonally adjusted' THEN TRUE ELSE FALSE END as is_seasonally_adjusted,
        2 as decimal_places
    FROM (
        SELECT unit, adjustment_type FROM rba_staging.h1_gdp_income WHERE extract_date = CURRENT_DATE
        UNION
        SELECT unit, adjustment_type FROM rba_staging.h2_household_finances WHERE extract_date = CURRENT_DATE
        UNION
        SELECT unit, adjustment_type FROM rba_staging.h3_business_finances WHERE extract_date = CURRENT_DATE
        UNION
        SELECT unit, adjustment_type FROM rba_staging.i1_trade_bop WHERE extract_date = CURRENT_DATE
        UNION
        SELECT unit, adjustment_type FROM rba_staging.d1_financial_aggregates WHERE extract_date = CURRENT_DATE
        UNION
        SELECT unit, adjustment_type FROM rba_staging.d2_lending_credit WHERE extract_date = CURRENT_DATE
        UNION
        SELECT unit, adjustment_type FROM rba_staging.a1_rba_balance_sheet WHERE extract_date = CURRENT_DATE
        UNION
        SELECT unit, adjustment_type FROM rba_staging.i3_exchange_rates WHERE extract_date = CURRENT_DATE
        UNION
        SELECT unit, adjustment_type FROM rba_staging.c1_credit_cards WHERE extract_date = CURRENT_DATE
    ) all_units
    WHERE NOT EXISTS (
        SELECT 1 FROM rba_dimensions.dim_measurement m
        WHERE m.unit_description = all_units.unit
        AND m.adjustment_type = all_units.adjustment_type
    )
)
SELECT 
    unit_type,
    unit_description,
    price_basis,
    adjustment_type,
    'INSERT INTO rba_dimensions.dim_measurement (unit_type, unit_description, unit_short_code, price_basis, adjustment_type, is_real_series, is_seasonally_adjusted, decimal_places) VALUES (''' 
    || unit_type || ''', ''' || unit_description || ''', ''' || unit_short_code || ''', ''' 
    || price_basis || ''', ''' || adjustment_type || ''', ' || is_real_series || ', ' 
    || is_seasonally_adjusted || ', ' || decimal_places || ');' as insert_statement
FROM needed_measurements
ORDER BY unit_type, unit_description;
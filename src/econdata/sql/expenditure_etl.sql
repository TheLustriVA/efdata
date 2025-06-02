-- Government Expenditure ETL
-- Date: June 2, 2025
-- Author: Claude & Kieran
-- Purpose: Process staged government expenditure data into circular flow G component

CREATE OR REPLACE FUNCTION abs_staging.process_expenditure_to_facts_simple()
RETURNS TABLE(
    records_processed integer,
    records_inserted integer,
    records_updated integer,
    errors text[]
) 
LANGUAGE plpgsql
AS $$
DECLARE
    v_source_key integer;
    v_component_key integer;
    v_measurement_key integer;
    v_records_processed integer := 0;
    v_records_inserted integer := 0;
    v_records_updated integer := 0;
    v_errors text[] := ARRAY[]::text[];
BEGIN
    -- Get dimension keys
    SELECT source_key INTO v_source_key
    FROM rba_dimensions.dim_data_source
    WHERE data_provider = 'ABS' AND rba_table_code = 'ABS';
    
    IF v_source_key IS NULL THEN
        v_errors := array_append(v_errors, 'ABS data source not found in dim_data_source');
        RETURN QUERY SELECT v_records_processed, v_records_inserted, v_records_updated, v_errors;
        RETURN;
    END IF;
    
    -- Get government expenditure component key
    SELECT component_key INTO v_component_key
    FROM rba_dimensions.dim_circular_flow_component
    WHERE component_code = 'G';
    
    IF v_component_key IS NULL THEN
        v_errors := array_append(v_errors, 'Government expenditure component (G) not found in dim_circular_flow_component');
        RETURN QUERY SELECT v_records_processed, v_records_inserted, v_records_updated, v_errors;
        RETURN;
    END IF;
    
    -- Get measurement key for millions
    SELECT measurement_key INTO v_measurement_key
    FROM rba_dimensions.dim_measurement
    WHERE unit_type = '$m' 
      AND price_basis = 'Current'
      AND adjustment_type = 'Original'
    LIMIT 1;
    
    IF v_measurement_key IS NULL THEN
        v_errors := array_append(v_errors, 'Measurement key for $m not found');
        RETURN QUERY SELECT v_records_processed, v_records_inserted, v_records_updated, v_errors;
        RETURN;
    END IF;
    
    -- Process expenditure data into facts with aggregation by period and government level
    WITH expenditure_data AS (
        SELECT 
            dt.time_key,
            v_component_key as component_key,
            v_source_key as source_key,
            v_measurement_key as measurement_key,
            -- Create series ID: G_GOVCODE_YYMMDD (using abbreviated codes to fit in VARCHAR(20))
            'G_' || 
            CASE 
                WHEN ge.level_of_government = 'Commonwealth' THEN 'CW'
                WHEN ge.level_of_government = 'NSW State' THEN 'NSW'
                WHEN ge.level_of_government = 'VIC State' THEN 'VIC'
                WHEN ge.level_of_government = 'QLD State' THEN 'QLD'
                WHEN ge.level_of_government = 'SA State' THEN 'SA'
                WHEN ge.level_of_government = 'WA State' THEN 'WA'
                WHEN ge.level_of_government = 'TAS State' THEN 'TAS'
                WHEN ge.level_of_government = 'ACT Territory' THEN 'ACT'
                WHEN ge.level_of_government = 'NT Territory' THEN 'NT'
                WHEN ge.level_of_government = 'Total' THEN 'TOT'
                WHEN ge.level_of_government ILIKE '%local%' THEN 'LOC'
                ELSE SUBSTR(REPLACE(UPPER(ge.level_of_government), ' ', ''), 1, 3)
            END || '_' || TO_CHAR(ge.reference_period, 'YYMMDD') as series_id,
            SUM(ge.amount) as value,  -- Aggregate all expenditure types
            true as is_primary_series,
            CASE 
                WHEN BOOL_OR(ge.interpolated = true) THEN 'INTERPOLATED'
                WHEN BOOL_OR(ge.data_quality = 'preliminary') THEN 'PRELIMINARY'
                WHEN BOOL_OR(ge.data_quality = 'revised') THEN 'REVISED'
                ELSE 'FINAL'
            END as data_quality_flag,
            'Quarterly' as data_frequency,
            EXTRACT(MONTH FROM ge.reference_period) IN (3, 6, 9, 12) as is_quarter_end_value,
            false as is_monthly_aggregate,
            'SUM' as aggregation_method
        FROM abs_staging.government_expenditure ge
        JOIN rba_dimensions.dim_time dt 
            ON ge.reference_period = dt.date_value
        WHERE ge.amount IS NOT NULL
          AND ge.amount > 0
          AND ge.processed = false
          -- NOTERROR: Include all government levels to preserve granularity
          -- We aggregate in the query rather than excluding levels
        GROUP BY 
            dt.time_key, 
            ge.level_of_government, 
            ge.reference_period
    ),
    -- Insert quarterly aggregates for "All Levels" to match RBA methodology
    all_levels_aggregate AS (
        SELECT 
            dt.time_key,
            v_component_key as component_key,
            v_source_key as source_key,
            v_measurement_key as measurement_key,
            'G_ALL_' || TO_CHAR(ge.reference_period, 'YYMMDD') as series_id,
            SUM(ge.amount) as value,
            true as is_primary_series,
            CASE 
                WHEN BOOL_OR(ge.interpolated = true) THEN 'INTERPOLATED'
                WHEN BOOL_OR(ge.data_quality = 'preliminary') THEN 'PRELIMINARY'
                WHEN BOOL_OR(ge.data_quality = 'revised') THEN 'REVISED'
                ELSE 'FINAL'
            END as data_quality_flag,
            'Quarterly' as data_frequency,
            EXTRACT(MONTH FROM ge.reference_period) IN (3, 6, 9, 12) as is_quarter_end_value,
            false as is_monthly_aggregate,
            'SUM' as aggregation_method
        FROM abs_staging.government_expenditure ge
        JOIN rba_dimensions.dim_time dt 
            ON ge.reference_period = dt.date_value
        WHERE ge.amount IS NOT NULL
          AND ge.amount > 0
          AND ge.processed = false
          -- Only aggregate non-total levels to avoid double counting
          AND ge.level_of_government NOT ILIKE '%total%'
          AND ge.level_of_government NOT ILIKE '%all levels%'
        GROUP BY dt.time_key, ge.reference_period
    ),
    combined_data AS (
        SELECT * FROM expenditure_data
        UNION ALL
        SELECT * FROM all_levels_aggregate
    ),
    upserted AS (
        INSERT INTO rba_facts.fact_circular_flow (
            time_key, component_key, source_key, measurement_key, series_id,
            value, is_primary_series, data_quality_flag, data_frequency,
            is_quarter_end_value, is_monthly_aggregate, aggregation_method
        )
        SELECT * FROM combined_data
        ON CONFLICT (time_key, component_key, source_key, measurement_key, series_id)
        DO UPDATE SET
            value = EXCLUDED.value,
            data_quality_flag = EXCLUDED.data_quality_flag,
            updated_at = CURRENT_TIMESTAMP
        RETURNING (xmax = 0) as inserted
    )
    SELECT 
        COUNT(*) as processed,
        COUNT(*) FILTER (WHERE inserted) as inserted,
        COUNT(*) FILTER (WHERE NOT inserted) as updated
    INTO v_records_processed, v_records_inserted, v_records_updated
    FROM upserted;
    
    -- Mark staging records as processed
    UPDATE abs_staging.government_expenditure
    SET processed = true,
        updated_at = CURRENT_TIMESTAMP
    WHERE processed = false
      AND amount IS NOT NULL
      AND amount > 0;
    
    -- Return results
    RETURN QUERY SELECT v_records_processed, v_records_inserted, v_records_updated, v_errors;
    
EXCEPTION WHEN OTHERS THEN
    v_errors := array_append(v_errors, SQLERRM);
    RETURN QUERY SELECT v_records_processed, v_records_inserted, v_records_updated, v_errors;
END;
$$;

-- Function to validate G component data quality
CREATE OR REPLACE FUNCTION abs_staging.validate_g_component()
RETURNS TABLE(
    check_name text,
    status text,
    details text
) 
LANGUAGE plpgsql
AS $$
BEGIN
    -- Check for negative expenditures
    RETURN QUERY
    SELECT 
        'Negative Expenditures'::text,
        CASE 
            WHEN COUNT(*) = 0 THEN 'PASS'::text
            ELSE 'FAIL'::text
        END,
        'Found ' || COUNT(*) || ' negative expenditure records'::text
    FROM abs_staging.government_expenditure
    WHERE amount < 0;
    
    -- Check for missing government levels
    RETURN QUERY
    SELECT 
        'Government Level Coverage'::text,
        CASE 
            WHEN COUNT(DISTINCT level_of_government) >= 4 THEN 'PASS'::text
            ELSE 'WARNING'::text
        END,
        'Found ' || COUNT(DISTINCT level_of_government) || ' government levels'::text
    FROM abs_staging.government_expenditure;
    
    -- Check temporal coverage
    RETURN QUERY
    SELECT 
        'Temporal Coverage'::text,
        CASE 
            WHEN COUNT(DISTINCT reference_period) >= 20 THEN 'PASS'::text
            ELSE 'WARNING'::text
        END,
        'Coverage from ' || MIN(reference_period) || ' to ' || MAX(reference_period) || 
        ' (' || COUNT(DISTINCT reference_period) || ' periods)'::text
    FROM abs_staging.government_expenditure;
    
    -- Check for data gaps
    RETURN QUERY
    WITH period_gaps AS (
        SELECT 
            reference_period,
            LEAD(reference_period) OVER (ORDER BY reference_period) as next_period,
            LEAD(reference_period) OVER (ORDER BY reference_period) - reference_period as gap_days
        FROM (SELECT DISTINCT reference_period FROM abs_staging.government_expenditure) t
    )
    SELECT 
        'Data Continuity'::text,
        CASE 
            WHEN MAX(gap_days) <= 92 THEN 'PASS'::text  -- Allow up to 92 days (quarterly + 1 day)
            ELSE 'WARNING'::text
        END,
        'Maximum gap between periods: ' || COALESCE(MAX(gap_days)::text, '0') || ' days'::text
    FROM period_gaps
    WHERE next_period IS NOT NULL;
    
    -- Check expenditure categories
    RETURN QUERY
    SELECT 
        'Expenditure Categories'::text,
        CASE 
            WHEN COUNT(DISTINCT expenditure_category) >= 5 THEN 'PASS'::text
            ELSE 'WARNING'::text
        END,
        'Found ' || COUNT(DISTINCT expenditure_category) || ' expenditure categories'::text
    FROM abs_staging.government_expenditure
    WHERE expenditure_category IS NOT NULL;
    
    -- Check COFOG coverage
    RETURN QUERY
    SELECT 
        'COFOG Classification'::text,
        CASE 
            WHEN COUNT(DISTINCT cofog_code) >= 8 THEN 'PASS'::text
            WHEN COUNT(DISTINCT cofog_code) >= 5 THEN 'WARNING'::text
            ELSE 'INFO'::text
        END,
        'Found ' || COUNT(DISTINCT cofog_code) || ' COFOG codes'::text
    FROM abs_staging.government_expenditure
    WHERE cofog_code IS NOT NULL;
END;
$$;
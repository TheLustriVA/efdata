-- Taxation ETL: From staging to facts
-- Date: June 1, 2025
-- Author: Claude & Kieran
-- Purpose: ETL procedure to move taxation data from staging to facts

-- ============================================
-- Create taxation aggregation view
-- ============================================
CREATE OR REPLACE VIEW rba_analytics.taxation_component AS
WITH taxation_aggregated AS (
    SELECT 
        gfs.reference_period as date,
        gfs.level_of_government,
        gl.level_type,
        gl.id as government_level_id,
        SUM(gfs.amount) as total_tax_revenue,
        COUNT(*) as record_count,
        STRING_AGG(DISTINCT gfs.tax_category, ', ') as tax_categories
    FROM abs_staging.government_finance_statistics gfs
    JOIN abs_dimensions.government_level gl 
        ON gfs.level_of_government = gl.level_name
    GROUP BY gfs.reference_period, gfs.level_of_government, gl.level_type, gl.id
),
all_levels_aggregate AS (
    SELECT 
        date,
        'All Levels of Government' as level_of_government,
        'consolidated' as level_type,
        NULL::integer as government_level_id,
        SUM(total_tax_revenue) as total_tax_revenue,
        SUM(record_count) as record_count,
        STRING_AGG(DISTINCT tax_categories, ', ') as tax_categories
    FROM taxation_aggregated
    WHERE level_of_government != 'Total'  -- Exclude the pre-aggregated totals
    GROUP BY date
)
SELECT * FROM taxation_aggregated
UNION ALL
SELECT * FROM all_levels_aggregate
ORDER BY date, level_of_government;

-- ============================================
-- Create ETL procedure for taxation to facts
-- ============================================
CREATE OR REPLACE FUNCTION abs_staging.process_taxation_to_facts()
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
    
    -- Get taxation component key
    SELECT component_key INTO v_component_key
    FROM rba_dimensions.dim_circular_flow_component
    WHERE component_code = 'T';
    
    IF v_component_key IS NULL THEN
        v_errors := array_append(v_errors, 'Taxation component (T) not found in dim_circular_flow_component');
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
    
    -- Process taxation data into facts with aggregation for duplicates
    WITH taxation_data AS (
        SELECT 
            dt.time_key,
            v_component_key as component_key,
            v_source_key as source_key,
            v_measurement_key as measurement_key,
            'T' || gl.id || '_' || TO_CHAR(gfs.reference_period, 'YYMMDD') as series_id,
            SUM(gfs.amount) as value,  -- Aggregate duplicates
            true as is_primary_series,
            CASE 
                WHEN BOOL_OR(gfs.interpolated = true) THEN 'INTERPOLATED'
                ELSE 'FINAL'
            END as data_quality_flag,
            'Quarterly' as data_frequency,
            EXTRACT(MONTH FROM gfs.reference_period) IN (3, 6, 9, 12) as is_quarter_end_value,
            false as is_monthly_aggregate,
            'SUM' as aggregation_method  -- Changed from DIRECT to SUM
        FROM abs_staging.government_finance_statistics gfs
        JOIN abs_dimensions.government_level gl 
            ON gfs.level_of_government = gl.level_name
        JOIN rba_dimensions.dim_time dt 
            ON gfs.reference_period = dt.date_value
        WHERE gfs.amount IS NOT NULL
          AND gfs.amount > 0
          AND gl.level_code != 'TOTAL'  -- Exclude totals to avoid double counting
        GROUP BY dt.time_key, gl.id, gfs.reference_period  -- Group to handle duplicates
    ),
    upserted AS (
        INSERT INTO rba_facts.fact_circular_flow (
            time_key, component_key, source_key, measurement_key, series_id,
            value, is_primary_series, data_quality_flag, data_frequency,
            is_quarter_end_value, is_monthly_aggregate, aggregation_method
        )
        SELECT * FROM taxation_data
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
    
    -- Update circular flow analytics
    PERFORM rba_analytics.update_circular_flow_taxation();
    
    -- Return results
    RETURN QUERY SELECT v_records_processed, v_records_inserted, v_records_updated, v_errors;
    
EXCEPTION WHEN OTHERS THEN
    v_errors := array_append(v_errors, SQLERRM);
    RETURN QUERY SELECT v_records_processed, v_records_inserted, v_records_updated, v_errors;
END;
$$;

-- ============================================
-- Test the ETL with a dry run query
-- ============================================
WITH test_run AS (
    SELECT 
        dt.time_key,
        6 as component_key,  -- T component
        (SELECT source_key FROM rba_dimensions.dim_data_source WHERE data_provider = 'ABS' LIMIT 1) as source_key,
        (SELECT measurement_key FROM rba_dimensions.dim_measurement WHERE unit_type = '$m' LIMIT 1) as measurement_key,
        'ABS_TAX_' || gl.level_code || '_' || TO_CHAR(gfs.reference_period, 'YYYYMMDD') as series_id,
        gfs.amount as value,
        gfs.level_of_government,
        gfs.reference_period
    FROM abs_staging.government_finance_statistics gfs
    JOIN abs_dimensions.government_level gl 
        ON gfs.level_of_government = gl.level_name
    JOIN rba_dimensions.dim_time dt 
        ON gfs.reference_period = dt.date_value
    WHERE gfs.amount IS NOT NULL
      AND gfs.amount > 0
      AND gl.level_code != 'TOTAL'
    LIMIT 10
)
SELECT 
    'Test ETL Preview' as status,
    COUNT(*) as sample_records,
    MIN(value) as min_amount,
    MAX(value) as max_amount,
    COUNT(DISTINCT level_of_government) as gov_levels,
    MIN(reference_period) as min_date,
    MAX(reference_period) as max_date
FROM test_run;

-- ============================================
-- Create summary statistics function
-- ============================================
CREATE OR REPLACE FUNCTION abs_staging.get_taxation_etl_stats()
RETURNS TABLE(
    metric text,
    value text
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    -- Source records
    SELECT 'Source Records'::text, 
           COUNT(*)::text
    FROM abs_staging.government_finance_statistics
    WHERE amount > 0;
    
    RETURN QUERY
    -- Expected fact records (excluding totals)
    SELECT 'Expected Fact Records'::text,
           COUNT(*)::text
    FROM abs_staging.government_finance_statistics gfs
    JOIN abs_dimensions.government_level gl 
        ON gfs.level_of_government = gl.level_name
    WHERE gl.level_code != 'TOTAL' AND gfs.amount > 0;
    
    RETURN QUERY
    -- Date range
    SELECT 'Date Range'::text,
           MIN(reference_period)::text || ' to ' || MAX(reference_period)::text
    FROM abs_staging.government_finance_statistics;
    
    RETURN QUERY
    -- Total amount
    SELECT 'Total Tax Revenue'::text,
           '$' || TO_CHAR(SUM(amount), 'FM999,999,999,990.00')
    FROM abs_staging.government_finance_statistics gfs
    JOIN abs_dimensions.government_level gl 
        ON gfs.level_of_government = gl.level_name
    WHERE gl.level_code != 'TOTAL';
    
    RETURN QUERY
    -- Government levels
    SELECT 'Government Levels'::text,
           STRING_AGG(DISTINCT level_of_government, ', ' ORDER BY level_of_government)
    FROM abs_staging.government_finance_statistics
    WHERE level_of_government != 'Total';
END;
$$;

-- Show ETL statistics
SELECT * FROM abs_staging.get_taxation_etl_stats();
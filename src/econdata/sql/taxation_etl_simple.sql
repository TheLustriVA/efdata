-- Simple Taxation ETL without analytics update
-- Date: June 1, 2025
-- Author: Claude & Kieran

CREATE OR REPLACE FUNCTION abs_staging.process_taxation_to_facts_simple()
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
    
    -- Return results
    RETURN QUERY SELECT v_records_processed, v_records_inserted, v_records_updated, v_errors;
    
EXCEPTION WHEN OTHERS THEN
    v_errors := array_append(v_errors, SQLERRM);
    RETURN QUERY SELECT v_records_processed, v_records_inserted, v_records_updated, v_errors;
END;
$$;
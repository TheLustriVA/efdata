-- F-Series Interest Rates ETL
-- Date: June 2, 2025
-- Author: Claude & Kieran
-- Purpose: Process F-series interest rate data into facts table

CREATE OR REPLACE FUNCTION rba_staging.process_f_series_to_facts()
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
    v_measurement_key integer;
    v_records_processed integer := 0;
    v_records_inserted integer := 0;
    v_records_updated integer := 0;
    v_errors text[] := ARRAY[]::text[];
    v_cash_rate numeric;
BEGIN
    -- Get RBA data source key
    SELECT source_key INTO v_source_key
    FROM rba_dimensions.dim_data_source
    WHERE data_provider = 'RBA' 
      AND table_description LIKE '%Interest Rates%'
    LIMIT 1;
    
    IF v_source_key IS NULL THEN
        -- Create RBA F-series source if not exists
        INSERT INTO rba_dimensions.dim_data_source (
            data_provider, rba_table_code, csv_filename, table_description, 
            data_category, primary_frequency, update_frequency, is_primary_source
        )
        VALUES (
            'RBA', 'F-SERIES', 'f-series-data.csv', 'RBA Statistical Tables - Interest Rates',
            'Financial Markets', 'Daily', 'Daily', true
        )
        RETURNING source_key INTO v_source_key;
    END IF;
    
    -- Get measurement key for percentage
    SELECT measurement_key INTO v_measurement_key
    FROM rba_dimensions.dim_measurement
    WHERE unit_type = '%' 
      AND price_basis = 'Nominal'
      AND adjustment_type = 'Original'
    LIMIT 1;
    
    IF v_measurement_key IS NULL THEN
        -- Create percentage measurement if not exists
        INSERT INTO rba_dimensions.dim_measurement (
            unit_type, unit_description, unit_short_code,
            price_basis, adjustment_type, decimal_places
        )
        VALUES (
            '%', 'Per cent per annum', '%',
            'Nominal', 'Original', 4
        )
        RETURNING measurement_key INTO v_measurement_key;
    END IF;
    
    -- Get current cash rate for spread calculations
    SELECT value INTO v_cash_rate
    FROM rba_staging.f_series_rates
    WHERE series_id = 'FIRMMCRTD'
      AND observation_date = (
          SELECT MAX(observation_date) 
          FROM rba_staging.f_series_rates 
          WHERE series_id = 'FIRMMCRTD'
      );
    
    -- Process F-series data into facts
    WITH rate_data AS (
        SELECT 
            dt.time_key,
            irt.rate_type_key,
            v_source_key as source_key,
            v_measurement_key as measurement_key,
            fs.value as rate_value,
            (fs.value * 100)::integer as rate_basis_points,
            fs.value - v_cash_rate as spread_to_cash_rate,
            fs.frequency as observation_frequency,
            false as is_interpolated,
            'FINAL' as data_quality_flag
        FROM rba_staging.f_series_rates fs
        JOIN rba_dimensions.dim_interest_rate_type irt 
            ON fs.series_id = irt.rate_code
        JOIN rba_dimensions.dim_time dt 
            ON fs.observation_date = dt.date_value
        WHERE fs.value IS NOT NULL
          AND fs.processed = false
          AND irt.is_active = true
    ),
    upserted AS (
        INSERT INTO rba_facts.fact_interest_rates (
            time_key, rate_type_key, source_key, measurement_key,
            rate_value, rate_basis_points, spread_to_cash_rate,
            observation_frequency, is_interpolated, data_quality_flag
        )
        SELECT * FROM rate_data
        ON CONFLICT (time_key, rate_type_key, source_key)
        DO UPDATE SET
            rate_value = EXCLUDED.rate_value,
            rate_basis_points = EXCLUDED.rate_basis_points,
            spread_to_cash_rate = EXCLUDED.spread_to_cash_rate,
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
    UPDATE rba_staging.f_series_rates
    SET processed = true,
        updated_at = CURRENT_TIMESTAMP
    WHERE processed = false
      AND value IS NOT NULL
      AND series_id IN (
          SELECT rate_code 
          FROM rba_dimensions.dim_interest_rate_type 
          WHERE is_active = true
      );
    
    -- Return results
    RETURN QUERY SELECT v_records_processed, v_records_inserted, v_records_updated, v_errors;
    
EXCEPTION WHEN OTHERS THEN
    v_errors := array_append(v_errors, SQLERRM);
    RETURN QUERY SELECT v_records_processed, v_records_inserted, v_records_updated, v_errors;
END;
$$;

-- Function to link interest rates to circular flow components
CREATE OR REPLACE FUNCTION rba_analytics.update_circular_flow_with_rates()
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
    v_component_key_s integer;
    v_component_key_i integer;
    v_source_key integer;
    v_measurement_key integer;
BEGIN
    -- Get component keys
    SELECT component_key INTO v_component_key_s
    FROM rba_dimensions.dim_circular_flow_component
    WHERE component_code = 'S';
    
    SELECT component_key INTO v_component_key_i
    FROM rba_dimensions.dim_circular_flow_component
    WHERE component_code = 'I';
    
    -- Get source and measurement keys
    SELECT source_key INTO v_source_key
    FROM rba_dimensions.dim_data_source
    WHERE rba_table_code = 'F-SERIES';
    
    SELECT measurement_key INTO v_measurement_key
    FROM rba_dimensions.dim_measurement
    WHERE unit_type = '%';
    
    -- Create weighted average deposit rate series for S component
    INSERT INTO rba_facts.fact_circular_flow (
        time_key, component_key, source_key, measurement_key, series_id,
        value, is_primary_series, data_quality_flag, data_frequency,
        is_quarter_end_value, is_monthly_aggregate, aggregation_method
    )
    SELECT 
        fir.time_key,
        v_component_key_s,
        v_source_key,
        v_measurement_key,
        'S_DEPOSIT_RATE',
        AVG(fir.rate_value) as value,
        false as is_primary_series,  -- This is supplementary data
        'FINAL',
        'Monthly',
        false,
        false,
        'WEIGHTED_AVG'
    FROM rba_facts.fact_interest_rates fir
    JOIN rba_dimensions.dim_interest_rate_type irt ON fir.rate_type_key = irt.rate_type_key
    WHERE irt.circular_flow_component = 'S'
      AND irt.rate_subcategory IN ('term_deposit', 'savings')
    GROUP BY fir.time_key
    ON CONFLICT (time_key, component_key, source_key, measurement_key, series_id)
    DO UPDATE SET 
        value = EXCLUDED.value,
        updated_at = CURRENT_TIMESTAMP;
    
    -- Create weighted average lending rate series for I component
    INSERT INTO rba_facts.fact_circular_flow (
        time_key, component_key, source_key, measurement_key, series_id,
        value, is_primary_series, data_quality_flag, data_frequency,
        is_quarter_end_value, is_monthly_aggregate, aggregation_method
    )
    SELECT 
        fir.time_key,
        v_component_key_i,
        v_source_key,
        v_measurement_key,
        'I_LENDING_RATE',
        AVG(fir.rate_value) as value,
        false as is_primary_series,  -- This is supplementary data
        'FINAL',
        'Monthly',
        false,
        false,
        'WEIGHTED_AVG'
    FROM rba_facts.fact_interest_rates fir
    JOIN rba_dimensions.dim_interest_rate_type irt ON fir.rate_type_key = irt.rate_type_key
    WHERE irt.circular_flow_component = 'I'
      AND irt.rate_subcategory IN ('housing', 'business')
    GROUP BY fir.time_key
    ON CONFLICT (time_key, component_key, source_key, measurement_key, series_id)
    DO UPDATE SET 
        value = EXCLUDED.value,
        updated_at = CURRENT_TIMESTAMP;
    
END;
$$;

-- Function to validate interest rate impact on circular flow
CREATE OR REPLACE FUNCTION rba_analytics.validate_rate_impact()
RETURNS TABLE(
    check_name text,
    status text,
    details text
) 
LANGUAGE plpgsql
AS $$
BEGIN
    -- Check if we have rate data for S and I components
    RETURN QUERY
    SELECT 
        'Rate Data Coverage'::text,
        CASE 
            WHEN COUNT(DISTINCT component_key) = 2 THEN 'PASS'::text
            ELSE 'FAIL'::text
        END,
        'Found rate data for ' || COUNT(DISTINCT component_key) || ' components'::text
    FROM rba_facts.fact_circular_flow
    WHERE series_id IN ('S_DEPOSIT_RATE', 'I_LENDING_RATE');
    
    -- Check temporal alignment with main circular flow data
    RETURN QUERY
    WITH rate_periods AS (
        SELECT MIN(date_value) as min_date, MAX(date_value) as max_date
        FROM rba_facts.fact_circular_flow f
        JOIN rba_dimensions.dim_time dt ON f.time_key = dt.time_key
        WHERE series_id IN ('S_DEPOSIT_RATE', 'I_LENDING_RATE')
    ),
    flow_periods AS (
        SELECT MIN(date_value) as min_date, MAX(date_value) as max_date
        FROM rba_facts.fact_circular_flow f
        JOIN rba_dimensions.dim_time dt ON f.time_key = dt.time_key
        JOIN rba_dimensions.dim_circular_flow_component c ON f.component_key = c.component_key
        WHERE c.component_code IN ('S', 'I')
          AND f.is_primary_series = true
    )
    SELECT 
        'Temporal Alignment'::text,
        CASE 
            WHEN r.min_date <= f.min_date AND r.max_date >= f.max_date THEN 'PASS'::text
            ELSE 'WARNING'::text
        END,
        'Rate data: ' || r.min_date || ' to ' || r.max_date || 
        ', Flow data: ' || f.min_date || ' to ' || f.max_date::text
    FROM rate_periods r, flow_periods f;
    
    -- Check spread relationship
    RETURN QUERY
    WITH recent_spreads AS (
        SELECT 
            AVG(spread_to_cash_rate) as avg_spread,
            MIN(spread_to_cash_rate) as min_spread,
            MAX(spread_to_cash_rate) as max_spread
        FROM rba_facts.fact_interest_rates
        WHERE spread_to_cash_rate IS NOT NULL
    )
    SELECT 
        'Interest Rate Spreads'::text,
        'INFO'::text,
        'Average spread to cash rate: ' || ROUND(avg_spread, 2) || '%, ' ||
        'Range: ' || ROUND(min_spread, 2) || '% to ' || ROUND(max_spread, 2) || '%'::text
    FROM recent_spreads;
END;
$$;
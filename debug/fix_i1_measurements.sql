-- Add measurements for i1 trade data

-- First check what's missing
\echo 'Current measurements:'
SELECT measurement_key, unit_type, unit_description, price_basis, adjustment_type
FROM rba_dimensions.dim_measurement
WHERE unit_description IN ('$ million', 'Per cent')
  AND adjustment_type = 'Seasonally adjusted'
ORDER BY unit_type, price_basis;

-- Add missing measurements for i1 data
INSERT INTO rba_dimensions.dim_measurement 
(unit_type, unit_description, unit_short_code, price_basis, adjustment_type, is_real_series, is_seasonally_adjusted, decimal_places)
VALUES
-- For Chain Volume Measures (exact match)
('Currency', '$ million', '$m', 'Chain Volume Measures', 'Seasonally adjusted', TRUE, TRUE, 0),
('Percentage', 'Per cent', '%', 'Chain Volume Measures', 'Seasonally adjusted', FALSE, TRUE, 2),
-- For Nominal
('Currency', '$ million', '$m', 'Nominal', 'Seasonally adjusted', FALSE, TRUE, 0),
('Percentage', 'Per cent', '%', 'Nominal', 'Seasonally adjusted', FALSE, TRUE, 2)
ON CONFLICT (unit_type, price_basis, adjustment_type) DO NOTHING;

-- Now retry loading exports
\echo '\nLoading Exports (X)...'
WITH export_insert AS (
    INSERT INTO rba_facts.fact_circular_flow (
        time_key, component_key, source_key, measurement_key,
        series_id, value, is_primary_series, data_quality_flag
    )
    SELECT
        t.time_key,
        c.component_key,
        s.source_key,
        m.measurement_key,
        st.series_id,
        st.value,
        CASE 
            WHEN st.series_id = 'HXEGSCVTOT' THEN TRUE
            ELSE FALSE 
        END as is_primary_series,
        'Good' as data_quality_flag
    FROM rba_staging.i1_trade_bop st
    JOIN rba_dimensions.dim_time t ON st.period_date = t.date_value
    JOIN rba_dimensions.dim_circular_flow_component c ON c.component_code = 'X'
    JOIN rba_dimensions.dim_data_source s ON s.csv_filename = 'i1-data.csv'
    JOIN rba_dimensions.dim_measurement m ON
        m.unit_description = st.unit AND
        m.price_basis = st.price_basis AND
        m.adjustment_type = st.adjustment_type
    WHERE st.extract_date = (SELECT MAX(extract_date) FROM rba_staging.i1_trade_bop)
      AND st.value IS NOT NULL
      AND st.series_description LIKE 'Exports of%'
    ON CONFLICT (time_key, component_key, source_key, measurement_key, series_id)
    DO UPDATE SET
        value = EXCLUDED.value,
        updated_at = CURRENT_TIMESTAMP
    RETURNING series_id
)
SELECT COUNT(DISTINCT series_id) as series_loaded, COUNT(*) as rows_loaded FROM export_insert;

-- Load imports
\echo '\nLoading Imports (M)...'
WITH import_insert AS (
    INSERT INTO rba_facts.fact_circular_flow (
        time_key, component_key, source_key, measurement_key,
        series_id, value, is_primary_series, data_quality_flag
    )
    SELECT
        t.time_key,
        c.component_key,
        s.source_key,
        m.measurement_key,
        st.series_id,
        st.value,
        CASE 
            WHEN st.series_id = 'HMIGSCVTOT' THEN TRUE
            ELSE FALSE 
        END as is_primary_series,
        'Good' as data_quality_flag
    FROM rba_staging.i1_trade_bop st
    JOIN rba_dimensions.dim_time t ON st.period_date = t.date_value
    JOIN rba_dimensions.dim_circular_flow_component c ON c.component_code = 'M'
    JOIN rba_dimensions.dim_data_source s ON s.csv_filename = 'i1-data.csv'
    JOIN rba_dimensions.dim_measurement m ON
        m.unit_description = st.unit AND
        m.price_basis = st.price_basis AND
        m.adjustment_type = st.adjustment_type
    WHERE st.extract_date = (SELECT MAX(extract_date) FROM rba_staging.i1_trade_bop)
      AND st.value IS NOT NULL
      AND st.series_description LIKE 'Imports of%'
    ON CONFLICT (time_key, component_key, source_key, measurement_key, series_id)
    DO UPDATE SET
        value = EXCLUDED.value,
        updated_at = CURRENT_TIMESTAMP
    RETURNING series_id
)
SELECT COUNT(DISTINCT series_id) as series_loaded, COUNT(*) as rows_loaded FROM import_insert;

-- Final check
\echo '\nFinal status for all components:'
SELECT 
    c.component_code,
    c.component_name,
    COUNT(DISTINCT f.series_id) as series,
    COUNT(*) as rows
FROM rba_dimensions.dim_circular_flow_component c
LEFT JOIN rba_facts.fact_circular_flow f ON c.component_key = f.component_key
GROUP BY c.component_code, c.component_name
ORDER BY c.component_code;
-- Load X (Exports) and M (Imports) from i1_trade_bop

-- First check what we're working with
\echo 'Series matching Exports:'
SELECT series_id, series_description 
FROM rba_staging.i1_trade_bop 
WHERE series_description LIKE 'Exports of%' 
  AND extract_date = (SELECT MAX(extract_date) FROM rba_staging.i1_trade_bop)
LIMIT 5;

\echo '\nSeries matching Imports:'
SELECT series_id, series_description 
FROM rba_staging.i1_trade_bop 
WHERE series_description LIKE 'Imports of%'
  AND extract_date = (SELECT MAX(extract_date) FROM rba_staging.i1_trade_bop)
LIMIT 5;

-- Load Exports (X)
\echo '\nLoading Exports (X)...'
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
        WHEN st.series_id = 'HXEGSCVTOT' THEN TRUE  -- Primary total exports series
        ELSE FALSE 
    END as is_primary_series,
    'Good' as data_quality_flag
FROM rba_staging.i1_trade_bop st
JOIN rba_dimensions.dim_time t ON st.period_date = t.date_value
JOIN rba_dimensions.dim_circular_flow_component c ON c.component_code = 'X'
JOIN rba_dimensions.dim_data_source s ON s.csv_filename = 'i1-data.csv'
JOIN rba_dimensions.dim_measurement m ON
    TRIM(m.unit_description) = TRIM(st.unit) AND
    m.price_basis = COALESCE(st.price_basis, 'Current Prices') AND
    m.adjustment_type = st.adjustment_type
WHERE st.extract_date = (SELECT MAX(extract_date) FROM rba_staging.i1_trade_bop)
  AND st.value IS NOT NULL
  AND st.series_description LIKE 'Exports of%'
ON CONFLICT (time_key, component_key, source_key, measurement_key, series_id)
DO UPDATE SET
    value = EXCLUDED.value,
    updated_at = CURRENT_TIMESTAMP;

-- Load Imports (M)
\echo '\nLoading Imports (M)...'
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
        WHEN st.series_id = 'HMIGSCVTOT' THEN TRUE  -- Primary total imports series
        ELSE FALSE 
    END as is_primary_series,
    'Good' as data_quality_flag
FROM rba_staging.i1_trade_bop st
JOIN rba_dimensions.dim_time t ON st.period_date = t.date_value
JOIN rba_dimensions.dim_circular_flow_component c ON c.component_code = 'M'
JOIN rba_dimensions.dim_data_source s ON s.csv_filename = 'i1-data.csv'
JOIN rba_dimensions.dim_measurement m ON
    TRIM(m.unit_description) = TRIM(st.unit) AND
    m.price_basis = COALESCE(st.price_basis, 'Current Prices') AND
    m.adjustment_type = st.adjustment_type
WHERE st.extract_date = (SELECT MAX(extract_date) FROM rba_staging.i1_trade_bop)
  AND st.value IS NOT NULL
  AND st.series_description LIKE 'Imports of%'
ON CONFLICT (time_key, component_key, source_key, measurement_key, series_id)
DO UPDATE SET
    value = EXCLUDED.value,
    updated_at = CURRENT_TIMESTAMP;

-- Check results
\echo '\nComponent status after loading:'
SELECT 
    c.component_code,
    c.component_name,
    COUNT(DISTINCT f.series_id) as series,
    COUNT(*) as rows,
    MIN(t.date_value) as earliest,
    MAX(t.date_value) as latest
FROM rba_facts.fact_circular_flow f
JOIN rba_dimensions.dim_circular_flow_component c ON f.component_key = c.component_key
JOIN rba_dimensions.dim_time t ON f.time_key = t.time_key
WHERE c.component_code IN ('X', 'M')
GROUP BY c.component_code, c.component_name
ORDER BY c.component_code;
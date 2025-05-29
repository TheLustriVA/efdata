-- Phase 2: Create frequency-specific views

\echo '=== PHASE 2: Creating frequency-specific views ==='

-- Monthly components view
CREATE OR REPLACE VIEW rba_analytics.v_monthly_components AS
SELECT 
    t.date_value,
    t.year,
    t.month,
    t.quarter,
    t.quarter_label,
    c.component_code,
    c.component_name,
    s.rba_table_code as source,
    f.series_id,
    f.value,
    m.unit_description,
    m.price_basis
FROM rba_facts.fact_circular_flow f
JOIN rba_dimensions.dim_time t ON f.time_key = t.time_key
JOIN rba_dimensions.dim_circular_flow_component c ON f.component_key = c.component_key
JOIN rba_dimensions.dim_data_source s ON f.source_key = s.source_key
JOIN rba_dimensions.dim_measurement m ON f.measurement_key = m.measurement_key
WHERE f.data_frequency = 'Monthly'
  AND f.is_primary_series = TRUE
ORDER BY t.date_value DESC, c.component_code;

-- Quarterly components view
CREATE OR REPLACE VIEW rba_analytics.v_quarterly_components AS
SELECT 
    t.date_value,
    t.year,
    t.quarter,
    t.quarter_label,
    c.component_code,
    c.component_name,
    s.rba_table_code as source,
    f.series_id,
    f.value,
    m.unit_description,
    m.price_basis
FROM rba_facts.fact_circular_flow f
JOIN rba_dimensions.dim_time t ON f.time_key = t.time_key
JOIN rba_dimensions.dim_circular_flow_component c ON f.component_key = c.component_key
JOIN rba_dimensions.dim_data_source s ON f.source_key = s.source_key
JOIN rba_dimensions.dim_measurement m ON f.measurement_key = m.measurement_key
WHERE f.data_frequency = 'Quarterly'
  AND f.is_primary_series = TRUE
  AND t.is_quarter_end = TRUE
ORDER BY t.date_value DESC, c.component_code;

-- Test the views
\echo '\nSample monthly data (last 5 records):'
SELECT date_value, component_code, source, ROUND(value::numeric) as value
FROM rba_analytics.v_monthly_components
LIMIT 5;

\echo '\nSample quarterly data (last 5 records):'
SELECT date_value, quarter_label, component_code, source, ROUND(value::numeric) as value
FROM rba_analytics.v_quarterly_components
LIMIT 5;
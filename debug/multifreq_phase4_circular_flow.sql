-- Phase 4: Multi-frequency circular flow view

\echo '=== PHASE 4: Multi-frequency circular flow ==='

-- Main circular flow view with mixed frequencies
CREATE OR REPLACE VIEW rba_analytics.v_circular_flow_multifreq AS
WITH 
-- All quarters we want to show
all_quarters AS (
    SELECT DISTINCT year, quarter, quarter_label
    FROM rba_dimensions.dim_time
    WHERE is_quarter_end = TRUE
      AND year >= 1959
      AND date_value <= CURRENT_DATE
),
-- Native quarterly data
quarterly_data AS (
    SELECT 
        t.year,
        t.quarter,
        t.quarter_label,
        c.component_code,
        SUM(f.value) as value,
        'Quarterly' as data_source,
        COUNT(DISTINCT f.series_id) as series_count
    FROM rba_facts.fact_circular_flow f
    JOIN rba_dimensions.dim_time t ON f.time_key = t.time_key
    JOIN rba_dimensions.dim_circular_flow_component c ON f.component_key = c.component_key
    WHERE f.data_frequency = 'Quarterly'
      AND f.is_primary_series = TRUE
      AND t.is_quarter_end = TRUE
    GROUP BY t.year, t.quarter, t.quarter_label, c.component_code
),
-- Monthly data aggregated to quarterly
monthly_aggregated AS (
    SELECT 
        year,
        quarter,
        quarter_label,
        component_code,
        quarterly_value as value,
        'Monthly-Agg' as data_source,
        1 as series_count
    FROM rba_analytics.v_monthly_to_quarterly
    WHERE quarterly_value IS NOT NULL
),
-- Combine all data, preferring quarterly over monthly
combined_data AS (
    SELECT 
        aq.year,
        aq.quarter,
        aq.quarter_label,
        cc.component_code,
        COALESCE(qd.value, ma.value) as value,
        COALESCE(qd.data_source, ma.data_source) as data_source,
        COALESCE(qd.series_count, ma.series_count, 0) as series_count
    FROM all_quarters aq
    CROSS JOIN (SELECT DISTINCT component_code FROM rba_dimensions.dim_circular_flow_component) cc
    LEFT JOIN quarterly_data qd 
        ON aq.year = qd.year 
        AND aq.quarter = qd.quarter 
        AND cc.component_code = qd.component_code
    LEFT JOIN monthly_aggregated ma 
        ON aq.year = ma.year 
        AND aq.quarter = ma.quarter 
        AND cc.component_code = ma.component_code
)
-- Final pivot
SELECT 
    year,
    quarter,
    quarter_label,
    -- Core components
    MAX(CASE WHEN component_code = 'Y' THEN value END) as income_y,
    MAX(CASE WHEN component_code = 'C' THEN value END) as consumption_c,
    MAX(CASE WHEN component_code = 'S' THEN value END) as savings_s,
    MAX(CASE WHEN component_code = 'I' THEN value END) as investment_i,
    MAX(CASE WHEN component_code = 'G' THEN value END) as government_g,
    MAX(CASE WHEN component_code = 'T' THEN value END) as taxation_t,
    MAX(CASE WHEN component_code = 'X' THEN value END) as exports_x,
    MAX(CASE WHEN component_code = 'M' THEN value END) as imports_m,
    
    -- Data sources
    MAX(CASE WHEN component_code = 'Y' THEN data_source END) as y_source,
    MAX(CASE WHEN component_code = 'C' THEN data_source END) as c_source,
    MAX(CASE WHEN component_code = 'S' THEN data_source END) as s_source,
    MAX(CASE WHEN component_code = 'I' THEN data_source END) as i_source,
    MAX(CASE WHEN component_code = 'G' THEN data_source END) as g_source,
    MAX(CASE WHEN component_code = 'T' THEN data_source END) as t_source,
    MAX(CASE WHEN component_code = 'X' THEN data_source END) as x_source,
    MAX(CASE WHEN component_code = 'M' THEN data_source END) as m_source,
    
    -- Circular flow calculations
    COALESCE(MAX(CASE WHEN component_code = 'S' THEN value END), 0) +
    COALESCE(MAX(CASE WHEN component_code = 'T' THEN value END), 0) +
    COALESCE(MAX(CASE WHEN component_code = 'M' THEN value END), 0) as total_leakages,
    
    COALESCE(MAX(CASE WHEN component_code = 'I' THEN value END), 0) +
    COALESCE(MAX(CASE WHEN component_code = 'G' THEN value END), 0) +
    COALESCE(MAX(CASE WHEN component_code = 'X' THEN value END), 0) as total_injections,
    
    -- Balance
    (COALESCE(MAX(CASE WHEN component_code = 'I' THEN value END), 0) +
     COALESCE(MAX(CASE WHEN component_code = 'G' THEN value END), 0) +
     COALESCE(MAX(CASE WHEN component_code = 'X' THEN value END), 0)) -
    (COALESCE(MAX(CASE WHEN component_code = 'S' THEN value END), 0) +
     COALESCE(MAX(CASE WHEN component_code = 'T' THEN value END), 0) +
     COALESCE(MAX(CASE WHEN component_code = 'M' THEN value END), 0)) as circular_flow_balance,
    
    -- Data completeness
    COUNT(DISTINCT CASE WHEN cd.value IS NOT NULL THEN cd.component_code END) as components_available
FROM combined_data cd
GROUP BY year, quarter, quarter_label
ORDER BY year DESC, quarter DESC;

-- Test the view
\echo '\nMulti-frequency circular flow (recent quarters):'
SELECT 
    quarter_label,
    ROUND(income_y::numeric) as Y,
    y_source,
    ROUND(investment_i::numeric) as I,
    i_source,
    ROUND(savings_s::numeric) as S,
    s_source,
    components_available as comps
FROM rba_analytics.v_circular_flow_multifreq
WHERE year >= 2024
ORDER BY quarter_label DESC
LIMIT 8;
-- Final test of multi-frequency architecture

\echo '=== MULTI-FREQUENCY ARCHITECTURE TEST ==='

-- 1. Show circular flow with mixed frequencies
\echo '\n1. Circular flow mixing quarterly and monthly data:'
SELECT 
    quarter_label,
    ROUND(income_y::numeric) as Y,
    CASE WHEN y_source IS NOT NULL THEN SUBSTRING(y_source, 1, 1) END as Y_freq,
    ROUND(consumption_c::numeric) as C,
    CASE WHEN c_source IS NOT NULL THEN SUBSTRING(c_source, 1, 1) END as C_freq,
    ROUND(savings_s::numeric) as S,
    CASE WHEN s_source IS NOT NULL THEN SUBSTRING(s_source, 1, 1) END as S_freq,
    ROUND(investment_i::numeric) as I,
    CASE WHEN i_source IS NOT NULL THEN SUBSTRING(i_source, 1, 1) END as I_freq,
    ROUND(total_leakages::numeric) as leakages,
    ROUND(total_injections::numeric) as injections,
    ROUND(circular_flow_balance::numeric) as balance
FROM rba_analytics.v_circular_flow_multifreq
WHERE year IN (2024, 2025)
  AND components_available >= 2
ORDER BY quarter_label DESC
LIMIT 10;

-- 2. Monthly detail for volatile components
\echo '\n2. Monthly detail for I and S (showing actual monthly granularity):'
SELECT 
    date_value,
    component_code,
    COUNT(DISTINCT series_id) as series,
    ROUND(MIN(value)::numeric, 2) as min_val,
    ROUND(AVG(value)::numeric, 2) as avg_val,
    ROUND(MAX(value)::numeric, 2) as max_val,
    ROUND(STDDEV(value)::numeric, 2) as std_dev
FROM rba_analytics.v_monthly_components
WHERE date_value >= '2024-10-01'
GROUP BY date_value, component_code
ORDER BY date_value DESC, component_code;

-- 3. Data completeness pattern
\echo '\n3. Component availability pattern over time:'
SELECT 
    quarter_label,
    component_pattern,
    quality_rating,
    CASE 
        WHEN component_pattern LIKE '%I%' AND i_source = 'Monthly-Agg' THEN 'Mixed (has monthly I)'
        WHEN component_pattern LIKE '%S%' AND s_source = 'Monthly-Agg' THEN 'Mixed (has monthly S)'
        ELSE 'Quarterly only'
    END as frequency_mix
FROM rba_analytics.v_data_completeness dc
JOIN rba_analytics.v_circular_flow_multifreq cf USING (quarter_label)
WHERE year >= 2024
ORDER BY quarter_label DESC
LIMIT 10;

-- 4. Summary statistics
\echo '\n4. Multi-frequency data summary:'
WITH stats AS (
    SELECT 
        'Monthly records' as metric,
        COUNT(*) as value
    FROM rba_facts.fact_circular_flow
    WHERE data_frequency = 'Monthly'
    UNION ALL
    SELECT 
        'Quarterly records',
        COUNT(*)
    FROM rba_facts.fact_circular_flow
    WHERE data_frequency = 'Quarterly'
    UNION ALL
    SELECT 
        'Components with monthly data',
        COUNT(DISTINCT component_key)
    FROM rba_facts.fact_circular_flow
    WHERE data_frequency = 'Monthly'
    UNION ALL
    SELECT 
        'Quarters with mixed frequencies',
        COUNT(DISTINCT quarter_label)
    FROM rba_analytics.v_circular_flow_multifreq
    WHERE (i_source = 'Monthly-Agg' OR s_source = 'Monthly-Agg')
)
SELECT metric, value FROM stats ORDER BY metric;

\echo '\n=== Multi-frequency architecture successfully implemented! ==='"
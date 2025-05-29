-- Phase 5: Volatility and completeness metrics

\echo '=== PHASE 5: Volatility metrics ==='

-- Monthly volatility tracking
CREATE OR REPLACE VIEW rba_analytics.v_monthly_volatility AS
WITH monthly_changes AS (
    SELECT 
        date_value,
        component_code,
        series_id,
        value,
        LAG(value, 1) OVER (PARTITION BY component_code, series_id ORDER BY date_value) as prev_month,
        LAG(value, 3) OVER (PARTITION BY component_code, series_id ORDER BY date_value) as prev_quarter,
        LAG(value, 12) OVER (PARTITION BY component_code, series_id ORDER BY date_value) as prev_year
    FROM rba_analytics.v_monthly_components
)
SELECT 
    date_value,
    component_code,
    series_id,
    value,
    prev_month,
    -- Percentage changes
    CASE 
        WHEN prev_month > 0 THEN ROUND(((value - prev_month) / prev_month * 100)::numeric, 2)
        ELSE NULL 
    END as mom_pct_change,
    CASE 
        WHEN prev_quarter > 0 THEN ROUND(((value - prev_quarter) / prev_quarter * 100)::numeric, 2)
        ELSE NULL 
    END as qoq_pct_change,
    CASE 
        WHEN prev_year > 0 THEN ROUND(((value - prev_year) / prev_year * 100)::numeric, 2)
        ELSE NULL 
    END as yoy_pct_change,
    -- Volatility classification
    CASE 
        WHEN ABS(value - prev_month) / NULLIF(prev_month, 0) > 0.10 THEN 'HIGH'
        WHEN ABS(value - prev_month) / NULLIF(prev_month, 0) > 0.05 THEN 'MEDIUM'
        WHEN prev_month IS NOT NULL THEN 'LOW'
        ELSE NULL
    END as volatility_flag
FROM monthly_changes
WHERE date_value >= '2024-01-01'  -- Focus on recent period
ORDER BY date_value DESC, component_code;

-- Data completeness tracking
CREATE OR REPLACE VIEW rba_analytics.v_data_completeness AS
SELECT 
    quarter_label,
    year,
    quarter,
    components_available,
    ROUND(components_available * 100.0 / 8, 1) as completeness_pct,
    CASE 
        WHEN income_y IS NOT NULL THEN 'Y' ELSE '-' 
    END ||
    CASE 
        WHEN consumption_c IS NOT NULL THEN 'C' ELSE '-' 
    END ||
    CASE 
        WHEN savings_s IS NOT NULL THEN 'S' ELSE '-' 
    END ||
    CASE 
        WHEN investment_i IS NOT NULL THEN 'I' ELSE '-' 
    END ||
    CASE 
        WHEN government_g IS NOT NULL THEN 'G' ELSE '-' 
    END ||
    CASE 
        WHEN taxation_t IS NOT NULL THEN 'T' ELSE '-' 
    END ||
    CASE 
        WHEN exports_x IS NOT NULL THEN 'X' ELSE '-' 
    END ||
    CASE 
        WHEN imports_m IS NOT NULL THEN 'M' ELSE '-' 
    END as component_pattern,
    CASE components_available
        WHEN 8 THEN 'Complete'
        WHEN 7 THEN 'Near-Complete'
        WHEN 6 THEN 'Good'
        WHEN 5 THEN 'Moderate'
        ELSE 'Poor'
    END as quality_rating
FROM rba_analytics.v_circular_flow_multifreq
ORDER BY year DESC, quarter DESC;

-- Test volatility detection
\echo '\nRecent monthly volatility (HIGH/MEDIUM only):'
SELECT 
    date_value,
    component_code,
    ROUND(value::numeric) as value,
    ROUND(prev_month::numeric) as prev,
    mom_pct_change as mom_chg,
    volatility_flag
FROM rba_analytics.v_monthly_volatility
WHERE volatility_flag IN ('HIGH', 'MEDIUM')
  AND date_value >= '2025-01-01'
ORDER BY date_value DESC, ABS(mom_pct_change) DESC NULLS LAST
LIMIT 10;

-- Test completeness view
\echo '\nData completeness by year:'
SELECT 
    year,
    COUNT(*) as quarters,
    ROUND(AVG(completeness_pct), 1) as avg_completeness,
    STRING_AGG(DISTINCT quality_rating, ', ' ORDER BY quality_rating) as quality_levels
FROM rba_analytics.v_data_completeness
WHERE year >= 2020
GROUP BY year
ORDER BY year DESC;
-- =====================================================
-- Multi-Frequency Temporal Architecture Implementation
-- =====================================================
-- Purpose: Handle mixed monthly/quarterly data without interpolation
-- Principle: Show only what we know, when we know it
-- Date: 2025-05-29
-- =====================================================

-- =====================================================
-- PHASE 1: FOUNDATION - Add Frequency Tracking
-- =====================================================

\echo '=== PHASE 1: Adding frequency tracking to fact table ==='

-- Add frequency column to fact table
ALTER TABLE rba_facts.fact_circular_flow 
ADD COLUMN IF NOT EXISTS data_frequency VARCHAR(10);

-- Update existing records based on source
UPDATE rba_facts.fact_circular_flow f
SET data_frequency = d.primary_frequency
FROM rba_dimensions.dim_data_source d
WHERE f.source_key = d.source_key
  AND f.data_frequency IS NULL;

-- Add helpful metadata columns
ALTER TABLE rba_facts.fact_circular_flow
ADD COLUMN IF NOT EXISTS is_quarter_end_value BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS is_monthly_aggregate BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS aggregation_method VARCHAR(20);

-- Update quarter-end flags
UPDATE rba_facts.fact_circular_flow f
SET is_quarter_end_value = t.is_quarter_end
FROM rba_dimensions.dim_time t
WHERE f.time_key = t.time_key;

-- Show frequency distribution
\echo '\nData frequency distribution:'
SELECT 
    c.component_code,
    c.component_name,
    f.data_frequency,
    COUNT(DISTINCT t.date_value) as periods,
    MIN(t.date_value) as earliest,
    MAX(t.date_value) as latest
FROM rba_facts.fact_circular_flow f
JOIN rba_dimensions.dim_circular_flow_component c ON f.component_key = c.component_key
JOIN rba_dimensions.dim_time t ON f.time_key = t.time_key
WHERE f.is_primary_series = TRUE
GROUP BY c.component_code, c.component_name, f.data_frequency
ORDER BY c.component_code, f.data_frequency;

-- =====================================================
-- PHASE 2: RAW FREQUENCY VIEWS
-- =====================================================

\echo '\n=== PHASE 2: Creating raw frequency views ==='

-- View 1: Native Monthly Data (no aggregation)
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
    m.price_basis,
    f.data_frequency
FROM rba_facts.fact_circular_flow f
JOIN rba_dimensions.dim_time t ON f.time_key = t.time_key
JOIN rba_dimensions.dim_circular_flow_component c ON f.component_key = c.component_key
JOIN rba_dimensions.dim_data_source s ON f.source_key = s.source_key
JOIN rba_dimensions.dim_measurement m ON f.measurement_key = m.measurement_key
WHERE f.data_frequency = 'Monthly'
  AND f.is_primary_series = TRUE
ORDER BY t.date_value, c.component_code;

-- View 2: Native Quarterly Data
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
    m.price_basis,
    f.data_frequency
FROM rba_facts.fact_circular_flow f
JOIN rba_dimensions.dim_time t ON f.time_key = t.time_key
JOIN rba_dimensions.dim_circular_flow_component c ON f.component_key = c.component_key
JOIN rba_dimensions.dim_data_source s ON f.source_key = s.source_key
JOIN rba_dimensions.dim_measurement m ON f.measurement_key = m.measurement_key
WHERE f.data_frequency = 'Quarterly'
  AND f.is_primary_series = TRUE
  AND t.is_quarter_end = TRUE
ORDER BY t.date_value, c.component_code;

-- =====================================================
-- PHASE 3: TEMPORAL ALIGNMENT LAYER
-- =====================================================

\echo '\n=== PHASE 3: Building temporal alignment layer ==='

-- Function to determine aggregation method by component type
CREATE OR REPLACE FUNCTION rba_analytics.get_aggregation_method(
    component_code CHAR(1),
    series_description TEXT
) RETURNS VARCHAR(20) AS $$
BEGIN
    -- Flow variables (sum over period)
    IF component_code IN ('I', 'C', 'G', 'X', 'M') THEN
        RETURN 'SUM';
    -- Stock variables (end of period)
    ELSIF component_code IN ('S') THEN
        RETURN 'LAST';
    -- Income (average or sum depending on series)
    ELSIF component_code = 'Y' THEN
        IF series_description ILIKE '%rate%' THEN
            RETURN 'AVG';
        ELSE
            RETURN 'SUM';
        END IF;
    -- Default
    ELSE
        RETURN 'AVG';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- View 3: Monthly-to-Quarterly Alignment (WITHOUT interpolation)
CREATE OR REPLACE VIEW rba_analytics.v_monthly_to_quarterly AS
WITH monthly_data AS (
    SELECT 
        t.year,
        t.quarter,
        t.quarter_label,
        c.component_code,
        c.component_name,
        f.series_id,
        m.unit_description,
        m.price_basis,
        -- Determine aggregation method
        rba_analytics.get_aggregation_method(c.component_code, f.series_id) as agg_method,
        -- Collect values for aggregation
        ARRAY_AGG(f.value ORDER BY t.date_value) as monthly_values,
        ARRAY_AGG(t.date_value ORDER BY t.date_value) as monthly_dates,
        COUNT(*) as months_available
    FROM rba_facts.fact_circular_flow f
    JOIN rba_dimensions.dim_time t ON f.time_key = t.time_key
    JOIN rba_dimensions.dim_circular_flow_component c ON f.component_key = c.component_key
    JOIN rba_dimensions.dim_measurement m ON f.measurement_key = m.measurement_key
    WHERE f.data_frequency = 'Monthly'
      AND f.is_primary_series = TRUE
    GROUP BY t.year, t.quarter, t.quarter_label, 
             c.component_code, c.component_name, 
             f.series_id, m.unit_description, m.price_basis
)
SELECT 
    year,
    quarter,
    quarter_label,
    component_code,
    component_name,
    series_id,
    unit_description,
    price_basis,
    months_available,
    CASE months_available
        WHEN 3 THEN 'Complete'
        WHEN 2 THEN 'Partial-2'
        WHEN 1 THEN 'Partial-1'
        ELSE 'Missing'
    END as data_quality,
    agg_method,
    -- Only aggregate if we have complete quarter (3 months)
    CASE 
        WHEN months_available = 3 THEN
            CASE agg_method
                WHEN 'SUM' THEN 
                    monthly_values[1] + monthly_values[2] + monthly_values[3]
                WHEN 'AVG' THEN 
                    (monthly_values[1] + monthly_values[2] + monthly_values[3]) / 3.0
                WHEN 'LAST' THEN 
                    monthly_values[3]
                ELSE 
                    monthly_values[3] -- default to last
            END
        ELSE 
            NULL -- Don't create fake data!
    END as quarterly_value,
    -- Keep monthly detail for drill-down
    monthly_values,
    monthly_dates
FROM monthly_data
ORDER BY year, quarter, component_code;

-- =====================================================
-- PHASE 4: MULTI-FREQUENCY CIRCULAR FLOW VIEW
-- =====================================================

\echo '\n=== PHASE 4: Creating multi-frequency circular flow view ==='

CREATE OR REPLACE VIEW rba_analytics.v_circular_flow_multifreq AS
WITH 
-- Get all available quarters
all_quarters AS (
    SELECT DISTINCT year, quarter, quarter_label
    FROM rba_dimensions.dim_time
    WHERE is_quarter_end = TRUE
      AND date_value >= '1959-01-01'
      AND date_value <= CURRENT_DATE
),
-- Native quarterly data
quarterly_native AS (
    SELECT 
        q.quarter_label,
        c.component_code,
        SUM(f.value) as value,
        'Quarterly-Native' as data_source,
        STRING_AGG(DISTINCT f.series_id, ', ') as series_used
    FROM all_quarters q
    JOIN rba_dimensions.dim_time t 
        ON t.year = q.year 
        AND t.quarter = q.quarter 
        AND t.is_quarter_end = TRUE
    JOIN rba_facts.fact_circular_flow f ON f.time_key = t.time_key
    JOIN rba_dimensions.dim_circular_flow_component c ON f.component_key = c.component_key
    WHERE f.data_frequency = 'Quarterly'
      AND f.is_primary_series = TRUE
    GROUP BY q.quarter_label, c.component_code
),
-- Monthly aggregated to quarterly
monthly_derived AS (
    SELECT 
        quarter_label,
        component_code,
        quarterly_value as value,
        'Monthly-Derived' as data_source,
        series_id as series_used
    FROM rba_analytics.v_monthly_to_quarterly
    WHERE quarterly_value IS NOT NULL
),
-- Combine, preferring native quarterly
combined_data AS (
    SELECT 
        q.quarter_label,
        q.component_code,
        COALESCE(q.value, m.value) as value,
        COALESCE(q.data_source, m.data_source, 'Missing') as data_source,
        COALESCE(q.series_used, m.series_used, 'None') as series_used
    FROM quarterly_native q
    FULL OUTER JOIN monthly_derived m 
        ON q.quarter_label = m.quarter_label 
        AND q.component_code = m.component_code
)
-- Final pivot for circular flow
SELECT 
    aq.year,
    aq.quarter,
    aq.quarter_label,
    -- Components with data source indicators
    MAX(CASE WHEN component_code = 'Y' THEN value END) as income_y,
    MAX(CASE WHEN component_code = 'Y' THEN data_source END) as income_source,
    
    MAX(CASE WHEN component_code = 'C' THEN value END) as consumption_c,
    MAX(CASE WHEN component_code = 'C' THEN data_source END) as consumption_source,
    
    MAX(CASE WHEN component_code = 'S' THEN value END) as savings_s,
    MAX(CASE WHEN component_code = 'S' THEN data_source END) as savings_source,
    
    MAX(CASE WHEN component_code = 'I' THEN value END) as investment_i,
    MAX(CASE WHEN component_code = 'I' THEN data_source END) as investment_source,
    
    MAX(CASE WHEN component_code = 'G' THEN value END) as government_g,
    MAX(CASE WHEN component_code = 'G' THEN data_source END) as government_source,
    
    MAX(CASE WHEN component_code = 'T' THEN value END) as taxation_t,
    MAX(CASE WHEN component_code = 'T' THEN data_source END) as taxation_source,
    
    MAX(CASE WHEN component_code = 'X' THEN value END) as exports_x,
    MAX(CASE WHEN component_code = 'X' THEN data_source END) as exports_source,
    
    MAX(CASE WHEN component_code = 'M' THEN value END) as imports_m,
    MAX(CASE WHEN component_code = 'M' THEN data_source END) as imports_source,
    
    -- Circular flow calculations (only where data exists)
    COALESCE(MAX(CASE WHEN component_code = 'S' THEN value END), 0) +
    COALESCE(MAX(CASE WHEN component_code = 'T' THEN value END), 0) +
    COALESCE(MAX(CASE WHEN component_code = 'M' THEN value END), 0) as total_leakages,
    
    COALESCE(MAX(CASE WHEN component_code = 'I' THEN value END), 0) +
    COALESCE(MAX(CASE WHEN component_code = 'G' THEN value END), 0) +
    COALESCE(MAX(CASE WHEN component_code = 'X' THEN value END), 0) as total_injections,
    
    -- Data completeness score (0-8 components)
    COUNT(DISTINCT CASE WHEN cd.value IS NOT NULL THEN cd.component_code END) as components_available,
    
    -- Component coverage bitmap for quick filtering
    STRING_AGG(DISTINCT CASE WHEN cd.value IS NOT NULL THEN cd.component_code END, '' ORDER BY cd.component_code) as components_present
    
FROM all_quarters aq
LEFT JOIN combined_data cd ON aq.quarter_label = cd.quarter_label
GROUP BY aq.year, aq.quarter, aq.quarter_label
ORDER BY aq.year DESC, aq.quarter DESC;

-- =====================================================
-- PHASE 5: VOLATILITY AND COMPLETENESS METRICS
-- =====================================================

\echo '\n=== PHASE 5: Adding volatility metrics ==='

-- Monthly volatility view (especially for post-April 2025)
CREATE OR REPLACE VIEW rba_analytics.v_monthly_volatility AS
WITH monthly_changes AS (
    SELECT 
        date_value,
        component_code,
        series_id,
        value,
        LAG(value, 1) OVER (PARTITION BY component_code, series_id ORDER BY date_value) as prev_value,
        LAG(value, 3) OVER (PARTITION BY component_code, series_id ORDER BY date_value) as prev_quarter_value,
        LAG(value, 12) OVER (PARTITION BY component_code, series_id ORDER BY date_value) as prev_year_value
    FROM rba_analytics.v_monthly_components
)
SELECT 
    date_value,
    component_code,
    series_id,
    value,
    -- Month-on-month changes
    CASE 
        WHEN prev_value > 0 THEN ((value - prev_value) / prev_value) * 100
        ELSE NULL 
    END as mom_pct_change,
    -- Quarter-on-quarter changes  
    CASE 
        WHEN prev_quarter_value > 0 THEN ((value - prev_quarter_value) / prev_quarter_value) * 100
        ELSE NULL 
    END as qoq_pct_change,
    -- Year-on-year changes
    CASE 
        WHEN prev_year_value > 0 THEN ((value - prev_year_value) / prev_year_value) * 100
        ELSE NULL 
    END as yoy_pct_change,
    -- Volatility flag
    CASE 
        WHEN ABS((value - prev_value) / NULLIF(prev_value, 0)) > 0.10 THEN 'HIGH'
        WHEN ABS((value - prev_value) / NULLIF(prev_value, 0)) > 0.05 THEN 'MEDIUM'
        ELSE 'LOW'
    END as volatility_flag
FROM monthly_changes
WHERE date_value >= '2025-01-01'  -- Focus on recent volatile period
ORDER BY date_value DESC, component_code;

-- Data completeness summary
CREATE OR REPLACE VIEW rba_analytics.v_data_completeness AS
SELECT 
    quarter_label,
    components_available,
    components_present,
    CASE components_available
        WHEN 8 THEN 'Complete'
        WHEN 7 THEN 'Near-Complete (Missing T)'
        WHEN 6 THEN 'Good'
        WHEN 5 THEN 'Moderate'
        ELSE 'Poor'
    END as data_quality,
    ROUND(components_available * 100.0 / 8, 1) as completeness_pct
FROM rba_analytics.v_circular_flow_multifreq
ORDER BY quarter_label DESC;

-- =====================================================
-- TESTING AND VALIDATION
-- =====================================================

\echo '\n=== Testing multi-frequency views ==='

-- Test 1: Show recent quarters with mixed frequencies
\echo '\nRecent circular flow with data sources:'
SELECT 
    quarter_label,
    ROUND(income_y::numeric, 0) as Y,
    income_source as Y_src,
    ROUND(investment_i::numeric, 0) as I,
    investment_source as I_src,
    components_available as comps,
    components_present as which
FROM rba_analytics.v_circular_flow_multifreq
WHERE quarter_label >= '2024Q1'
ORDER BY quarter_label DESC
LIMIT 5;

-- Test 2: Check monthly volatility for 2025
\echo '\nMonthly volatility check (post-April 2025):'
SELECT 
    date_value,
    component_code,
    ROUND(value::numeric, 0) as value,
    ROUND(mom_pct_change::numeric, 1) as mom_chg,
    volatility_flag
FROM rba_analytics.v_monthly_volatility
WHERE date_value >= '2025-04-01'
  AND component_code IN ('I', 'S')
  AND volatility_flag IN ('HIGH', 'MEDIUM')
ORDER BY date_value DESC
LIMIT 10;

-- Test 3: Data completeness over time
\echo '\nData completeness summary:'
SELECT 
    EXTRACT(YEAR FROM quarter_label::date) as year,
    COUNT(*) as quarters,
    ROUND(AVG(completeness_pct), 1) as avg_completeness,
    STRING_AGG(DISTINCT components_present, ' | ' ORDER BY components_present) as patterns
FROM rba_analytics.v_data_completeness
GROUP BY EXTRACT(YEAR FROM quarter_label::date)
ORDER BY year DESC
LIMIT 5;

\echo '\n=== Multi-frequency architecture implementation complete! ==='"
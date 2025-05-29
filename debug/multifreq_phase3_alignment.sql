-- Phase 3: Build temporal alignment layer

\echo '=== PHASE 3: Building temporal alignment ==='

-- Create aggregation method function
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

-- Monthly to quarterly alignment
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
    months_available,
    CASE months_available
        WHEN 3 THEN 'Complete'
        WHEN 2 THEN 'Partial'
        WHEN 1 THEN 'Partial'
        ELSE 'Missing'
    END as data_quality,
    -- Component-specific aggregation
    CASE 
        WHEN months_available = 3 THEN
            CASE component_code
                WHEN 'I' THEN -- Investment: sum
                    monthly_values[1] + monthly_values[2] + monthly_values[3]
                WHEN 'S' THEN -- Savings: last value (stock)
                    monthly_values[3]
                ELSE -- Default: average
                    (monthly_values[1] + monthly_values[2] + monthly_values[3]) / 3.0
            END
        ELSE 
            NULL -- Don't interpolate!
    END as quarterly_value,
    monthly_values,
    monthly_dates
FROM monthly_data
WHERE year >= 2024  -- Focus on recent data for testing
ORDER BY year DESC, quarter DESC, component_code;

-- Test the alignment
\echo '\nMonthly to quarterly alignment (2025 data):'
SELECT 
    quarter_label,
    component_code,
    months_available,
    data_quality,
    ROUND(quarterly_value::numeric) as q_value,
    ROUND(monthly_values[1]::numeric) as m1,
    ROUND(monthly_values[2]::numeric) as m2,
    ROUND(monthly_values[3]::numeric) as m3
FROM rba_analytics.v_monthly_to_quarterly
WHERE year = 2025
ORDER BY quarter DESC, component_code;
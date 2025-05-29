-- Phase 1: Foundation - Add frequency tracking

\echo '=== PHASE 1: Adding frequency tracking ==='

-- Add frequency column
ALTER TABLE rba_facts.fact_circular_flow 
ADD COLUMN IF NOT EXISTS data_frequency VARCHAR(10);

-- Update from data source
UPDATE rba_facts.fact_circular_flow f
SET data_frequency = d.primary_frequency
FROM rba_dimensions.dim_data_source d
WHERE f.source_key = d.source_key
  AND f.data_frequency IS NULL;

-- Add metadata columns
ALTER TABLE rba_facts.fact_circular_flow
ADD COLUMN IF NOT EXISTS is_quarter_end_value BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS is_monthly_aggregate BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS aggregation_method VARCHAR(20);

-- Update quarter-end flags
UPDATE rba_facts.fact_circular_flow f
SET is_quarter_end_value = t.is_quarter_end
FROM rba_dimensions.dim_time t
WHERE f.time_key = t.time_key;

-- Check frequency distribution
\echo '\nFrequency distribution by component:'
SELECT 
    c.component_code,
    f.data_frequency,
    COUNT(*) as records,
    COUNT(DISTINCT t.date_value) as periods
FROM rba_facts.fact_circular_flow f
JOIN rba_dimensions.dim_circular_flow_component c ON f.component_key = c.component_key
JOIN rba_dimensions.dim_time t ON f.time_key = t.time_key
WHERE f.is_primary_series = TRUE
GROUP BY c.component_code, f.data_frequency
ORDER BY c.component_code, f.data_frequency;
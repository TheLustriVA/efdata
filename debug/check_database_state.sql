-- =====================================================
-- Quick Database State Check
-- =====================================================

-- Check what schemas were created
SELECT schema_name 
FROM information_schema.schemata 
WHERE schema_name LIKE 'rba_%' 
ORDER BY schema_name;

-- Check what tables were created in each RBA schema
SELECT 
    schemaname as schema_name,
    tablename as table_name,
    'Table created successfully' as status
FROM pg_tables 
WHERE schemaname LIKE 'rba_%'
ORDER BY schemaname, tablename;

-- Count tables per schema
SELECT 
    schemaname as schema_name,
    COUNT(*) as table_count
FROM pg_tables 
WHERE schemaname LIKE 'rba_%'
GROUP BY schemaname
ORDER BY schemaname;

-- Expected table counts:
-- rba_staging: 8 tables (h1, h2, h3, i1, d1, d2, a1, i3, c1)
-- rba_dimensions: 4 tables (dim_time, dim_circular_flow_component, dim_data_source, dim_measurement)
-- rba_facts: 3 tables (fact_circular_flow, fact_financial_flows, fact_component_mapping)
-- rba_analytics: 0 tables (only views)

SELECT 'Expected vs Actual Table Counts:' as info;
SELECT 'rba_staging should have 8 tables' as expected_staging;
SELECT 'rba_dimensions should have 4 tables' as expected_dimensions;
SELECT 'rba_facts should have 3 tables' as expected_facts;
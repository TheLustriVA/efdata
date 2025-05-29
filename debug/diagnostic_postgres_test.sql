-- =====================================================
-- PostgreSQL Diagnostic Test Script
-- =====================================================

-- Test 1: Check PostgreSQL version and current user privileges
SELECT version() as postgres_version;
SELECT current_user as current_user, current_database() as current_db;

-- Test 2: Check schema creation privileges
SELECT has_database_privilege(current_user, current_database(), 'CREATE') as can_create_schema;

-- Test 3: Test CURRENT_DATE variations
SELECT 'Testing CURRENT_DATE functions:' as test_section;
SELECT CURRENT_DATE as current_date_upper;
SELECT current_date as current_date_lower;
SELECT now()::date as now_date_alternative;

-- Test 4: Try simple schema creation
DO $$
BEGIN
    -- Drop test schema if exists
    DROP SCHEMA IF EXISTS test_schema CASCADE;
    RAISE NOTICE 'Test schema dropped successfully';
    
    -- Create test schema
    CREATE SCHEMA IF NOT EXISTS test_schema;
    RAISE NOTICE 'Test schema created successfully';
    
    -- Test simple table with CURRENT_DATE
    CREATE TABLE test_schema.test_table (
        id SERIAL PRIMARY KEY,
        test_date DATE DEFAULT CURRENT_DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    RAISE NOTICE 'Test table with CURRENT_DATE created successfully';
    
    -- Clean up
    DROP SCHEMA test_schema CASCADE;
    RAISE NOTICE 'Test schema cleanup completed';
    
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Error occurred: %', SQLERRM;
        RAISE NOTICE 'Error code: %', SQLSTATE;
END;
$$;

-- Test 5: Check for transaction state issues
SELECT 'Transaction test completed - if you see this, no transaction issues' as transaction_status;
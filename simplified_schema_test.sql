-- =====================================================
-- Simplified Schema Test - Isolate the Problem
-- =====================================================

-- First, ensure clean transaction state
ROLLBACK;

-- Test 1: Basic schema creation (line 25 equivalent)
CREATE SCHEMA IF NOT EXISTS test_rba_staging;

-- Test 2: Simple table with CURRENT_DATE (around position 244)
CREATE TABLE test_rba_staging.simple_test (
    id SERIAL PRIMARY KEY,
    test_date DATE DEFAULT CURRENT_DATE,
    description TEXT
);

-- Test 3: Alternative CURRENT_DATE syntax
CREATE TABLE test_rba_staging.alternative_test (
    id SERIAL PRIMARY KEY,
    test_date DATE DEFAULT current_date,
    test_timestamp TIMESTAMP DEFAULT now(),
    description TEXT
);

-- Clean up
DROP SCHEMA test_rba_staging CASCADE;

-- Success message
SELECT 'All tests passed successfully!' as result;
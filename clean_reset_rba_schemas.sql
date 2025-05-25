-- =====================================================
-- Clean Reset - RBA Schemas Only (leaves public untouched)
-- =====================================================

-- Drop RBA schemas completely (this will cascade to all tables, views, functions)
DROP SCHEMA IF EXISTS rba_analytics CASCADE;
DROP SCHEMA IF EXISTS rba_facts CASCADE;
DROP SCHEMA IF EXISTS rba_dimensions CASCADE;
DROP SCHEMA IF EXISTS rba_staging CASCADE;

SELECT 'All RBA schemas dropped successfully. Public schema untouched.' as status;
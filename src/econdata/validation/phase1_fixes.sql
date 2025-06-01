-- Phase 1 Data Quality Fixes
-- Date: June 1, 2025
-- Author: Claude & Kieran
-- Purpose: Fix issues identified during Phase 1 validation

-- ============================================
-- CRITICAL FIX: Remove COFOG code from taxation table
-- ============================================
ALTER TABLE abs_staging.government_finance_statistics 
DROP COLUMN IF EXISTS cofog_code;

-- Verify fix
SELECT column_name 
FROM information_schema.columns 
WHERE table_schema = 'abs_staging' 
  AND table_name = 'government_finance_statistics'
  AND column_name = 'cofog_code';

-- ============================================
-- WARNING FIX: Add missing government levels to dimension table
-- ============================================

-- First check what's already in the dimension table
SELECT * FROM abs_dimensions.government_level ORDER BY level_name;

-- Insert missing government levels
-- Using UPSERT pattern to avoid conflicts
INSERT INTO abs_dimensions.government_level (level_code, level_name, level_type, description)
VALUES 
    ('CW', 'Commonwealth', 'Federal', 'Commonwealth Government of Australia'),
    ('ST', 'State', 'Aggregate', 'All State Governments (Aggregate)'),
    ('LC', 'Local', 'Local', 'Local Government Areas'),
    ('NSW', 'NSW State', 'State', 'New South Wales State Government'),
    ('VIC', 'VIC State', 'State', 'Victoria State Government'),
    ('QLD', 'QLD State', 'State', 'Queensland State Government'),
    ('WA', 'WA State', 'State', 'Western Australia State Government'),
    ('SA', 'SA State', 'State', 'South Australia State Government'),
    ('TAS', 'TAS State', 'State', 'Tasmania State Government'),
    ('ACT', 'ACT Territory', 'Territory', 'Australian Capital Territory'),
    ('NT', 'NT Territory', 'Territory', 'Northern Territory Government')
ON CONFLICT (level_code) DO UPDATE
SET 
    level_name = EXCLUDED.level_name,
    level_type = EXCLUDED.level_type,
    description = EXCLUDED.description;

-- Verify all government levels are now mapped
WITH unmapped AS (
    SELECT DISTINCT ge.level_of_government, COUNT(*) as record_count
    FROM abs_staging.government_expenditure ge
    LEFT JOIN abs_dimensions.government_level gl 
        ON ge.level_of_government = gl.level_name
        OR ge.level_of_government = gl.level_code
    WHERE gl.id IS NULL
      AND ge.level_of_government != 'Total'  -- Exclude aggregated totals
    GROUP BY ge.level_of_government
)
SELECT 
    CASE 
        WHEN COUNT(*) = 0 THEN 'SUCCESS: All government levels mapped!'
        ELSE 'ERROR: ' || COUNT(*) || ' levels still unmapped'
    END as status,
    COALESCE(string_agg(level_of_government || ' (' || record_count || ' records)', ', '), 'None') as unmapped_levels
FROM unmapped;

-- ============================================
-- DATA INTEGRITY: Verify record counts
-- ============================================
SELECT 
    'government_expenditure' as table_name,
    COUNT(*) as record_count,
    COUNT(DISTINCT level_of_government) as unique_gov_levels,
    COUNT(DISTINCT expenditure_category) as unique_categories,
    MIN(reference_period) as min_date,
    MAX(reference_period) as max_date,
    SUM(amount) as total_amount
FROM abs_staging.government_expenditure

UNION ALL

SELECT 
    'government_finance_statistics' as table_name,
    COUNT(*) as record_count,
    COUNT(DISTINCT level_of_government) as unique_gov_levels,
    COUNT(DISTINCT tax_category) as unique_categories,
    MIN(reference_period) as min_date,
    MAX(reference_period) as max_date,
    SUM(amount) as total_amount
FROM abs_staging.government_finance_statistics;

-- ============================================
-- VALIDATION: Check for any remaining issues
-- ============================================

-- Check for any null amounts (should be 0)
SELECT 
    'Null amounts in expenditure' as check_type,
    COUNT(*) as issue_count
FROM abs_staging.government_expenditure
WHERE amount IS NULL

UNION ALL

SELECT 
    'Null amounts in taxation' as check_type,
    COUNT(*) as issue_count
FROM abs_staging.government_finance_statistics
WHERE amount IS NULL;

-- Final validation summary
SELECT 
    'Phase 1 Fixes Complete' as status,
    NOW() as completed_at,
    'Ready for Phase 2 ETL' as next_step;
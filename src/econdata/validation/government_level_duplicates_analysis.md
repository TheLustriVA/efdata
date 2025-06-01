# Government Level Duplicates Analysis
**Date**: June 1, 2025  
**Issue Type**: NOTERROR - Intentional Dual Coding Scheme  
**Analyst**: Claude & Kieran  

## Issue Description

The `abs_dimensions.government_level` table contains what appears to be duplicate entries for each state/territory:

### RBA Format (Historical - rows 2-12)
- COMMONWEALTH, STATE_TOTAL, STATE_NSW, STATE_VIC, etc.
- Used by existing RBA data mappings
- Follows RBA's internal coding conventions

### ABS Format (Added for ABS Integration - rows 13-23)  
- CW, ST, NSW, VIC, QLD, etc.
- Added during ABS spider implementation (Phase 2)
- Follows ABS Government Finance Statistics conventions

## Why This Is NOT An Error

### 1. **Different Data Source Requirements**
- **RBA Data**: Uses STATE_QLD format in their CSV downloads
- **ABS Data**: Uses QLD format in their XLSX government finance files
- Each format matches the source system's native coding

### 2. **Backward Compatibility**
- Existing RBA fact records (48,382 records) already reference STATE_* codes
- Changing existing codes would break historical data integrity
- New ABS codes added alongside without disrupting existing mappings

### 3. **ETL Flexibility**
- ETL processes can map to appropriate code based on data source
- ABS spider maps to QLD, NSW, etc.
- RBA spider maps to STATE_QLD, STATE_NSW, etc.
- Both resolve to correct government entities

### 4. **Data Lineage Preservation**
- Code format indicates data provenance (RBA vs ABS)
- Enables source-specific analysis and validation
- Maintains audit trail for government finance data

## Evidence This Is Intentional

```sql
-- Both formats map to same logical entities but from different sources
SELECT 
    rba_format.level_name as rba_name,
    abs_format.level_name as abs_name,
    rba_format.level_code as rba_code,
    abs_format.level_code as abs_code
FROM abs_dimensions.government_level rba_format
JOIN abs_dimensions.government_level abs_format
    ON REPLACE(rba_format.level_name, 'STATE_', '') = REPLACE(abs_format.level_name, ' State', '')
WHERE rba_format.level_code LIKE 'STATE_%'
  AND abs_format.level_code NOT LIKE 'STATE_%'
  AND abs_format.level_type = 'State';
```

## Future Maintenance Notes

### When This Might Look Like An Error
- **Database Normalization Review**: Appears to violate normal forms
- **Code Cleanup**: Looks like redundant/duplicate data
- **New Developer Onboarding**: Confusing without context

### Why It Should Be Preserved
- **Historical Data Integrity**: 48,382+ RBA records depend on STATE_* codes
- **Source System Alignment**: Each format matches its originating system
- **ETL Simplicity**: Direct mapping without code translation needed

### Recommended Actions
1. **Document in Schema**: Add comments to table explaining dual coding
2. **ETL Documentation**: Specify which codes each spider uses
3. **Data Dictionary**: Explain relationship between code formats
4. **Monitoring**: Alert if new duplicate patterns emerge

## Implementation Timeline
- **2025-05-25**: Original RBA codes created (STATE_* format)
- **2025-06-01**: ABS codes added during Phase 2 (short format)
- **Decision**: Maintain both to preserve data integrity

## Validation Queries

```sql
-- Verify no unexpected duplicates beyond the known dual coding
WITH potential_issues AS (
    SELECT level_name, level_type, COUNT(*) as count
    FROM abs_dimensions.government_level
    WHERE level_code NOT IN ('TOTAL', 'STATE_TOTAL', 'ST')  -- Known aggregates
    GROUP BY level_name, level_type
    HAVING COUNT(*) > 2  -- More than RBA + ABS pair
)
SELECT * FROM potential_issues;

-- Expected result: 0 rows (no triple+ duplicates)
```

## Conclusion

The dual coding scheme is an intentional design decision that:
- Preserves historical data integrity (48K+ records)
- Supports heterogeneous data sources (RBA + ABS)
- Enables source-specific analysis and lineage tracking
- Follows established ETL patterns for multi-source systems

**Status**: NOTERROR - Intentional architectural decision for multi-source data integration.
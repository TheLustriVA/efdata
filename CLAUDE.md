# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Guidelines

### Coding Practices

- **NOTERROR Documentation**: When a coding decision or some data may look weird but is not an error, document it as a NOTERROR and justify why it might seem to a future code maintainer like an error but is not. This should only be done in clear cases that might cause unnecessary investigations later and have been absolutely confirmed as not an error.

### Library-Ready Development

When developing new functionality, consider modularity for future library extraction:

**Good Candidates for Modularization:**
- Statistical validation models (regression, PLS validation)
- Economic identity calculations (circular flow equilibrium)
- Data quality frameworks (validation pipelines)
- Time series utilities (quarterly interpolation)

**When Building New Features:**
1. Keep business logic separate from database specifics
2. Use dependency injection for configuration
3. Create clear interfaces with type hints
4. Include docstrings with usage examples
5. Flag with comment: `# LIBRARY-READY: candidate for econlib`

**Not Worth Modularizing:**
- Spider-specific scraping logic (too site-specific)
- Database migrations (project-specific)
- One-off data fixes (too context-dependent)

## Recent Progress (2025-06-02/03 Sessions)

### Completed
- ✅ **Phase 1**: Data quality validation completed
  - Database integrity check: 1 CRITICAL issue fixed (COFOG contamination)
  - Staging data validation: 27,624 records validated
  - Government level mappings: All 11 levels mapped
- ✅ **Phase 2**: Taxation ETL implemented
  - 400 aggregated records loaded to facts table
  - Total tax revenue: $43.3M captured
  - Circular flow completion: 97% (up from 94%)
- ✅ **Phase 3**: Government expenditure ETL completed
  - 25,380 records processed → 520 aggregated records
  - G component: 2,246 records ($404.6B total)
  - All government levels included with COFOG classification
- ✅ **Phase 4**: F-series interest rates implemented
  - 59,701 records loaded from F1, F4, F5, F6, F7 tables
  - 12,629 interest rate observations in facts table
  - Interest rates linked to S and I components
  - Created deposit/lending rate aggregates for circular flow

### Key Discoveries
- **NOTERROR Pattern**: Documented dual government coding (RBA vs ABS formats)
- **Methodological Variance**: Identified 25% systematic difference between RBA/ABS expenditure
- **Validation Innovation**: Proposed PLS regression for empirical validation bounds
- **Interest Rate Transmission**: Successfully linked monetary policy to S-I flows
- **Data Completeness**: 100% circular flow coverage (all 8 components)

### Current Status
- **Model Completeness**: 100% - all components have data
- **Total Records**: 50,619 across all components
- **Average Imbalance**: 14.0% (S+T+M vs I+G+X)
- **Interest Rates**: Linked to circular flow via S and I
- **Main Gap**: Taxation data limited to 2015-2025

### In Progress
- 📝 **Academic Paper**: "Empirical Validation of Circular Flow Models Using PLS"
  - First draft completed: `/docs/validation_methodology_working_paper_v1.md`
  - Novel contribution: PLS-based multi-source validation framework

### Next Steps
- **Phase 5**: Circular flow equilibrium validation
- **Enhancement**: Expand taxation data coverage (pre-2015)
- **Paper Review**: Iterate on working paper draft
- **Future**: Blender visualization integration

[Rest of the existing file content remains unchanged]
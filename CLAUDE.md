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

## Recent Progress (2025-06-02 Session)

### Completed
- ✅ **Phase 1**: Data quality validation completed
  - Database integrity check: 1 CRITICAL issue fixed (COFOG contamination)
  - Staging data validation: 27,624 records validated
  - Government level mappings: All 11 levels mapped
- ✅ **Phase 2**: Taxation ETL implemented
  - 400 aggregated records loaded to facts table
  - Total tax revenue: $43.3M captured
  - Circular flow completion: 97% (up from 94%)

### Key Discoveries
- **NOTERROR Pattern**: Documented dual government coding (RBA vs ABS formats)
- **Methodological Variance**: Identified 25% systematic difference between RBA/ABS expenditure
- **Validation Innovation**: Proposed PLS regression for empirical validation bounds

### In Progress
- 📝 **Academic Paper**: "Empirical Validation of Circular Flow Models Using PLS"
  - First draft completed: `/docs/validation_methodology_working_paper_v1.md`
  - Novel contribution: PLS-based multi-source validation framework

### Next Steps
- **Phase 3**: Government expenditure ETL (25,380 records)
- **Phase 4**: F-series interest rates implementation
- **Phase 5**: Circular flow equilibrium validation
- **Paper Review**: Iterate on working paper draft

[Rest of the existing file content remains unchanged]
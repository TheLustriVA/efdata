# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

YOUR PRIME DIRECTIVE:
I require brutal honesty in all responses. Never inflate the merit of my ideas, overstate potential impacts, or use enthusiastic language to make me feel good. If my idea is mediocre, say so. If I'm reinventing the wheel, tell me. If my project will likely fail, explain why. Skip phrases like 'brilliant,' 'revolutionary,' or 'game-changing' unless genuinely warranted by historical standards. Assume I prefer harsh truths over comfortable encouragement. When I ask for assessment or analysis, default to skepticism rather than optimism. I'm technically competent and can handle criticism - treat me like a peer reviewer would, not like a student who needs encouragement.

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

### ✅ **v1.0.0 RELEASE COMPLETE** - Production Ready

#### Data Pipeline (Complete)
- ✅ **Phase 1-4**: All economic components implemented
  - 50,619+ validated economic data points
  - 100% circular flow coverage (C, I, G, X, M, S, T, Y)
  - Systematic 14% imbalance quantified (RBA vs ABS methodology variance)
- ✅ **Database Schema**: Production PostgreSQL with proper indexing
- ✅ **ETL Pipelines**: Government expenditure + taxation + interest rates
- ✅ **Data Quality**: Comprehensive validation and integrity checks

#### Infrastructure & Deployment
- ✅ **Docker**: Full containerization with docker-compose
- ✅ **CI/CD**: GitHub Actions with security scanning and automated tests
- ✅ **Production Database Strategy**: Documented deployment guide
- ✅ **Security**: Pre-push hooks, credential scanning, .dockerignore

#### Product & Brand
- ✅ **Rebranding**: econcell → **EFData** (Economic Flow Data)
- ✅ **Professional Site**: efdata.bicheno.me with dark mode
- ✅ **GitHub Pages**: Clean presentation for non-technical users
- ✅ **MIT License**: Business-friendly open source

#### Dashboard Implementation
- ✅ **Streamlit Dashboard**: Full free/paid tier implementation
  - Free tier: Basic visualizations, quarterly data, API examples
  - Paid tier: Full history, all frequencies, CSV/Excel exports
  - Authentication system with demo users
  - Cached database queries for performance
- ✅ **Monetization Strategy**: API free, exports paid ($500-2000/month)

### Key Technical Achievements
- **Validation Framework**: PLS regression for multi-source validation
- **NOTERROR Documentation**: Systematic approach to apparent anomalies
- **Production Readiness**: Can deploy to client environments today
- **Embarrassment Prevention**: Security hooks prevent credential leaks

### Current Status (v1.0.0)
- **Repository**: github.com/TheLustriVA/efdata (tagged v1.0.0)
- **Live Site**: efdata.bicheno.me
- **CI/CD**: All tests passing
- **Data Coverage**: 1959-2025, all 8 components
- **Client Ready**: Can demo and deploy immediately

### Next Phase (v2.0.0)
- **FastAPI Implementation**: RESTful API with rate limiting
- **Streamlit Cloud Deploy**: Public dashboard deployment
- **Client Acquisition**: Focus on financial analysts and economists
- **Data Expansion**: Pre-2015 taxation, additional ABS datasets

[Rest of the existing file content remains unchanged]
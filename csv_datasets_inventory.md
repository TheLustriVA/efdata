# RBA CSV Datasets Inventory for Macro-Economic Circular Flow Modeling

**Analysis Date:** 2025-05-25  
**Total Datasets:** 193 CSV files  
**Data Source:** Reserve Bank of Australia Statistical Tables

## Executive Summary

This inventory documents 193 CSV datasets downloaded from the RBA, covering all major components of Australia's macro-economic system. The datasets are structured consistently with metadata headers, making them suitable for PostgreSQL DDL generation and circular flow analysis.

## Dataset Structure Pattern

All RBA CSV files follow a standardized 6-row header structure:
- **Row 1:** Table identifier and descriptive title
- **Row 2:** Column titles/variable names
- **Row 3:** Detailed descriptions of each data series
- **Row 4:** Data frequency (Daily, Weekly, Monthly, Quarterly)
- **Row 5:** Data type (Original, Seasonally adjusted, Chain volume, etc.)
- **Row 6:** Units of measurement ($ million, Per cent, Index, Number, etc.)

## Circular Flow Model Categories

### 1. Central Banking & Monetary Policy (A Series)
**Key for:** Government sector, financial intermediation

| Dataset | Description | Frequency | Key Variables |
|---------|-------------|-----------|---------------|
| `a1-data.csv` | RBA Balance Sheet | Weekly | Notes on issue, Exchange settlement balances, Government deposits, Gold & FX reserves |
| `a2-data.csv` | Monetary Policy Changes | As announced | Policy rate changes, timing |
| `a4-data.csv` | FX Transactions & Official Reserves | Monthly/Weekly | Foreign exchange holdings, interventions |
| `a5-data.csv` | Daily FX Market Interventions | Daily | Market intervention transactions |

**Data Types:** Monetary values ($ million), percentages, policy indicators  
**Time Series:** Mix of daily, weekly, monthly frequencies

### 2. Financial Institutions (B Series)
**Key for:** Financial intermediary flows, credit creation

| Dataset | Description | Frequency | Key Variables |
|---------|-------------|-----------|---------------|
| `b1-data.csv` | Assets of Financial Institutions | Quarterly | RBA assets, Bank assets, RFC assets, Managed funds |
| `b2-data.csv` | Liabilities of Financial Institutions | Quarterly | Deposit categories, funding sources |
| `b10-data.csv` | Banks Balance Sheet | Monthly | Bank-specific balance sheet items |
| `b11.1-assets.csv` | International Banking - Assets | Quarterly | Cross-border banking flows |
| `b11.1-liabilities.csv` | International Banking - Liabilities | Quarterly | International funding sources |

**Data Types:** Monetary aggregates ($ billion), institutional breakdowns  
**Time Series:** Primarily quarterly with some monthly data

### 3. Payment Systems (C Series)
**Key for:** Household consumption flows, payment velocity

| Dataset | Description | Frequency | Key Variables |
|---------|-------------|-----------|---------------|
| `c1-data.csv` | Credit & Charge Cards | Monthly | 61 variables covering transactions, values, balances by card type |
| `c2-data.csv` | Debit Cards | Monthly | Transaction volumes, values, domestic/overseas splits |
| `c3-data.csv` | ATM Transactions | Monthly | Cash withdrawal patterns |
| `c4-data.csv` | EFTPOS Transactions | Monthly | Electronic payment flows |

**Data Types:** Transaction counts ('000), values ($ million), seasonally adjusted  
**Time Series:** Monthly frequency, extensive variable coverage

### 4. Credit & Monetary Aggregates (D Series)
**Key for:** Credit creation, money supply analysis

| Dataset | Description | Frequency | Key Variables |
|---------|-------------|-----------|---------------|
| `d1-data.csv` | Growth in Financial Aggregates | Monthly | Housing credit, business credit, M3, broad money growth rates |
| `d2-data.csv` | Lending & Credit Aggregates | Monthly | Credit stock levels by category |
| `d3-data.csv` | Lending Rates | Monthly | Interest rates by loan type |
| `d5-data.csv` | Banks Balance Sheet Aggregates | Monthly | Bank credit and funding aggregates |

**Data Types:** Growth rates (Per cent), stock levels ($ billion)  
**Time Series:** Monthly, seasonally adjusted

### 5. Interest Rates & Yields (F Series)
**Key for:** Cost of capital, investment flows

| Dataset | Description | Frequency | Key Variables |
|---------|-------------|-----------|---------------|
| `f1-data.csv` | Money Market Rates | Daily | Cash rate, interbank rates, short-term securities, 18 variables |
| `f2-data.csv` | Capital Market Yields | Daily | Government bond yields by maturity |
| `f4-data.csv` | Lending Rates | Monthly | Bank lending rates by category |
| `f17-yields.csv` | Zero-coupon Yields | Daily | Yield curve construction |

**Data Types:** Interest rates (Per cent), yield indices  
**Time Series:** Mix of daily and monthly

### 6. Inflation Measures (G Series)
**Key for:** Price level analysis, real vs nominal flows

| Dataset | Description | Frequency | Key Variables |
|---------|-------------|-----------|---|
| `g3-data.csv` | Inflation Expectations | Quarterly | Consumer, business, union, economist expectations (1-2 years ahead) |

**Data Types:** Inflation expectations (Per cent)  
**Time Series:** Quarterly survey data

### 7. National Accounts (H Series)
**Key for:** GDP components, aggregate demand/supply

| Dataset | Description | Frequency | Key Variables |
|---------|-------------|-----------|---------------|
| `h1-data.csv` | GDP & Income | Quarterly | Real GDP, nominal GDP, GDI, per capita measures, terms of trade |
| `h2-data.csv` | Household Finances | Quarterly | Household income, consumption, saving, debt |
| `h3-data.csv` | Business Finances | Quarterly | Business investment, profits, debt |

**Data Types:** GDP aggregates ($ million), growth rates (Per cent), indices  
**Time Series:** Quarterly, seasonally adjusted

### 8. International Trade (I Series)
**Key for:** External sector flows, current account

| Dataset | Description | Frequency | Key Variables |
|---------|-------------|-----------|---------------|
| `i1-data.csv` | Trade & Balance of Payments | Quarterly | Exports/imports by category, trade balance, current account (20 variables) |
| `i3-data.csv` | Exchange Rates | Daily | Trade-weighted index, bilateral rates |

**Data Types:** Trade flows ($ million), exchange rate indices  
**Time Series:** Quarterly for trade, daily for exchange rates

### 9. Market Forecasts (J Series)
**Key for:** Expectations, forward-looking indicators

| Dataset | Description | Frequency | Key Variables |
|---------|-------------|-----------|---------------|
| `j1-cash-rate.csv` | Cash Rate Forecasts | Quarterly | Median, mean, range of economist forecasts |
| `j1-gdp-growth.csv` | GDP Growth Forecasts | Quarterly | Economic growth expectations |
| `j1-headline-inflation.csv` | Inflation Forecasts | Quarterly | CPI forecasts by economists |

**Data Types:** Forecast distributions (Per cent), survey responses  
**Time Series:** Quarterly survey rounds

## Technical Database Considerations

### Primary Keys
- Most tables use date-based primary keys
- Time series nature requires temporal indexing
- Some tables have multiple series requiring composite keys

### Data Types for PostgreSQL DDL
- **Monetary values:** DECIMAL(15,2) for $ million amounts
- **Percentages:** DECIMAL(8,4) for rates and growth figures  
- **Counts:** INTEGER for transaction numbers
- **Dates:** DATE for time series indexing
- **Indices:** DECIMAL(10,4) for economic indices

### Indexing Strategy
- Primary temporal index on date columns
- Secondary indices on major economic categories
- Consider partitioning for large daily datasets (F1, I3)

### Normalization Approach
- Dimension tables for metadata (frequencies, units, descriptions)
- Fact tables for time series values
- Bridge tables for multi-series relationships

## Circular Flow Mapping Potential

### Financial Flows
- **Household sector:** C series (payments), H2 (household finances), D series (credit)
- **Business sector:** H3 (business finances), D series (business credit), B series (banking)
- **Government sector:** A1 (RBA balance sheet), A4 (reserves), H1 (GDP components)
- **External sector:** I1 (trade flows), I3 (exchange rates), B11 (international banking)

### Stock-Flow Consistency
- Credit stocks (D2) vs credit flows (D1)
- Balance sheet positions (A1, B series) vs transaction flows (C series)
- GDP flows (H1) vs sectoral balance sheets (H2, H3)

## Data Quality Indicators

### Completeness
- All 193 files successfully mapped with metadata
- Consistent 6-row header structure across all datasets
- No missing structural elements identified

### Temporal Coverage
- Mix of frequencies from daily to quarterly
- Long time series apparent from file inspection
- Series breaks documented in metadata descriptions

### Data Validation
- Units clearly specified for all series
- Seasonal adjustment status documented
- Original vs derived series identified

## Recommendations for DDL Generation

1. **Staging approach:** Create raw import tables matching CSV structure, then transform to normalized schema
2. **Metadata preservation:** Store all header information for data lineage
3. **Time series optimization:** Use appropriate temporal data types and indexing
4. **Circular flow views:** Create analytical views mapping to circular flow components
5. **Data validation:** Implement checks for stock-flow consistency across related tables

---

**Note:** This inventory provides the structural foundation for PostgreSQL DDL generation and circular flow analysis. The consistent RBA data format enables automated schema creation and systematic economic modeling.
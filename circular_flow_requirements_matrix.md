# Circular Flow Model Requirements Matrix

## Summary of Requirements

The RBA circular flow model requires data for 8 key components that must satisfy the equilibrium equation:
**S + T + M = I + G + X**

## Component Requirements Matrix

| Component | Symbol | Description | Required Variables | Primary Source | Secondary Source | Frequency | Granularity |
|-----------|--------|-------------|-------------------|----------------|------------------|-----------|-------------|
| **National Income** | Y | GDP/Income | - Gross Domestic Product<br>- Gross National Income<br>- Gross Household Disposable Income<br>- Compensation of Employees | ABS National Accounts<br>(Cat. 5206.0) | RBA H1 table | Quarterly | - Total<br>- By income type<br>- By sector |
| **Consumption** | C | Household Spending | - Household Final Consumption Expenditure (HFCE)<br>- By purpose (COICOP categories) | ABS National Accounts<br>(Cat. 5206.0)<br>GDPE_H API | RBA H2 table | Quarterly | - Total<br>- By category<br>- Seasonally adjusted |
| **Savings** | S | Household Savings | - Household Net Saving<br>- Gross Saving<br>- Saving Ratio<br>- Derived: S = Y - C | ABS National Accounts<br>(Cat. 5204.0, 5206.0) | Calculated from Y-C | Quarterly | - Total households<br>- Net vs gross |
| **Investment** | I | Capital Formation | - Gross Fixed Capital Formation (GFCF)<br>- Private GFCF by asset type:<br>  • Dwellings<br>  • Non-dwelling construction<br>  • Machinery & equipment<br>  • Intellectual property | ABS National Accounts<br>(Cat. 5206.0, 5625.0)<br>GDPE_H API | RBA H3 table | Quarterly | - By asset type<br>- By industry<br>- Private vs public |
| **Government Spending** | G | Public Expenditure | - Government Final Consumption Expenditure (GFCE)<br>- Government GFCF<br>- By level of government<br>- By purpose (COFOG) | ABS GFS (Cat. 5512.0)<br>GDPE_H API | RBA H1 (limited) | Annual/Quarterly | - By level<br>- By function<br>- Current vs capital |
| **Taxation** | T | Government Revenue | - Taxes on income<br>- Taxes on production & imports<br>- GST revenue<br>- By level of government | ABS GFS (Cat. 5512.0) | N/A | Annual | - By tax type<br>- By government level |
| **Exports** | X | Foreign Sales | - Exports of goods<br>- Exports of services<br>- By commodity/service type<br>- By destination | ABS International Trade<br>(Cat. 5368.0)<br>ITGS_H API | RBA I1 table | Monthly/Quarterly | - Goods vs services<br>- By partner country |
| **Imports** | M | Foreign Purchases | - Imports of goods<br>- Imports of services<br>- By commodity/service type<br>- By origin | ABS International Trade<br>(Cat. 5368.0)<br>ITGS_H API | RBA I1 table | Monthly/Quarterly | - Goods vs services<br>- By partner country |

## Supporting Data Requirements

| Category | Data Elements | Source | Purpose |
|----------|---------------|--------|---------|
| **Financial Sector** | - Interest rates (deposit/lending)<br>- Credit aggregates<br>- Monetary aggregates | RBA Tables:<br>- D1-D4 (aggregates)<br>- F1-F7 (rates) | Influences S→I flow |
| **Exchange Rates** | - AUD/USD daily<br>- Trade-weighted index<br>- Real exchange rates | RBA Tables:<br>- F11, F11.1<br>- F15 | Impacts X, M valuation |
| **Labor Market** | - Employment<br>- Hours worked<br>- Wage price index | ABS Labour Force | Context for Y, C |

## Data Quality Requirements

1. **Temporal Consistency**
   - All components must be available quarterly
   - Historical data back to at least 2010
   - Consistent seasonal adjustment methodology

2. **Measurement Consistency**
   - Current prices AND chain volume measures
   - Consistent base year for real values
   - Units in AUD millions

3. **Conceptual Alignment**
   - National accounts basis (SNA 2008)
   - Consistent sector definitions
   - Proper treatment of imputations

## Validation Requirements

1. **Internal Consistency**
   - GDP(E) = C + I + G + X - M
   - GDP(I) = Compensation + GOS + GMI + Taxes - Subsidies
   - S = Y - C (household level)

2. **Equilibrium Check**
   - S + T + M = I + G + X
   - Acceptable variance: ±2% due to statistical discrepancy

3. **Cross-Source Validation**
   - RBA vs ABS figures for overlapping series
   - Quarterly vs annual reconciliation

## Implementation Priority

### Priority 1 (Essential)
- Y, C, I, G, X, M core aggregates
- T (taxation revenue totals)
- Basic S calculation

### Priority 2 (Enhanced)
- Detailed breakdowns by category
- State-level components
- Financial sector flows

### Priority 3 (Advanced)
- Industry-level detail
- Real-time updates
- Forecasting capabilities

## Notes on Current Gaps
- G (Government Spending): Need detailed COFOG breakdown from ABS GFS
- Financial flows: Need explicit S→I tracking through financial sector
- Quarterly taxation: Currently annual, needs interpolation
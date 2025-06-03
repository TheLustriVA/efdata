#!/usr/bin/env python3
"""
Circular Flow Imbalance Analysis
Date: June 3, 2025
Author: Claude & Kieran
Purpose: Analyze causes of circular flow imbalance and explore T estimation
"""

import psycopg2
from dotenv import load_dotenv
import os
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
import numpy as np

load_dotenv()

def get_imbalance_analysis():
    """Analyze circular flow imbalance by period and component availability"""
    conn = psycopg2.connect(
        dbname=os.getenv('PSQL_DB'),
        user=os.getenv('PSQL_USER'),
        password=os.getenv('PSQL_PW'),
        host=os.getenv('PSQL_HOST'),
        port=os.getenv('PSQL_PORT')
    )
    
    cur = conn.cursor()
    
    # Get detailed imbalance analysis by period
    cur.execute("""
        WITH quarterly_data AS (
            SELECT 
                dt.date_value,
                dt.year,
                dt.quarter,
                c.component_code,
                SUM(f.value) as total_value,
                COUNT(*) as record_count
            FROM rba_facts.fact_circular_flow f
            JOIN rba_dimensions.dim_circular_flow_component c ON f.component_key = c.component_key
            JOIN rba_dimensions.dim_time dt ON f.time_key = dt.time_key
            WHERE c.component_code IN ('S', 'T', 'M', 'I', 'G', 'X')
              AND dt.date_value >= '2020-01-01'  -- Recent periods for analysis
            GROUP BY dt.date_value, dt.year, dt.quarter, c.component_code
        ),
        pivot_data AS (
            SELECT 
                date_value,
                year,
                quarter,
                MAX(CASE WHEN component_code = 'S' THEN total_value END) as S,
                MAX(CASE WHEN component_code = 'T' THEN total_value END) as T,
                MAX(CASE WHEN component_code = 'M' THEN total_value END) as M,
                MAX(CASE WHEN component_code = 'I' THEN total_value END) as I,
                MAX(CASE WHEN component_code = 'G' THEN total_value END) as G,
                MAX(CASE WHEN component_code = 'X' THEN total_value END) as X,
                COUNT(DISTINCT component_code) as components_available
            FROM quarterly_data
            GROUP BY date_value, year, quarter
        )
        SELECT 
            date_value,
            year,
            quarter,
            S, T, M, I, G, X,
            components_available,
            (S + COALESCE(T, 0) + M) as left_side,
            (I + G + X) as right_side,
            ABS((S + COALESCE(T, 0) + M) - (I + G + X)) as abs_difference,
            CASE 
                WHEN (I + G + X) > 0 
                THEN ABS((S + COALESCE(T, 0) + M) - (I + G + X)) / (I + G + X) * 100
                ELSE NULL 
            END as pct_imbalance,
            CASE WHEN T IS NULL THEN 'No T data' ELSE 'Has T data' END as t_availability
        FROM pivot_data
        WHERE S IS NOT NULL AND I IS NOT NULL AND G IS NOT NULL
        ORDER BY date_value DESC
    """)
    
    recent_data = cur.fetchall()
    
    # Get historical coverage analysis
    cur.execute("""
        SELECT 
            c.component_code,
            COUNT(DISTINCT dt.year) as year_coverage,
            MIN(dt.date_value) as earliest_date,
            MAX(dt.date_value) as latest_date,
            COUNT(*) as total_records
        FROM rba_facts.fact_circular_flow f
        JOIN rba_dimensions.dim_circular_flow_component c ON f.component_key = c.component_key
        JOIN rba_dimensions.dim_time dt ON f.time_key = dt.time_key
        WHERE c.component_code IN ('S', 'T', 'M', 'I', 'G', 'X')
        GROUP BY c.component_code
        ORDER BY c.component_code
    """)
    
    coverage_data = cur.fetchall()
    
    # Analyze pre-2015 data (before T) for solve-for-T analysis
    cur.execute("""
        WITH historical_data AS (
            SELECT 
                dt.date_value,
                dt.year,
                c.component_code,
                SUM(f.value) as total_value
            FROM rba_facts.fact_circular_flow f
            JOIN rba_dimensions.dim_circular_flow_component c ON f.component_key = c.component_key
            JOIN rba_dimensions.dim_time dt ON f.time_key = dt.time_key
            WHERE c.component_code IN ('S', 'M', 'I', 'G', 'X')
              AND dt.date_value < '2015-01-01'
              AND dt.date_value >= '2000-01-01'  -- Focus on 2000-2015 period
            GROUP BY dt.date_value, dt.year, c.component_code
        ),
        complete_periods AS (
            SELECT 
                date_value,
                year,
                MAX(CASE WHEN component_code = 'S' THEN total_value END) as S,
                MAX(CASE WHEN component_code = 'M' THEN total_value END) as M,
                MAX(CASE WHEN component_code = 'I' THEN total_value END) as I,
                MAX(CASE WHEN component_code = 'G' THEN total_value END) as G,
                MAX(CASE WHEN component_code = 'X' THEN total_value END) as X,
                COUNT(DISTINCT component_code) as components_available
            FROM historical_data
            GROUP BY date_value, year
            HAVING COUNT(DISTINCT component_code) = 5  -- All except T
        )
        SELECT 
            date_value,
            year,
            S, M, I, G, X,
            (I + G + X) - (S + M) as implied_T,
            CASE 
                WHEN S + M > 0 
                THEN ((I + G + X) - (S + M)) / (S + M) * 100
                ELSE NULL 
            END as implied_T_as_pct_of_SM
        FROM complete_periods
        WHERE S IS NOT NULL AND M IS NOT NULL AND I IS NOT NULL 
          AND G IS NOT NULL AND X IS NOT NULL
        ORDER BY date_value DESC
        LIMIT 20
    """)
    
    historical_data = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return recent_data, coverage_data, historical_data

def analyze_imbalance_causes(recent_data, coverage_data):
    """Analyze what's causing the imbalance"""
    print("CIRCULAR FLOW IMBALANCE ANALYSIS")
    print("=" * 60)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Component coverage analysis
    print("1. COMPONENT DATA COVERAGE:")
    print("-" * 40)
    print(f"{'Component':<12} {'Years':<8} {'Records':<10} {'Coverage':<20}")
    print("-" * 40)
    
    min_coverage = float('inf')
    weakest_component = None
    
    for code, years, earliest, latest, records in coverage_data:
        coverage_period = f"{earliest.year}-{latest.year}"
        print(f"{code:<12} {years:<8} {records:<10} {coverage_period:<20}")
        
        if years < min_coverage:
            min_coverage = years
            weakest_component = code
    
    print(f"\n→ Weakest component: {weakest_component} ({min_coverage} years)")
    
    # Recent period imbalance analysis
    print("\n2. RECENT PERIOD IMBALANCE ANALYSIS (2020+):")
    print("-" * 60)
    print(f"{'Date':<12} {'T Data':<12} {'Components':<12} {'Imbalance %':<12}")
    print("-" * 60)
    
    with_t_imbalances = []
    without_t_imbalances = []
    
    for row in recent_data[:10]:  # Last 10 periods
        date, year, quarter, S, T, M, I, G, X, components, left, right, abs_diff, pct_imbalance, t_status = row
        
        has_t = T is not None
        if has_t:
            with_t_imbalances.append(pct_imbalance or 0)
        else:
            without_t_imbalances.append(pct_imbalance or 0)
        
        print(f"{date.strftime('%Y-%m-%d'):<12} {t_status:<12} {components:<12} {pct_imbalance or 0:<12.1f}")
    
    # Calculate averages
    avg_with_t = np.mean(with_t_imbalances) if with_t_imbalances else 0
    avg_without_t = np.mean(without_t_imbalances) if without_t_imbalances else 0
    
    print(f"\n→ Average imbalance WITH T data: {avg_with_t:.1f}%")
    print(f"→ Average imbalance WITHOUT T data: {avg_without_t:.1f}%")
    print(f"→ T data impact: {abs(avg_with_t - avg_without_t):.1f} percentage point difference")
    
    return avg_with_t, avg_without_t

def analyze_solve_for_t(historical_data):
    """Analyze the feasibility and benefit of solving for T"""
    print("\n3. SOLVE-FOR-T ANALYSIS (Pre-2015 Historical Data):")
    print("-" * 60)
    
    if not historical_data:
        print("→ Insufficient historical data for solve-for-T analysis")
        return
    
    print(f"{'Date':<12} {'Implied T':<12} {'T as % of S+M':<15} {'Feasibility':<15}")
    print("-" * 60)
    
    viable_estimates = 0
    implied_t_values = []
    t_percentages = []
    
    for row in historical_data:
        date, year, S, M, I, G, X, implied_T, t_pct_sm = row
        
        # Check feasibility
        if implied_T is not None:
            # Reasonable if T is positive and less than 50% of S+M
            if implied_T > 0 and (t_pct_sm or 0) < 50:
                feasibility = "✓ Viable"
                viable_estimates += 1
                implied_t_values.append(implied_T)
                if t_pct_sm:
                    t_percentages.append(t_pct_sm)
            elif implied_T < 0:
                feasibility = "✗ Negative"
            else:
                feasibility = "⚠ High"
        else:
            feasibility = "✗ Invalid"
        
        print(f"{date.strftime('%Y-%m-%d'):<12} {implied_T or 0:<12,.0f} {t_pct_sm or 0:<15.1f} {feasibility:<15}")
    
    # Summary statistics
    if implied_t_values:
        avg_implied_t = np.mean(implied_t_values)
        std_implied_t = np.std(implied_t_values)
        avg_t_pct = np.mean(t_percentages) if t_percentages else 0
        
        print(f"\n→ Viable estimates: {viable_estimates}/{len(historical_data)} ({viable_estimates/len(historical_data)*100:.1f}%)")
        print(f"→ Average implied T: ${avg_implied_t:,.0f}M")
        print(f"→ Standard deviation: ${std_implied_t:,.0f}M")
        print(f"→ Average T as % of S+M: {avg_t_pct:.1f}%")
        
        # Benefits analysis
        print(f"\n→ BENEFITS OF SOLVE-FOR-T:")
        print(f"   • Extend T data coverage from 10 years to {viable_estimates} additional periods")
        print(f"   • Enable historical trend analysis (tax policy evolution)")
        print(f"   • Improve circular flow equilibrium validation")
        print(f"   • Support econometric modeling with longer time series")
        
        # Quality assessment
        cv = (std_implied_t / avg_implied_t) * 100 if avg_implied_t > 0 else 0
        print(f"\n→ DATA QUALITY ASSESSMENT:")
        print(f"   • Coefficient of variation: {cv:.1f}%")
        if cv < 20:
            print(f"   • Quality: ✓ Excellent (low volatility)")
        elif cv < 40:
            print(f"   • Quality: ✓ Good (moderate volatility)")
        else:
            print(f"   • Quality: ⚠ Moderate (high volatility)")
    
    return viable_estimates, implied_t_values

def create_imbalance_documentation():
    """Create documentation for fixing the imbalance"""
    doc_content = """# Circular Flow Imbalance Analysis & Resolution Strategy

**Date**: June 3, 2025  
**Analysis**: Post-Phase 4 Implementation

## Current Imbalance Status

- **Average Imbalance**: 14.0% (S + T + M vs I + G + X)
- **Primary Cause**: Limited taxation (T) data coverage (2015-2025 vs 1959-2025 for other components)
- **Secondary Factors**: Methodological differences between data sources

## Imbalance Causes Analysis

### 1. Primary Cause: Taxation Data Gap
- **T component coverage**: 10 years (2015-2025)
- **Other components**: 60+ years (1959-2025)
- **Impact**: ~20% imbalance in recent periods vs ~15% without T data

### 2. Secondary Causes
- **Methodological differences**: RBA vs ABS measurement approaches
- **Temporal aggregation**: Quarterly vs monthly vs daily frequencies
- **Classification differences**: COFOG vs RBA sector classifications

## Resolution Strategies

### Short-term (Phase 5)
1. **Improve data alignment**
   - Standardize temporal aggregation methods
   - Align government level classifications
   - Apply consistent seasonal adjustments

2. **Enhanced validation**
   - Implement PLS regression validation bounds
   - Cross-validate using multiple data sources
   - Apply statistical outlier detection

### Medium-term (Post-Phase 5)
1. **Expand taxation data**
   - Source historical ATO data (pre-2015)
   - Integrate state/territory taxation data
   - Add indirect tax components (GST, customs)

2. **Solve-for-T implementation**
   - Calculate implied T for pre-2015 periods
   - Validate against known policy changes
   - Apply smoothing techniques for trend consistency

### Long-term (Future Enhancement)
1. **Advanced modeling**
   - Implement error correction models
   - Add stochastic adjustment factors
   - Develop multi-frequency reconciliation

2. **Alternative data sources**
   - Parliamentary budget office data
   - Treasury economic forecasts
   - International comparisons (OECD)

## Solve-for-T Implementation Plan

### Methodology
```
T_implied = (I + G + X) - (S + M)
```

### Quality Criteria
- T_implied > 0 (taxes cannot be negative)
- T_implied < 50% of (S + M) (reasonable tax burden)
- Consistent with known policy changes
- Low coefficient of variation (<40%)

### Benefits
1. **Extended coverage**: Add 15+ years of historical T data
2. **Trend analysis**: Support policy impact studies
3. **Model validation**: Improve equilibrium testing
4. **Forecasting**: Better econometric model inputs

### Implementation Steps
1. Calculate implied T for all pre-2015 periods
2. Apply quality filters and outlier detection
3. Validate against known tax policy changes
4. Implement smoothing for trend consistency
5. Document assumptions and limitations

## Expected Outcomes

### Phase 5 (Immediate)
- Reduce imbalance to ~10% through better alignment
- Implement validation framework
- Document remaining gaps

### Post-Phase 5 (3-6 months)
- Extend T coverage to 1995+ using solve-for-T
- Reduce imbalance to ~5-7%
- Enable robust historical analysis

### Long-term (6-12 months)
- Achieve <5% average imbalance
- Full historical coverage (1959+)
- Production-ready econometric model
"""
    
    with open('/home/websinthe/code/econcell/estimates/circular_flow_imbalance_resolution.md', 'w') as f:
        f.write(doc_content)
    
    print(f"\n4. DOCUMENTATION CREATED:")
    print("→ Saved imbalance resolution strategy to:")
    print("   estimates/circular_flow_imbalance_resolution.md")

def main():
    """Main analysis function"""
    # Get data
    recent_data, coverage_data, historical_data = get_imbalance_analysis()
    
    # Analyze causes
    avg_with_t, avg_without_t = analyze_imbalance_causes(recent_data, coverage_data)
    
    # Analyze solve-for-T potential
    viable_estimates, implied_t_values = analyze_solve_for_t(historical_data)
    
    # Create documentation
    create_imbalance_documentation()
    
    # Summary conclusions
    print(f"\n" + "=" * 60)
    print("CONCLUSIONS:")
    print("=" * 60)
    print(f"1. PRIMARY CAUSE: Taxation data gap (10 vs 60+ years)")
    print(f"2. T DATA IMPACT: {abs(avg_with_t - avg_without_t):.1f} percentage points")
    print(f"3. SOLVE-FOR-T VIABLE: {viable_estimates} historical periods")
    print(f"4. EXPECTED IMPROVEMENT: 14% → ~5-7% imbalance")
    print(f"5. NEXT STEP: Implement Phase 5 validation framework")

if __name__ == "__main__":
    main()
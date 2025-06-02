#!/usr/bin/env python3
"""
Circular Flow Visualization
Date: June 3, 2025
Author: Claude & Kieran
Purpose: Quick visualization of circular flow model status
"""

import psycopg2
from dotenv import load_dotenv
import os
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Circle
import numpy as np

load_dotenv()

def get_flow_data():
    """Get circular flow component data from database"""
    conn = psycopg2.connect(
        dbname=os.getenv('PSQL_DB'),
        user=os.getenv('PSQL_USER'),
        password=os.getenv('PSQL_PW'),
        host=os.getenv('PSQL_HOST'),
        port=os.getenv('PSQL_PORT')
    )
    
    cur = conn.cursor()
    
    # Get component summary
    cur.execute("""
        SELECT 
            c.component_code,
            c.component_name,
            COUNT(DISTINCT f.time_key) as periods,
            COUNT(f.value) as records,
            MIN(dt.date_value) as earliest,
            MAX(dt.date_value) as latest,
            AVG(f.value) as avg_value
        FROM rba_dimensions.dim_circular_flow_component c
        LEFT JOIN rba_facts.fact_circular_flow f ON c.component_key = f.component_key
        LEFT JOIN rba_dimensions.dim_time dt ON f.time_key = dt.time_key
        WHERE c.component_code IN ('C', 'I', 'G', 'X', 'M', 'S', 'T', 'Y')
        GROUP BY c.component_code, c.component_name
        ORDER BY c.component_code
    """)
    
    components = {}
    for row in cur.fetchall():
        code, name, periods, records, earliest, latest, avg_value = row
        components[code] = {
            'name': name,
            'periods': periods or 0,
            'records': records or 0,
            'earliest': earliest,
            'latest': latest,
            'avg_value': avg_value or 0
        }
    
    # Get recent equilibrium check
    cur.execute("""
        WITH quarterly_components AS (
            SELECT 
                dt.date_value,
                MAX(CASE WHEN c.component_code = 'S' THEN f.value END) as S,
                MAX(CASE WHEN c.component_code = 'T' THEN f.value END) as T,
                MAX(CASE WHEN c.component_code = 'M' THEN f.value END) as M,
                MAX(CASE WHEN c.component_code = 'I' THEN f.value END) as I,
                MAX(CASE WHEN c.component_code = 'G' THEN f.value END) as G,
                MAX(CASE WHEN c.component_code = 'X' THEN f.value END) as X
            FROM rba_facts.fact_circular_flow f
            JOIN rba_dimensions.dim_circular_flow_component c ON f.component_key = c.component_key
            JOIN rba_dimensions.dim_time dt ON f.time_key = dt.time_key
            WHERE dt.date_value >= '2023-01-01'
              AND c.component_code IN ('S', 'T', 'M', 'I', 'G', 'X')
            GROUP BY dt.date_value
            HAVING COUNT(DISTINCT c.component_code) = 6
        )
        SELECT 
            AVG(ABS((S + T + M) - (I + G + X)) / NULLIF((I + G + X), 0) * 100) as avg_imbalance
        FROM quarterly_components
    """)
    
    avg_imbalance = cur.fetchone()[0] or 0
    
    # Get interest rate linkage status
    cur.execute("""
        SELECT COUNT(DISTINCT series_id)
        FROM rba_facts.fact_circular_flow
        WHERE series_id IN ('S_DEPOSIT_RATE', 'I_LENDING_RATE')
    """)
    
    rate_series_count = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    return components, avg_imbalance, rate_series_count

def create_circular_flow_diagram(components, avg_imbalance, rate_series_count):
    """Create visual representation of circular flow"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Left plot: Circular flow diagram
    ax1.set_xlim(-3, 3)
    ax1.set_ylim(-3, 3)
    ax1.set_aspect('equal')
    ax1.axis('off')
    ax1.set_title('Circular Flow Model Structure', fontsize=16, fontweight='bold', pad=20)
    
    # Define positions for components
    positions = {
        'Y': (0, 2.2),      # Income at top
        'C': (-2, 0.5),     # Consumption left
        'S': (-2, -0.5),    # Savings left  
        'T': (-2, -1.5),    # Taxation left
        'I': (2, 0.5),      # Investment right
        'G': (2, -0.5),     # Government right
        'X': (2, -1.5),     # Exports right
        'M': (0, -2.2)      # Imports at bottom
    }
    
    # Color coding based on data coverage
    def get_color(code):
        if components[code]['records'] == 0:
            return '#ff6b6b'  # Red for no data
        elif components[code]['periods'] < 100:
            return '#ffd93d'  # Yellow for limited data
        else:
            return '#6bcf7f'  # Green for good coverage
    
    # Draw components
    for code, (x, y) in positions.items():
        if code in components:
            color = get_color(code)
            comp = components[code]
            
            # Draw box
            box = FancyBboxPatch(
                (x - 0.4, y - 0.2), 0.8, 0.4,
                boxstyle="round,pad=0.1",
                facecolor=color,
                edgecolor='black',
                linewidth=2
            )
            ax1.add_patch(box)
            
            # Add text
            ax1.text(x, y, f"{code}", fontsize=14, fontweight='bold', 
                    ha='center', va='center')
            ax1.text(x, y - 0.4, f"{comp['records']} rec", fontsize=8, 
                    ha='center', va='top')
    
    # Draw flows
    # Left side flows (household to economy)
    ax1.arrow(-1.5, 2.0, 1.0, -1.3, head_width=0.1, head_length=0.1, 
             fc='blue', ec='blue', linewidth=2, alpha=0.7)  # Y to C
    ax1.arrow(-1.5, 0.3, 1.0, -0.6, head_width=0.1, head_length=0.1,
             fc='blue', ec='blue', linewidth=2, alpha=0.7)  # C to S
    ax1.arrow(-1.5, -0.7, 1.0, -0.6, head_width=0.1, head_length=0.1,
             fc='blue', ec='blue', linewidth=2, alpha=0.7)  # S to T
    
    # Right side flows (economy to production)
    ax1.arrow(0.5, 0.7, 1.0, -0.0, head_width=0.1, head_length=0.1,
             fc='red', ec='red', linewidth=2, alpha=0.7)  # to I
    ax1.arrow(0.5, -0.3, 1.0, -0.0, head_width=0.1, head_length=0.1,
             fc='red', ec='red', linewidth=2, alpha=0.7)  # to G
    ax1.arrow(0.5, -1.3, 1.0, -0.0, head_width=0.1, head_length=0.1,
             fc='red', ec='red', linewidth=2, alpha=0.7)  # to X
    
    # Equilibrium equation
    ax1.text(0, 0, 'S + T + M = I + G + X', fontsize=12, 
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
            ha='center', va='center')
    
    # Imbalance indicator
    imbalance_color = 'green' if avg_imbalance < 5 else 'orange' if avg_imbalance < 15 else 'red'
    ax1.text(0, -0.5, f'Avg Imbalance: {avg_imbalance:.1f}%', fontsize=10,
            color=imbalance_color, ha='center', va='center', fontweight='bold')
    
    # Interest rate indicator
    if rate_series_count == 2:
        ax1.text(0, 1.5, '✓ Interest Rates Linked', fontsize=10,
                color='green', ha='center', va='center',
                bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
    
    # Right plot: Data coverage timeline
    ax2.set_title('Data Coverage Timeline', fontsize=16, fontweight='bold')
    ax2.set_xlabel('Year')
    ax2.set_ylabel('Component')
    
    # Plot timeline bars
    y_pos = 0
    colors = []
    for code in ['Y', 'C', 'I', 'G', 'S', 'T', 'X', 'M']:
        if code in components and components[code]['earliest']:
            comp = components[code]
            start_year = comp['earliest'].year
            end_year = comp['latest'].year
            
            color = get_color(code)
            colors.append(color)
            
            # Draw timeline bar
            ax2.barh(y_pos, end_year - start_year, left=start_year, 
                    height=0.8, color=color, edgecolor='black', linewidth=1)
            
            # Add component label
            ax2.text(start_year - 2, y_pos, f"{code}: {comp['name'][:20]}", 
                    fontsize=10, ha='right', va='center')
            
            # Add record count
            ax2.text(end_year + 1, y_pos, f"{comp['records']} records", 
                    fontsize=8, ha='left', va='center')
            
            y_pos += 1
    
    ax2.set_ylim(-0.5, y_pos - 0.5)
    ax2.set_xlim(1955, 2030)
    ax2.grid(True, axis='x', alpha=0.3)
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#6bcf7f', label='Good coverage (>100 periods)'),
        Patch(facecolor='#ffd93d', label='Limited coverage (<100 periods)'),
        Patch(facecolor='#ff6b6b', label='No data')
    ]
    ax2.legend(handles=legend_elements, loc='lower right')
    
    plt.tight_layout()
    return fig

def print_summary(components, avg_imbalance, rate_series_count):
    """Print text summary of circular flow status"""
    print("\nCIRCULAR FLOW MODEL STATUS SUMMARY")
    print("=" * 60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Overall progress
    components_with_data = sum(1 for c in components.values() if c['records'] > 0)
    total_records = sum(c['records'] for c in components.values())
    
    print("OVERALL PROGRESS:")
    print(f"  ✓ Components with data: {components_with_data}/8 ({components_with_data/8*100:.0f}%)")
    print(f"  ✓ Total records: {total_records:,}")
    print(f"  ✓ Average imbalance: {avg_imbalance:.1f}%")
    print(f"  ✓ Interest rates linked: {'Yes' if rate_series_count == 2 else 'No'}")
    print()
    
    # Component status
    print("COMPONENT STATUS:")
    print("-" * 60)
    print(f"{'Code':<5} {'Component':<25} {'Status':<12} {'Coverage':<20}")
    print("-" * 60)
    
    for code in ['Y', 'C', 'I', 'G', 'S', 'T', 'X', 'M']:
        if code in components:
            comp = components[code]
            if comp['records'] == 0:
                status = "❌ No data"
            elif comp['periods'] < 100:
                status = "⚠️  Limited"
            else:
                status = "✅ Good"
            
            if comp['earliest'] and comp['latest']:
                coverage = f"{comp['earliest'].year}-{comp['latest'].year}"
            else:
                coverage = "N/A"
            
            print(f"{code:<5} {comp['name'][:24]:<25} {status:<12} {coverage:<20}")
    
    print()
    print("RECENT ACHIEVEMENTS:")
    print("  ✓ Phase 3: Government expenditure ETL (25,380 → 520 records)")
    print("  ✓ Phase 4: F-series interest rates (59,701 → 12,629 records)")
    print("  ✓ Interest rates linked to S and I components")
    print()
    print("NEXT STEPS:")
    print("  → Phase 5: Validate circular flow equilibrium")
    print("  → Address ~20% imbalance (expand taxation data)")
    print("  → Review PLS validation paper")

def main():
    """Main function"""
    # Get data
    components, avg_imbalance, rate_series_count = get_flow_data()
    
    # Print summary
    print_summary(components, avg_imbalance, rate_series_count)
    
    # Create visualization
    fig = create_circular_flow_diagram(components, avg_imbalance, rate_series_count)
    
    # Save figure
    output_path = 'circular_flow_status.png'
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nVisualization saved to: {output_path}")
    
    # Also try to display if possible
    try:
        plt.show()
    except:
        pass

if __name__ == "__main__":
    main()
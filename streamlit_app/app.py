"""
EFData Dashboard - Australian Economic Data Visualization
Free tier dashboard with paid upgrade options
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from streamlit_app.auth import check_authentication, get_user_tier
from streamlit_app.database import get_component_data, get_circular_flow_summary, get_data_freshness
from streamlit_app.visualizations import (
    create_time_series_chart,
    create_circular_flow_sankey,
    create_component_comparison,
    create_data_quality_heatmap
)

# Page configuration
st.set_page_config(
    page_title="EFData - Australian Economic Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for branding
st.markdown("""
<style>
    .stApp {
        background-color: var(--background-color);
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .premium-feature {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    div[data-testid="metric-container"] {
        background-color: #f0f2f6;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 5px;
        margin: 5px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Authentication
    username, user_tier = check_authentication()
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/300x100/2c3e50/ffffff?text=EFData", width=300)
        st.markdown("### Australian Economic Data")
        st.markdown("---")
        
        # Component selector
        component = st.selectbox(
            "Select Component",
            ["📈 Overview", 
             "🛍️ Consumption (C)", 
             "🏗️ Investment (I)", 
             "🏛️ Government (G)", 
             "📦 Exports (X)", 
             "📥 Imports (M)", 
             "💰 Savings (S)", 
             "💸 Taxation (T)", 
             "💵 Income (Y)"]
        )
        
        # Date range selector
        if user_tier == "paid":
            min_date = datetime(1959, 1, 1)
            default_start = datetime(2015, 1, 1)
        else:
            # Free tier: last 5 years only
            min_date = datetime.now() - timedelta(days=5*365)
            default_start = min_date
            
        date_range = st.date_input(
            "Date Range",
            value=(default_start, datetime.now()),
            min_value=min_date,
            max_value=datetime.now()
        )
        
        # Frequency selector (paid only)
        if user_tier == "paid":
            frequency = st.radio(
                "Data Frequency",
                ["Daily", "Monthly", "Quarterly", "Annual"],
                index=2
            )
        else:
            frequency = "Quarterly"
            st.info("🔒 Daily/Monthly data available in paid tier")
        
        st.markdown("---")
        
        # User info
        if username:
            st.markdown(f"**User:** {username}")
            st.markdown(f"**Tier:** {user_tier.title()}")
            if user_tier == "free":
                st.button("⬆️ Upgrade to Pro", type="primary")
        else:
            if st.button("🔐 Login"):
                st.session_state.show_login = True
    
    # Main content area
    if component == "📈 Overview":
        show_overview(user_tier, date_range)
    else:
        show_component_detail(component, date_range, frequency, user_tier)
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("📊 **EFData** - Economic Flow Data")
    with col2:
        st.markdown("🔗 [API Documentation](https://efdata.bicheno.me/api)")
    with col3:
        st.markdown("📧 [Contact Support](mailto:kieran@bicheno.me)")

def show_overview(user_tier, date_range):
    """Display overview dashboard with circular flow visualization"""
    st.title("Australian Economic Flow Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Get latest data summary
    summary = get_circular_flow_summary(date_range[1])
    
    with col1:
        st.metric(
            "Total GDP (Y)", 
            f"${summary['gdp']:,.0f}M",
            f"{summary['gdp_growth']:.1f}% YoY"
        )
    
    with col2:
        st.metric(
            "Flow Imbalance",
            f"{summary['imbalance']:.1f}%",
            "Known methodology variance",
            delta_color="off"
        )
    
    with col3:
        st.metric(
            "Data Freshness",
            f"{summary['days_old']} days",
            "Last RBA update",
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            "Coverage",
            f"{summary['coverage']:.0f}%",
            "All 8 components active"
        )
    
    # Circular flow sankey diagram
    st.subheader("Circular Flow of Income")
    
    if user_tier == "paid":
        fig = create_circular_flow_sankey(date_range)
        st.plotly_chart(fig, use_container_width=True)
    else:
        # Simplified version for free tier
        st.info("🔒 Interactive flow diagram available in paid tier")
        # Show static image or simplified version
        fig = create_circular_flow_sankey(date_range, simplified=True)
        st.plotly_chart(fig, use_container_width=True)
    
    # Component comparison
    st.subheader("Component Trends")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        comparison_fig = create_component_comparison(date_range)
        st.plotly_chart(comparison_fig, use_container_width=True)
    
    with col2:
        st.markdown("### Key Insights")
        st.markdown("""
        - **Consumption (C)** remains the largest component at ~60% of GDP
        - **Government (G)** spending increased significantly post-2020
        - **Trade balance (X-M)** volatile due to commodity prices
        - **Investment (I)** showing signs of recovery
        """)
        
        if user_tier == "free":
            st.markdown("""
            <div class="premium-feature">
            <b>🔒 Premium Features:</b>
            <ul>
            <li>Download this data as CSV/Excel</li>
            <li>Access daily updates</li>
            <li>Custom date ranges</li>
            <li>API access for automation</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
    
    # Data quality heatmap
    st.subheader("Data Coverage & Quality")
    quality_fig = create_data_quality_heatmap()
    st.plotly_chart(quality_fig, use_container_width=True)

def show_component_detail(component, date_range, frequency, user_tier):
    """Display detailed view for a specific component"""
    # Extract component code from display name
    component_code = component.split("(")[1].strip(")")
    component_name = component.split("(")[0].strip()
    
    st.title(f"{component_name} Analysis")
    
    # Get component data
    df = get_component_data(component_code, date_range[0], date_range[1], frequency)
    
    if df.empty:
        st.warning("No data available for selected criteria")
        return
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    latest_value = df['value'].iloc[-1]
    prev_value = df['value'].iloc[-2] if len(df) > 1 else latest_value
    change = ((latest_value - prev_value) / prev_value * 100) if prev_value != 0 else 0
    
    with col1:
        st.metric(
            "Latest Value",
            f"${latest_value:,.0f}M",
            f"{change:+.1f}%"
        )
    
    with col2:
        st.metric(
            "Average",
            f"${df['value'].mean():,.0f}M"
        )
    
    with col3:
        st.metric(
            "Volatility",
            f"{df['value'].std() / df['value'].mean() * 100:.1f}%"
        )
    
    with col4:
        st.metric(
            "Data Points",
            f"{len(df):,}"
        )
    
    # Time series chart
    st.subheader("Historical Trend")
    
    ts_fig = create_time_series_chart(df, component_name, show_advanced=user_tier=="paid")
    st.plotly_chart(ts_fig, use_container_width=True)
    
    # Export options (paid only)
    if user_tier == "paid":
        st.subheader("Export Data")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Download CSV",
                csv,
                f"efdata_{component_code}_{datetime.now():%Y%m%d}.csv",
                "text/csv"
            )
        
        with col2:
            # Excel export would go here
            st.button("📊 Download Excel")
        
        with col3:
            if st.button("🔗 Get API Endpoint"):
                st.code(f"""
curl -X GET "https://api.efdata.bicheno.me/v1/data/{component_code.lower()}?start_date={date_range[0]}&end_date={date_range[1]}&frequency={frequency.lower()}" \\
  -H "Authorization: Bearer YOUR_API_KEY"
""")
    else:
        st.info("🔒 Data export available in paid tier. API access is free with rate limits.")
    
    # Additional analysis
    with st.expander("📊 Statistical Analysis"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Descriptive Statistics")
            st.dataframe(df['value'].describe())
        
        with col2:
            st.markdown("### Seasonal Patterns")
            if user_tier == "paid":
                st.write("Seasonal decomposition chart here")
            else:
                st.info("🔒 Advanced analytics in paid tier")

if __name__ == "__main__":
    main()
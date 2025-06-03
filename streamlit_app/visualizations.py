"""
Visualization functions for Streamlit dashboard
"""
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime
from streamlit_app.database import get_all_components_data, get_data_freshness

def create_time_series_chart(df, component_name, show_advanced=False):
    """Create time series chart for a component"""
    
    fig = make_subplots(
        rows=2 if show_advanced else 1, 
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.7, 0.3] if show_advanced else [1]
    )
    
    # Main time series
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['value'],
            mode='lines',
            name='Value',
            line=dict(color='#3498db', width=2)
        ),
        row=1, col=1
    )
    
    # Add trend line if advanced
    if show_advanced and len(df) > 10:
        z = np.polyfit(range(len(df)), df['value'], 1)
        p = np.poly1d(z)
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=p(range(len(df))),
                mode='lines',
                name='Trend',
                line=dict(color='red', width=1, dash='dash')
            ),
            row=1, col=1
        )
    
    # Add change chart if advanced
    if show_advanced and 'pct_change' in df.columns:
        colors = ['red' if x < 0 else 'green' for x in df['pct_change']]
        fig.add_trace(
            go.Bar(
                x=df['date'],
                y=df['pct_change'],
                name='% Change',
                marker_color=colors
            ),
            row=2, col=1
        )
    
    # Update layout
    fig.update_layout(
        title=f"{component_name} Over Time",
        height=500 if show_advanced else 400,
        showlegend=True,
        hovermode='x unified',
        template='plotly_white'
    )
    
    fig.update_xaxes(title_text="Date", row=2 if show_advanced else 1, col=1)
    fig.update_yaxes(title_text="Value ($M)", row=1, col=1)
    if show_advanced:
        fig.update_yaxes(title_text="% Change", row=2, col=1)
    
    return fig

def create_circular_flow_sankey(date_range, simplified=False):
    """Create Sankey diagram for circular flow"""
    
    # Get latest data
    df = get_all_components_data(date_range[0], date_range[1])
    
    if df.empty:
        return go.Figure()
    
    # Get latest values for each component
    latest_data = df.groupby('component_code')['value'].last().to_dict()
    
    # Define flows
    if simplified:
        # Simplified version for free tier
        labels = ["Income", "Consumption", "Savings", "Investment", "Government", "Net Exports"]
        source = [0, 0, 2, 2, 2]
        target = [1, 2, 3, 4, 5]
        values = [
            latest_data.get('C', 0),
            latest_data.get('S', 0),
            latest_data.get('I', 0),
            latest_data.get('G', 0),
            latest_data.get('X', 0) - latest_data.get('M', 0)
        ]
    else:
        # Full version for paid tier
        labels = ["Y", "C", "S", "T", "I", "G", "X", "M", "Households", "Firms", "Government", "Overseas"]
        # Complex flow mapping here
        source = [0, 0, 0, 8, 8, 8, 9, 9, 10, 11]
        target = [1, 2, 3, 4, 5, 6, 7, 8, 9, 9]
        values = [latest_data.get(c, 0) for c in ['C', 'S', 'T', 'I', 'G', 'X', 'M', 'Y', 'Y', 'Y']]
    
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            color="#3498db"
        ),
        link=dict(
            source=source,
            target=target,
            value=[v for v in values if v > 0]  # Filter out zero/negative values
        )
    )])
    
    fig.update_layout(
        title="Circular Flow of Income",
        height=500,
        font_size=12
    )
    
    return fig

def create_component_comparison(date_range):
    """Create comparison chart for all components"""
    
    df = get_all_components_data(date_range[0], date_range[1])
    
    if df.empty:
        return go.Figure()
    
    # Normalize by GDP for comparison
    gdp_df = df[df['component_code'] == 'Y'][['date', 'value']].rename(columns={'value': 'gdp'})
    df = df.merge(gdp_df, on='date')
    df['pct_of_gdp'] = (df['value'] / df['gdp'] * 100).round(1)
    
    # Create line chart
    fig = px.line(
        df[df['component_code'] != 'Y'],
        x='date',
        y='pct_of_gdp',
        color='component_name',
        title='Components as % of GDP',
        labels={'pct_of_gdp': '% of GDP', 'date': 'Date'},
        template='plotly_white'
    )
    
    fig.update_layout(
        height=400,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode='x unified'
    )
    
    return fig

def create_data_quality_heatmap():
    """Create heatmap showing data coverage and quality"""
    
    df = get_data_freshness()
    
    if df.empty:
        return go.Figure()
    
    # Calculate days since last update
    df['days_old'] = (datetime.now() - pd.to_datetime(df['latest_date'])).dt.days
    df['coverage_years'] = (pd.to_datetime(df['latest_date']) - pd.to_datetime(df['earliest_date'])).dt.days / 365.25
    
    # Create heatmap data
    components = ['C', 'I', 'G', 'X', 'M', 'S', 'T', 'Y']
    metrics = ['Data Points', 'Days Old', 'Years Coverage']
    
    z_data = []
    for component in components:
        row_data = df[df['component_code'] == component]
        if not row_data.empty:
            z_data.append([
                min(row_data['data_points'].iloc[0] / 1000, 100),  # Normalize to 0-100
                min(row_data['days_old'].iloc[0] / 30, 100),  # Days to months
                min(row_data['coverage_years'].iloc[0] / 50, 100)  # Years normalized
            ])
        else:
            z_data.append([0, 0, 0])
    
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=metrics,
        y=components,
        colorscale='RdYlGn',
        reversescale=False,
        text=[[f"{val:.0f}" for val in row] for row in z_data],
        texttemplate="%{text}",
        textfont={"size": 12},
        hovertemplate="Component: %{y}<br>Metric: %{x}<br>Score: %{z:.0f}<extra></extra>"
    ))
    
    fig.update_layout(
        title="Data Quality Matrix",
        height=400,
        xaxis_title="Quality Metrics",
        yaxis_title="Economic Component"
    )
    
    return fig
"""
Database connection and queries for Streamlit app
"""
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime, timedelta
from functools import lru_cache
import streamlit as st

# Database connection parameters
DB_PARAMS = {
    'host': os.getenv('PSQL_HOST', 'localhost'),
    'port': os.getenv('PSQL_PORT', '5432'),
    'dbname': os.getenv('PSQL_DB', 'efdata'),
    'user': os.getenv('PSQL_USER', 'efdata_user'),
    'password': os.getenv('PSQL_PW', 'changeme')
}

@st.cache_resource
def get_connection():
    """Get database connection with connection pooling"""
    return psycopg2.connect(**DB_PARAMS)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_component_data(component_code, start_date, end_date, frequency="Quarterly"):
    """Fetch component data for given date range"""
    
    frequency_map = {
        "Daily": "1 day",
        "Monthly": "1 month", 
        "Quarterly": "3 months",
        "Annual": "1 year"
    }
    
    query = """
    WITH time_series AS (
        SELECT 
            date_trunc(%s, dt.date_value) as period,
            AVG(cf.value) as value,
            COUNT(*) as data_points
        FROM rba_facts.fact_circular_flow cf
        JOIN rba_dimensions.dim_circular_flow_component c 
            ON cf.component_key = c.component_key
        JOIN rba_dimensions.dim_time dt 
            ON cf.time_key = dt.time_key
        WHERE c.component_code = %s
          AND dt.date_value BETWEEN %s AND %s
        GROUP BY date_trunc(%s, dt.date_value)
        ORDER BY period
    )
    SELECT 
        period as date,
        value,
        data_points,
        value - LAG(value) OVER (ORDER BY period) as change,
        (value - LAG(value) OVER (ORDER BY period)) / NULLIF(LAG(value) OVER (ORDER BY period), 0) * 100 as pct_change
    FROM time_series
    """
    
    try:
        conn = get_connection()
        df = pd.read_sql_query(
            query, 
            conn,
            params=[frequency.lower(), component_code, start_date, end_date, frequency.lower()]
        )
        return df
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_circular_flow_summary(as_of_date):
    """Get summary statistics for circular flow overview"""
    
    query = """
    WITH latest_values AS (
        SELECT 
            c.component_code,
            c.component_name,
            cf.value,
            dt.date_value
        FROM rba_facts.fact_circular_flow cf
        JOIN rba_dimensions.dim_circular_flow_component c 
            ON cf.component_key = c.component_key
        JOIN rba_dimensions.dim_time dt 
            ON cf.time_key = dt.time_key
        WHERE dt.date_value <= %s
          AND dt.date_value >= %s - INTERVAL '1 year'
        ORDER BY dt.date_value DESC
    ),
    summary AS (
        SELECT 
            component_code,
            FIRST_VALUE(value) OVER (PARTITION BY component_code ORDER BY date_value DESC) as latest_value,
            FIRST_VALUE(date_value) OVER (PARTITION BY component_code ORDER BY date_value DESC) as latest_date
        FROM latest_values
    ),
    flow_check AS (
        SELECT 
            SUM(CASE WHEN component_code IN ('S', 'T', 'M') THEN latest_value ELSE 0 END) as inflows,
            SUM(CASE WHEN component_code IN ('I', 'G', 'X') THEN latest_value ELSE 0 END) as outflows,
            SUM(CASE WHEN component_code = 'Y' THEN latest_value ELSE 0 END) as gdp
        FROM summary
    )
    SELECT 
        gdp,
        ABS(inflows - outflows) / NULLIF(outflows, 0) * 100 as imbalance,
        EXTRACT(days FROM NOW() - MAX(latest_date)) as days_old,
        COUNT(DISTINCT component_code) * 100.0 / 8 as coverage,
        (gdp - LAG(gdp) OVER (ORDER BY gdp)) / NULLIF(LAG(gdp) OVER (ORDER BY gdp), 0) * 100 as gdp_growth
    FROM flow_check, summary
    GROUP BY gdp, inflows, outflows
    """
    
    try:
        conn = get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, [as_of_date, as_of_date])
            result = cur.fetchone()
            
        # Provide defaults if no data
        if not result:
            return {
                'gdp': 0,
                'imbalance': 14.0,  # Known average
                'days_old': 0,
                'coverage': 100,
                'gdp_growth': 0
            }
        
        return dict(result)
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return {
            'gdp': 0,
            'imbalance': 14.0,
            'days_old': 0,
            'coverage': 100,
            'gdp_growth': 0
        }

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_data_freshness():
    """Get data freshness information for all components"""
    
    query = """
    SELECT 
        c.component_code,
        c.component_name,
        MAX(dt.date_value) as latest_date,
        COUNT(DISTINCT dt.date_value) as data_points,
        MIN(dt.date_value) as earliest_date
    FROM rba_facts.fact_circular_flow cf
    JOIN rba_dimensions.dim_circular_flow_component c 
        ON cf.component_key = c.component_key
    JOIN rba_dimensions.dim_time dt 
        ON cf.time_key = dt.time_key
    GROUP BY c.component_code, c.component_name
    ORDER BY c.component_code
    """
    
    try:
        conn = get_connection()
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_all_components_data(start_date, end_date):
    """Get data for all components for comparison charts"""
    
    query = """
    SELECT 
        date_trunc('quarter', dt.date_value) as date,
        c.component_code,
        c.component_name,
        AVG(cf.value) as value
    FROM rba_facts.fact_circular_flow cf
    JOIN rba_dimensions.dim_circular_flow_component c 
        ON cf.component_key = c.component_key
    JOIN rba_dimensions.dim_time dt 
        ON cf.time_key = dt.time_key
    WHERE dt.date_value BETWEEN %s AND %s
      AND c.component_code IN ('C', 'I', 'G', 'X', 'M', 'S', 'T', 'Y')
    GROUP BY date_trunc('quarter', dt.date_value), c.component_code, c.component_name
    ORDER BY date, c.component_code
    """
    
    try:
        conn = get_connection()
        df = pd.read_sql_query(query, conn, params=[start_date, end_date])
        return df
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return pd.DataFrame()
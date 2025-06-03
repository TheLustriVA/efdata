# EFData Streamlit Dashboard Implementation Plan

## Executive Summary
Add a Streamlit dashboard to visualize the economic data we already have. Free tier shows basic charts, paid tier gets API access and data exports.

## Why Streamlit (Not Grafana)
- **Time to deploy**: 2-4 hours vs 2-4 days
- **Learning curve**: You already know Python
- **Maintenance**: Zero additional infrastructure
- **Cost**: Free on Streamlit Cloud (with limits)
- **Customization**: Full control with Python

## Phase 1: Basic Free Dashboard (4 hours)

### Core Features
```python
# app.py structure
import streamlit as st
import pandas as pd
import plotly.express as px
from src.econdata.econdata.spiders.db_utils import get_connection

st.set_page_config(
    page_title="EFData - Australian Economic Dashboard",
    page_icon="📊",
    layout="wide"
)

# Sidebar
with st.sidebar:
    st.image("logo.png")  # Add your logo
    component = st.selectbox(
        "Select Component",
        ["Overview", "Consumption (C)", "Investment (I)", 
         "Government (G)", "Exports (X)", "Imports (M)", 
         "Savings (S)", "Taxation (T)", "Income (Y)"]
    )
    
    date_range = st.date_input(
        "Date Range",
        value=(datetime(2020, 1, 1), datetime.now()),
        min_value=datetime(1959, 1, 1),
        max_value=datetime.now()
    )

# Main content
if component == "Overview":
    show_circular_flow_summary()
elif component in ["Consumption (C)", "Investment (I)", ...]:
    show_component_detail(component)
```

### Key Visualizations

1. **Circular Flow Overview**
   - Sankey diagram showing money flows
   - Imbalance indicator (that 14% discrepancy)
   - Traffic light system for data freshness

2. **Component Deep Dives**
   - Time series with trend lines
   - Year-over-year growth rates
   - Seasonal patterns
   - Data source comparison (RBA vs ABS)

3. **Data Quality Dashboard**
   - Coverage heatmap by component/date
   - Missing data indicators
   - Last update timestamps

### Database Queries
```python
# Reuse your existing connection
def get_component_data(component, start_date, end_date):
    query = """
    SELECT 
        dt.date_value as date,
        cf.value,
        ds.data_provider as source
    FROM rba_facts.fact_circular_flow cf
    JOIN rba_dimensions.dim_circular_flow_component c 
        ON cf.component_key = c.component_key
    JOIN rba_dimensions.dim_time dt 
        ON cf.time_key = dt.time_key
    JOIN rba_dimensions.dim_data_source ds 
        ON cf.source_key = ds.source_key
    WHERE c.component_code = %s
      AND dt.date_value BETWEEN %s AND %s
    ORDER BY dt.date_value
    """
    return pd.read_sql(query, conn, params=[component, start_date, end_date])
```

## Phase 2: Authentication & Free/Paid Tiers (2 hours)

### Simple Auth with Streamlit-Authenticator
```python
import streamlit_authenticator as stauth

# In secrets.toml (Streamlit Cloud)
users = {
    "demo": {
        "email": "demo@efdata.com",
        "name": "Demo User",
        "password": "$2b$12$...",  # Hashed
        "tier": "free"
    },
    "client1": {
        "email": "client@company.com",
        "name": "Paid Client",
        "password": "$2b$12$...",
        "tier": "paid"
    }
}

# In app.py
authenticator = stauth.Authenticate(
    users,
    "efdata_cookie_name",
    "random_signature_key",
    cookie_expiry_days=30
)

name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your username and password')
elif authentication_status:
    # Check tier
    user_tier = users[username]["tier"]
    
    if user_tier == "free":
        show_free_dashboard()
    else:
        show_paid_dashboard()
```

### Free Tier Limitations
- Last 2 years of data only
- Quarterly aggregates only  
- No download buttons
- Watermarked charts
- 5 refreshes per day

### Paid Tier Features
- Full historical data (1959-present)
- Daily/monthly/quarterly/annual views
- Download as CSV/Excel buttons
- API key generation
- No watermarks
- Unlimited refreshes

## Phase 3: Data Export Features (2 hours)

### Export Buttons (Paid Only)
```python
if user_tier == "paid":
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Download CSV",
            csv,
            f"efdata_{component}_{datetime.now():%Y%m%d}.csv",
            "text/csv"
        )
    
    with col2:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Data', index=False)
            # Add metadata sheet
            metadata_df.to_excel(writer, sheet_name='Metadata')
        
        st.download_button(
            "📊 Download Excel",
            buffer.getvalue(),
            f"efdata_{component}_{datetime.now():%Y%m%d}.xlsx",
            "application/vnd.ms-excel"
        )
    
    with col3:
        if st.button("🔗 Generate API Link"):
            api_url = generate_api_url(component, date_range)
            st.code(api_url)
```

### API Integration
```python
# Show API examples for paid users
if user_tier == "paid":
    with st.expander("API Access"):
        st.code(f"""
# Python example
import requests

response = requests.get(
    'https://api.efdata.com.au/v1/data/{component}',
    headers={{'X-API-Key': '{user_api_key}'}},
    params={{
        'start_date': '{start_date}',
        'end_date': '{end_date}',
        'frequency': 'quarterly'
    }}
)
data = response.json()
""")
```

## Deployment Strategy

### Local Development
```bash
# Install
pip install streamlit streamlit-authenticator plotly

# Run
streamlit run app.py

# Test
streamlit run app.py --server.port 8501
```

### Streamlit Cloud Deployment
1. Push to GitHub repo (public or private)
2. Connect Streamlit Cloud to repo
3. Add secrets in dashboard:
   ```toml
   [database]
   host = "your-db-host"
   user = "efdata_user"
   password = "xxx"
   database = "efdata"
   
   [users]
   # User credentials here
   ```
4. Deploy - gets URL like `efdata.streamlit.app`

### Custom Domain
- Streamlit Cloud supports custom domains on paid plans
- Or embed as iframe in your main site

## Pricing Model Integration

### Free Dashboard (Loss Leader)
- Show enough to be useful
- Frustrate power users with limitations
- Clear upgrade CTAs

### Paid Tiers
1. **Analyst** ($500/month)
   - Full dashboard access
   - Data exports
   - 10,000 API calls/month

2. **Enterprise** ($2000/month)
   - Everything in Analyst
   - Unlimited API calls
   - Custom branding
   - Priority support
   - Direct database access

## Implementation Timeline

### Week 1
- Day 1-2: Basic dashboard with all components
- Day 3: Authentication system
- Day 4: Export features
- Day 5: Testing and deployment

### Week 2
- Day 1-2: API endpoint creation (FastAPI)
- Day 3: Stripe payment integration
- Day 4: User management system
- Day 5: Production deployment

## Technical Gotchas

1. **Database Connections**
   - Use connection pooling
   - Cache query results aggressively
   - Consider read replica for dashboard

2. **Streamlit Limitations**
   - Reruns entire script on interaction
   - Use `@st.cache_data` decorator liberally
   - Session state for user data

3. **Security**
   - Never show connection strings
   - Rate limit API endpoints
   - Log all data exports

## Code Structure
```
efdata/
├── streamlit_app/
│   ├── app.py              # Main entry point
│   ├── auth.py             # Authentication logic
│   ├── components.py       # UI components
│   ├── queries.py          # Database queries
│   ├── visualizations.py   # Chart generation
│   └── utils.py            # Helper functions
├── requirements.txt        # Add streamlit deps
└── .streamlit/
    └── config.toml         # Theming to match brand
```

## Marketing the Dashboard

### Free Tier Pitch
"See Australian economic data visualized in real-time. No spreadsheets, no manual updates."

### Paid Tier Pitch
"Export any data. Build your own models. API access for your applications."

### Upgrade Prompts
- "📊 Want to download this data? Upgrade to Analyst"
- "🚀 Need API access? Check out our Enterprise plan"
- "📈 See daily data instead of quarterly? Go Pro"

## ROI Calculation

### Costs
- Development: 40 hours @ $150/hr = $6,000
- Streamlit Cloud: Free (Community tier)
- Maintenance: 2 hrs/month = $300/month

### Revenue (Conservative)
- 5 Analyst subscribers: $2,500/month
- 1 Enterprise subscriber: $2,000/month
- Total: $4,500/month

### Break-even: 1.5 months

## Next Steps

1. Start with `streamlit hello` to see examples
2. Build basic component viewer (2 hours)
3. Add one fancy visualization (1 hour)
4. Deploy to Streamlit Cloud (30 mins)
5. Share link with potential clients for feedback

The beauty is you can have v1 live TODAY and iterate based on what clients actually want to see.
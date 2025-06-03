# EFData Streamlit Dashboard

## Quick Start

### Local Development

```bash
# From the streamlit_app directory
cd streamlit_app

# Install dependencies
pip install -r requirements.txt

# Set environment variables (or use .env file)
export PSQL_HOST=localhost
export PSQL_DB=efdata
export PSQL_USER=efdata_user
export PSQL_PW=yourpassword

# Run the dashboard
streamlit run app.py
```

Access at: http://localhost:8501

### Demo Credentials

- **Free tier**: username: `demo`, password: `demo123`
- **Paid tier**: username: `premium`, password: `premium123`

## Features

### Free Tier
- View all 8 economic components
- Quarterly data for last 5 years
- Basic visualizations
- API endpoint information

### Paid Tier
- Full historical data (1959-present)
- Daily/Monthly/Quarterly/Annual views
- Export to CSV/Excel
- Advanced analytics
- No rate limits

## Deployment

### Deploy to Streamlit Cloud

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Select `streamlit_app/app.py` as the main file
5. Add secrets in dashboard:

```toml
[database]
PSQL_HOST = "your-db-host"
PSQL_DB = "efdata"
PSQL_USER = "efdata_user"
PSQL_PW = "your-password"
PSQL_PORT = "5432"
```

### Deploy with Docker

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## Customization

### Adding New Visualizations

1. Add function to `visualizations.py`
2. Import in `app.py`
3. Add to appropriate section

### Modifying Authentication

Edit `auth.py` to:
- Connect to your user database
- Implement OAuth
- Add more user tiers

### Changing Theme

Edit `.streamlit/config.toml` to match your brand colors.

## API Integration

The dashboard shows example API calls. Actual API implementation is separate (FastAPI).

## Performance

- Database queries are cached for 5 minutes
- Static data cached for 1 hour
- Use `@st.cache_data` for expensive computations
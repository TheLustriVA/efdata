#!/bin/bash
# Launch EFData Streamlit Dashboard

echo "🚀 Starting EFData Dashboard..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Change to streamlit directory
cd streamlit_app

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit not found. Installing..."
    pip install -r requirements.txt
fi

# Run streamlit
echo "📊 Dashboard starting at http://localhost:8501"
streamlit run app.py \
    --server.port 8501 \
    --server.address localhost \
    --browser.gatherUsageStats false
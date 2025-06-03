#!/bin/bash
# MindsDB Setup Script for Econcell Integration
# Date: January 6, 2025

echo "Setting up MindsDB for Econcell economic data analysis..."

# Check if required environment variables are set
if [ -z "$VENICE_API_KEY" ]; then
    echo "Warning: VENICE_API_KEY not set. Venice integration will not work."
fi

if [ -z "$PSQL_USER" ] || [ -z "$PSQL_PW" ]; then
    echo "Warning: PostgreSQL credentials not set. Database integration will not work."
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "Warning: Ollama doesn't appear to be running on localhost:11434"
    echo "MindsDB will not be able to use local Ollama models."
fi

# Start MindsDB
echo "Starting MindsDB containers..."
docker-compose -f mindsdb-econcell-compose.yml up -d

# Wait for MindsDB to be healthy
echo "Waiting for MindsDB to start..."
for i in {1..30}; do
    if curl -s http://localhost:47334/api/util/ping > /dev/null; then
        echo "MindsDB is running!"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 5
done

# Create initial connections via SQL API
echo "Setting up MindsDB connections..."

# Create Ollama ML engine
cat << EOF > /tmp/mindsdb_setup.sql
-- Create Ollama ML engine
CREATE ML_ENGINE IF NOT EXISTS ollama_engine
FROM ollama
USING
  base_url = 'http://host.docker.internal:11434';

-- Create models using your preferred Ollama models
CREATE MODEL IF NOT EXISTS qwen_coder
PREDICT response
USING
  engine = 'ollama_engine',
  model_name = 'qwen2.5-coder:32b',
  prompt_template = 'Analyze this economic data pattern: {{text}}';

CREATE MODEL IF NOT EXISTS phi_reasoning  
PREDICT response
USING
  engine = 'ollama_engine',
  model_name = 'phi4-reasoning:14b',
  prompt_template = 'Find novel patterns in: {{text}}';

-- Connect to your Econcell database
CREATE DATABASE IF NOT EXISTS econcell_db
WITH ENGINE = 'postgres',
PARAMETERS = {
  "host": "host.docker.internal",
  "port": 5432,
  "database": "econcell",
  "user": "$PSQL_USER",
  "password": "$PSQL_PW"
};
EOF

echo ""
echo "MindsDB Setup Complete!"
echo "========================"
echo "Access MindsDB at:"
echo "- Web UI: http://localhost:47334"
echo "- MySQL API: mysql -h 127.0.0.1 -P 47335 -u mindsdb"
echo "- PostgreSQL API: psql -h localhost -p 47337 -U mindsdb"
echo ""
echo "Next steps:"
echo "1. Upload the SQL setup script to MindsDB"
echo "2. Create pattern-finding queries for your economic data"
echo "3. Set up automated analysis jobs"
echo ""
echo "To stop MindsDB: docker-compose -f mindsdb-econcell-compose.yml down"
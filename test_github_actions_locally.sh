#!/bin/bash
# Test GitHub Actions locally to catch errors before pushing

echo "=== Testing Docker Build Workflow ==="
echo "1. Building Docker image..."
docker build -t efdata:test . || { echo "❌ Docker build failed"; exit 1; }

echo -e "\n2. Testing Docker Compose config..."
cp .env.example .env.test
docker-compose --env-file .env.test config > /dev/null || { echo "❌ Docker compose config failed"; exit 1; }
rm .env.test

echo -e "\n3. Checking for secrets in code..."
if grep -r -E "(password|api_key|secret)\s*=\s*['\"][^'\"]{3,}['\"]" --include="*.py" --exclude-dir=".venv" --exclude-dir=".git" . | grep -v -E "(getenv|environ|example|\.env|input\(|st\.text_input|settings\.get)"; then
    echo "❌ WARNING: Possible hardcoded secrets found!"
    exit 1
fi
echo "✅ No hardcoded secrets detected"

echo -e "\n=== Testing Data Validation Workflow ==="
echo "4. Testing Python syntax..."
find src/econdata/econdata/spiders -name "*.py" -type f -exec python -m py_compile {} \; || { echo "❌ Python syntax check failed"; exit 1; }

echo -e "\n5. Testing RBA endpoint..."
cat << 'EOF' > test_rba.py
import requests
try:
    response = requests.get('https://api.rba.gov.au/statistics/tables', timeout=10)
    if response.status_code != 200:
        print(f'❌ ERROR: RBA API returned {response.status_code}')
        exit(1)
    print('✅ RBA API accessible')
except Exception as e:
    print(f'❌ ERROR: {e}')
    exit(1)
EOF
python test_rba.py || { echo "❌ RBA endpoint test failed"; exit 1; }
rm test_rba.py

echo -e "\n✅ All tests passed! Safe to push to GitHub"
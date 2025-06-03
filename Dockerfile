FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY pyproject.toml uv.lock* ./
COPY requirements*.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir uv && \
    uv pip install --system -r requirements.txt || \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY setup/ ./setup/
COPY main.py ./
COPY .env.example ./

# Create necessary directories
RUN mkdir -p logs downloads

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python", "main.py"]
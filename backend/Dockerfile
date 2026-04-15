FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for Playwright + lxml + Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg ca-certificates \
    gcc g++ libxml2-dev libxslt1-dev zlib1g-dev libjpeg62-turbo-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium browser + its OS deps
RUN playwright install chromium --with-deps

# Copy application code
COPY . .

# Non-root user for security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

# 2 workers for handling concurrent requests (pipeline runs + health checks)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]

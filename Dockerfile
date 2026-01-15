FROM python:3.13-slim

# Install diatheke (SWORD CLI)
RUN apt-get update && apt-get install -y --no-install-recommends \
    diatheke \
    unzip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy SWORD modules and extract them
COPY data/sword/*.zip /app/data/sword/
RUN mkdir -p /app/data/sword/mods.d /app/data/sword/modules && \
    cd /app/data/sword && \
    for f in *.zip; do unzip -o "$f"; done

# Copy application code
COPY app/ /app/app/
COPY scripts/ /app/scripts/

# Set environment variables
ENV PYTHONPATH=/app
ENV DATABASE_PATH=/data/commentariat.db
# Note: SWORD_PATH is set dynamically per-module, not globally

# Expose port
EXPOSE 8000

# Default command - startup script handles DB init and ingestion
CMD ["python", "scripts/startup.py"]

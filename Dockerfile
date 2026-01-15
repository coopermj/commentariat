FROM python:3.13-slim

# Install diatheke (SWORD CLI) and KJV module
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsword-utils \
    sword-text-kjv \
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
ENV SWORD_PATH=/app/data/sword
ENV DATABASE_PATH=/data/commentariat.db

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

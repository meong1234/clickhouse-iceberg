FROM python:3.10-slim

WORKDIR /app

# Install required system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Only keep Python unbuffered output setting here, move AWS settings to docker-compose
ENV PYTHONUNBUFFERED=1

# Install packages with compatible versions for PyIceberg 0.9.0
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    numpy==1.24.3 \
    pandas==1.5.3 \
    pyarrow==14.0.1 \
    pyiceberg==0.9.0 \
    fsspec==2023.9.2 \
    s3fs==2023.9.2 \
    requests \
    aiohttp \
    fastparquet

# Set up log directory
RUN mkdir -p /var/log/schema

# Copy the application code
COPY . /app/

# Command will be provided by docker-compose
CMD ["python", "create_battery_schema.py"]

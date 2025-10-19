FROM apache/airflow:2.8.0-python3.11

USER root

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Copy requirements
COPY requirements.txt /requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /requirements.txt

# Create data directories
USER root
RUN mkdir -p /opt/airflow/data/raw && \
    mkdir -p /opt/airflow/data/bronze && \
    mkdir -p /opt/airflow/data/silver && \
    mkdir -p /opt/airflow/data/gold && \
    chown -R airflow:root /opt/airflow/data

USER airflow

# Copy source code
COPY --chown=airflow:root ./src /opt/airflow/src
COPY --chown=airflow:root ./dags /opt/airflow/dags

# Brewery Data Pipeline - Medallion Architecture

A production-ready data pipeline that ingests brewery data from the Open Brewery DB API and processes it through a medallion architecture (Bronze → Silver → Gold layers).

## 🚀 Two Implementation Options

This repository provides **two complete implementations** for different environments:

### 1️⃣ **Airflow + Docker** (On-Premise/Self-Hosted)
- 📂 **Location**: Root directory
- 🔧 **Stack**: Apache Airflow, Docker, Pandas, Parquet
- 🎯 **Best For**: Local development, on-premise deployments, full control
- 📖 **Setup**: See instructions below

### 2️⃣ **Databricks + Azure** (Cloud-Native)
- 📂 **Location**: [`databricks_azure/`](./databricks_azure/)
- 🔧 **Stack**: Databricks, PySpark, Azure Blob Storage, Delta Lake
- 🎯 **Best For**: Cloud deployments, scalability, distributed processing
- 💰 **Free Tier**: Compatible with Databricks Community Edition + Azure Free Tier
- 📖 **Setup**: See [databricks_azure/SETUP_GUIDE.md](./databricks_azure/SETUP_GUIDE.md)

**Choose the implementation that best fits your infrastructure and team expertise!**

---

## 📋 Airflow + Docker Implementation

## 🏗️ Architecture

### Medallion Architecture Layers

```
┌─────────────┐
│   API       │  Open Brewery DB API
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   BRONZE    │  Raw JSON data (as received from API)
│   Layer     │  - Minimal transformation
└──────┬──────┘  - Timestamped with metadata
       │          - Preserves original structure
       ▼
┌─────────────┐
│   SILVER    │  Curated Parquet data
│   Layer     │  - Cleaned and validated
└──────┬──────┘  - Partitioned by location (country/state)
       │          - Schema enforcement
       ▼          - Data quality transformations
┌─────────────┐
│    GOLD     │  Aggregated analytics views
│   Layer     │  - Breweries by type and location
└─────────────┘  - Summary statistics
                 - Ready for BI tools
```

### Key Features

✅ **Robust Error Handling**: Retry logic, exception handling, comprehensive logging
✅ **Data Quality Gate**: Quality checks between Silver and Gold layers with pipeline halt on failure
✅ **Automatic Data Cleanup**: Silver layer auto-cleanup before each run to prevent data corruption
✅ **Character Encoding Support**: UTF-8 with special character handling (German umlauts, accents, etc.)
✅ **Timestamped Outputs**: Gold layer files include date + time for unique identification
✅ **Partitioning**: Silver layer partitioned by country and state
✅ **Containerization**: Fully Dockerized with docker-compose
✅ **Orchestration**: Apache Airflow with proper dependency management
✅ **Standalone Execution**: Can run without Docker for development/testing
✅ **Testing**: Comprehensive unit tests with pytest
✅ **Monitoring**: Built-in data quality monitoring and alerting strategy

## 📁 Project Structure

```
brewery_case/
├── dags/
│   └── brewery_pipeline.py          # Airflow DAG definition
├── src/
│   ├── api/
│   │   └── brewery_api.py           # API extraction with retry logic
│   ├── bronze/
│   │   └── bronze_layer.py          # Raw data persistence
│   ├── silver/
│   │   └── silver_layer.py          # Parquet transformation & partitioning
│   ├── gold/
│   │   └── gold_layer.py            # Analytical aggregations
│   ├── common/
│   │   └── data_quality.py          # Data quality validation
│   └── tests/
│       ├── test_api.py
│       ├── test_bronze.py
│       └── test_silver.py
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── requirements.txt
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- 4GB+ RAM

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/paulo-orlando/brewery_case.git
cd brewery_case
```

2. **Set up environment variables** (optional)
```bash
export AIRFLOW_UID=$(id -u)
```

3. **Start the services**
```bash
cd docker
docker-compose up -d
```

4. **Wait for services to initialize** (1-2 minutes)
```bash
docker-compose ps
```

5. **Access Airflow UI**
- URL: http://localhost:8080
- Username: `airflow`
- Password: `airflow`

6. **Enable and trigger the DAG**
- Navigate to the `brewery_pipeline` DAG
- Toggle it ON
- Click "Trigger DAG"

### Local Development (Without Docker)

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run complete standalone pipeline
python run_pipeline_standalone.py

# Run tests
pytest src/tests/ -v --cov=src

# Test individual layers
python src/api/brewery_api.py ./data/raw
python src/bronze/bronze_layer.py ./data/raw ./data/bronze
python src/silver/silver_layer.py ./data/bronze ./data/silver
python src/gold/gold_layer.py ./data/silver ./data/gold
python src/common/data_quality.py ./data/silver silver

# Check medallion structure
python check_medallion_structure.py
```

## 🔍 Pipeline Details

### Task Flow

```
extract_brewery_data
        ↓
  load_to_bronze
        ↓
  clean_silver_layer (NEW - Auto cleanup)
        ↓
 transform_to_silver
        ↓
  data_quality_check (QUALITY GATE - Pipeline halts on failure)
        ↓
create_gold_aggregations
```

**Key Changes**:
- 🧹 **Silver Cleanup**: Automatic removal of old/corrupted data before transformation
- 🛡️ **Quality Gate**: Data quality check now runs BEFORE Gold layer (prevents bad data propagation)
- ⏰ **Timestamped Outputs**: Gold files include both date and time (YYYYMMDD_HHMMSS)

### 1. Extract (API Layer)

**Module**: `src/api/brewery_api.py`

- Fetches all brewery data from Open Brewery DB API
- Pagination support (200 records per page)
- Exponential backoff retry logic (3 attempts)
- Timeout handling (30 seconds)
- Saves raw JSON with extraction metadata

**Output**: `/opt/airflow/data/raw/{execution_date}/breweries_*.json`

### 2. Bronze Layer

**Module**: `src/bronze/bronze_layer.py`

- Preserves raw data in original JSON format
- Adds ingestion metadata and lineage tracking
- No transformation applied
- Serves as immutable source of truth

**Output**: `/opt/airflow/data/bronze/breweries/{execution_date}/bronze_breweries_*.json`

### 3. Silver Layer

**Module**: `src/silver/silver_layer.py`

**Transformations Applied**:
- ✅ Convert JSON to Parquet (Snappy compression)
- ✅ Partition by `country` and `state`
- ✅ Standardize column names
- ✅ Handle missing values and nulls
- ✅ Parse and validate coordinates (lat/long)
- ✅ Remove duplicate records
- ✅ **Character encoding fixes** for special characters (ä, ö, ü, ñ, é, etc.)
- ✅ **Auto cleanup** before processing (removes old/corrupted files)
- ✅ Add derived columns:
  - `ingestion_date`
  - `ingestion_timestamp`
  - `location_key`
  - `has_complete_address`
  - `has_coordinates`

**Character Encoding**:
- Handles German umlauts: ä → ä, ö → ö, ü → ü
- Handles Spanish/French characters: ñ → ñ, é → é, à → à
- Special fix for "Kärnten" and other location names
- UTF-8 encoding throughout the pipeline

**Output**: `/opt/airflow/data/silver/breweries/` (partitioned)
```
silver/breweries/
  country=United States/
    state=California/
      part-0.parquet
    state=Oregon/
      part-0.parquet
```

### 4. Gold Layer

**Module**: `src/gold/gold_layer.py`

**Aggregations Created**:
1. **Breweries by Type and Location**
   - Grouped by: `country`, `state`, `brewery_type`
   - Metrics:
     - `brewery_count`: Total breweries
     - `unique_cities`: Number of cities
     - `avg_latitude`, `avg_longitude`: Centroid coordinates
     - `pct_with_coordinates`: Percentage with geolocation
     - `pct_with_address`: Percentage with complete address
   - **Creates complete cross-tabulation**: All state+type combinations (including zero counts)
   - **Example**: 16 countries × 125 states × 13 types = 26,000 rows

2. **Summary Statistics**
   - Total breweries
   - Unique countries, states, cities
   - Top 10 states and cities
   - Brewery type distribution
   - Data quality metrics

**Output** (with timestamp YYYYMMDD_HHMMSS):
- `/opt/airflow/data/gold/breweries_by_type_location/breweries_by_type_location_20251020_130013.parquet`
- `/opt/airflow/data/gold/breweries_by_type_location/breweries_by_type_location_20251020_130013.csv` (UTF-8-sig encoding)
- `/opt/airflow/data/gold/summary_statistics_20251020_130013.json`

**Why 8,923 → 26,000 rows?**
The Gold layer creates a **complete analytical cube** with one row for each unique combination of country + state + brewery_type. This includes zero counts (e.g., "Australia/ACT/brewpub = 0") for comprehensive analysis.

### 5. Data Quality Checks

**Module**: `src/common/data_quality.py`

**Pipeline Behavior**:
- ✅ **Quality Gate Position**: Runs BETWEEN Silver and Gold layers (Stage 4/6)
- ✅ **Pipeline Halt**: If status = FAILED, pipeline stops and Gold layer is NOT created
- ✅ **Warnings Allowed**: If status = WARNING, pipeline continues with logged issues
- ✅ **Protection**: Prevents bad data from reaching expensive Gold aggregations

**Checks Performed**:
1. ✅ **Minimum Record Count**: Ensures sufficient data (threshold: 100 records)
2. ✅ **Duplicate Detection**: Flags duplicate IDs (threshold: <5%)
3. ✅ **Data Completeness**: Validates critical fields (threshold: >70%)
4. ✅ **Coordinate Availability**: Checks geolocation data (threshold: >50%)
5. ✅ **Schema Validation**: Ensures required columns exist

**Severity Levels**:
- `CRITICAL`: Pipeline fails immediately, Gold layer not created
- `WARNING`: Pipeline continues, issues logged for review
- `INFO`: Pass, everything OK

**Example Output**:
```
✅ Quality check complete!
   • Status: PASSED
   • Total validated records: 8,781
   • Checks performed: 5
   • Checks passed: 5
   • Success rate: 100.0%
```

## 📊 Monitoring & Alerting Strategy

## 🆕 Recent Improvements (v0.0.6)

### 1. Quality Gate Implementation
**Problem**: Bad data could reach Gold layer, causing expensive reprocessing
**Solution**: Moved data quality checks BEFORE Gold layer creation
- Pipeline now halts on FAILED quality status
- Gold aggregations only run on clean, validated data
- Saves compute resources and prevents data corruption

### 2. Silver Layer Auto-Cleanup
**Problem**: Accumulated data from multiple runs caused:
- High duplicate rates (66.67% → false warnings)
- Corrupted Parquet files from schema changes
- Quality check failures

**Solution**: Automatic cleanup before each Silver transformation
- Removes entire Silver directory before processing
- Ensures fresh start with consistent schema
- Quality scores improved from 80% to 100%

**Implementation**:
- **Standalone**: `shutil.rmtree()` in `run_pipeline_standalone.py` (lines 106-111)
- **Airflow**: `BashOperator` with `rm -rf` command in DAG (lines 57-59)

### 3. Gold Layer Timestamping
**Problem**: Files with same date overwrite each other
**Solution**: Include time in filename
- Before: `breweries_by_type_location_20251020.csv`
- After: `breweries_by_type_location_20251020_130013.csv`
- Format: `YYYYMMDD_HHMMSS` for unique identification

### 4. Character Encoding Fixes
**Problem**: Special characters corrupted (K�rnten instead of Kärnten)
**Solution**: Comprehensive UTF-8 handling
- Added `fix_encoding()` function in Silver layer
- Handles German umlauts (ä, ö, ü), Spanish/French accents (ñ, é, à)
- CSV exports use `utf-8-sig` encoding (Excel-compatible)

### 5. Code Localization
**Problem**: Mixed Portuguese and English comments
**Solution**: Complete English translation
- All comments, docstrings, and print statements translated
- Consistent English throughout codebase
- Better maintainability for international teams

### Performance Impact
- **Pipeline Duration**: ~20-45 seconds (consistent)
- **Quality Score**: 100% (up from 80%)
- **Zero Warnings**: No more duplicate/corruption issues
- **Clean Outputs**: Every run produces fresh, validated data

## 📊 Monitoring & Alerting Strategy

### Built-in Monitoring

1. **Airflow UI**
   - Task duration tracking
   - Success/failure rates
   - Execution logs
   - Resource utilization

2. **Data Quality Dashboard**
   - Automated quality checks in pipeline
   - Results logged to `/opt/airflow/logs/`
   - JSON reports in Gold layer

3. **Logging**
   - Structured logging with Python logging module
   - Log levels: INFO, WARNING, ERROR, CRITICAL
   - Centralized in Airflow logs

### Recommended Production Monitoring

#### 1. Pipeline Health Monitoring

```python
# Metrics to track:
- Task execution duration (SLA: < 15 minutes)
- Task failure rate (Target: < 1%)
- Data freshness (Max delay: 24 hours)
- Resource utilization (CPU, Memory, Disk)
```

**Tools**: 
- Airflow SLA monitoring
- Prometheus + Grafana for metrics
- CloudWatch/Datadog for cloud deployments

#### 2. Data Quality Monitoring

```python
# Metrics to track:
- Record count variance (Alert if > 20% change)
- Null percentage in critical fields (Alert if > 10%)
- Duplicate records (Alert if > 5%)
- Schema drift detection
- Partition imbalance
```

**Implementation**:
- Extend `data_quality.py` with custom thresholds
- Store quality metrics in time-series database
- Create Grafana dashboards for visualization

#### 3. Alert Channels

**Critical Alerts** (Pipeline failures, data quality failures):
- Email: `email_on_failure=True` in DAG args
- Slack: Airflow Slack webhook integration
- PagerDuty: For 24/7 on-call rotation

**Warning Alerts** (Performance degradation, quality warnings):
- Email digests (daily summary)
- Slack channel (non-urgent)

**Implementation Example**:
```python
# In DAG:
default_args = {
    'email_on_failure': True,
    'email': ['data-team@company.com'],
    'on_failure_callback': slack_alert_function,
    'sla': timedelta(minutes=15),
}
```

#### 4. Observability Best Practices

1. **Structured Logging**
```python
import logging
logging.info(
    "Pipeline completed",
    extra={
        "records_processed": count,
        "execution_time": duration,
        "layer": "silver"
    }
)
```

2. **Custom Metrics**
```python
from airflow.providers.statsd.stats import Stats
stats = Stats()
stats.incr('brewery_pipeline.records_processed', count)
stats.timing('brewery_pipeline.duration', duration)
```

3. **Health Checks**
```bash
# Add health check endpoint
curl http://localhost:8080/health
```

4. **Data Lineage Tracking**
- Track data flow through layers with metadata
- Store execution metadata in Gold layer
- Use Airflow XCom for inter-task communication

### Alerting Rules

| Condition | Severity | Action | Channel |
|-----------|----------|--------|---------|
| Pipeline failure | CRITICAL | Immediate investigation | PagerDuty + Slack |
| Quality check failure | CRITICAL | Data review required | Email + Slack |
| Task duration > 15min | WARNING | Performance review | Slack |
| Record count variance > 20% | WARNING | Data investigation | Email |
| Disk usage > 80% | WARNING | Cleanup/scaling | Slack |

## 🧪 Testing

### Run All Tests
```bash
pytest src/tests/ -v --cov=src --cov-report=html
```

### Run Specific Test Modules
```bash
pytest src/tests/test_api.py -v
pytest src/tests/test_bronze.py -v
pytest src/tests/test_silver.py -v
```

### Test Coverage
- Target: >80% code coverage
- Current modules have comprehensive unit tests
- Mocking external API calls for reliability

## 🔧 Configuration

### Environment Variables

Create `.env` file in project root:
```env
# Airflow
AIRFLOW_UID=50000
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=true

# Database
POSTGRES_USER=airflow
POSTGRES_PASSWORD=airflow
POSTGRES_DB=airflow

# API
BREWERY_API_URL=https://api.openbrewerydb.org/v1/breweries
API_TIMEOUT=30
API_RETRY_ATTEMPTS=3

# Data Quality Thresholds
DQ_MIN_RECORDS=100
DQ_MAX_DUPLICATE_PCT=5
DQ_MIN_COMPLETENESS_PCT=70
```

### DAG Configuration

Edit `dags/brewery_pipeline.py`:
```python
# Schedule
schedule_interval='@daily'  # Run daily at midnight
# OR
schedule_interval='0 2 * * *'  # Run at 2 AM

# Retries
'retries': 3,
'retry_delay': timedelta(minutes=5),

# Timeout
'execution_timeout': timedelta(hours=1),
```

## 🐛 Troubleshooting

### Common Issues

1. **Docker services won't start**
```bash
# Check logs
docker-compose logs -f

# Restart services
docker-compose down -v
docker-compose up -d
```

2. **Permission denied errors**
```bash
# Fix permissions
mkdir -p ./logs ./plugins
chmod -R 777 ./logs ./plugins
```

3. **DAG not appearing in UI**
```bash
# Check for Python errors
docker-compose exec airflow-webserver airflow dags list
docker-compose exec airflow-webserver python /opt/airflow/dags/brewery_pipeline.py
```

4. **Import errors in tasks**
```bash
# Verify module installation
docker-compose exec airflow-webserver pip list
docker-compose exec airflow-webserver python -c "from src.api.brewery_api import fetch_brewery_data"
```

## 📈 Performance Optimization

### Current Performance
- **API Extraction**: ~2-3 minutes (8,000+ breweries)
- **Bronze Layer**: <30 seconds
- **Silver Layer**: ~1-2 minutes
- **Gold Layer**: ~30 seconds
- **Total Pipeline**: ~5-7 minutes

### Optimization Strategies

1. **Parallel Processing**
```python
# Use Airflow task groups for parallel execution
with TaskGroup("parallel_transformations") as group:
    task_a = PythonOperator(...)
    task_b = PythonOperator(...)
```

2. **Incremental Processing**
- Process only new/changed data
- Use watermark columns for incremental loads
- Implement Change Data Capture (CDC)

3. **Partitioning Strategy**
- Consider adding time-based partitioning
- Balance partition size (not too small/large)
- Use partition pruning in queries

4. **Caching**
- Cache API responses for development
- Use Airflow Variables for configuration
- Implement smart retry logic

## 🌐 Cloud Deployment

### AWS Deployment

**Services**:
- **Airflow**: Amazon MWAA (Managed Workflows for Apache Airflow)
- **Storage**: S3 (bronze/silver/gold layers)
- **Database**: RDS PostgreSQL
- **Monitoring**: CloudWatch

**Setup**:
```bash
# 1. Create S3 buckets
aws s3 mb s3://brewery-data-lake-bronze
aws s3 mb s3://brewery-data-lake-silver
aws s3 mb s3://brewery-data-lake-gold

# 2. Upload DAGs to S3
aws s3 cp dags/ s3://mwaa-environment/dags/ --recursive

# 3. Create MWAA environment
aws mwaa create-environment \
  --name brewery-pipeline \
  --dag-s3-path dags/ \
  --execution-role-arn arn:aws:iam::xxx:role/mwaa-execution-role

# 4. Update paths in DAG
# Change /opt/airflow/data to s3://brewery-data-lake/
```

### GCP Deployment

**Services**:
- **Airflow**: Cloud Composer
- **Storage**: Cloud Storage (GCS)
- **Database**: Cloud SQL
- **Monitoring**: Cloud Monitoring

### Azure Deployment

**Services**:
- **Airflow**: Azure Data Factory + VM
- **Storage**: Azure Data Lake Storage Gen2
- **Database**: Azure Database for PostgreSQL
- **Monitoring**: Azure Monitor

## 📝 Design Choices & Trade-offs

### 1. Medallion Architecture
**Choice**: Bronze → Silver → Gold layered approach
**Rationale**:
- Preserves raw data for audit/reprocessing
- Clear separation of concerns
- Progressive data quality improvement
**Trade-off**: More storage vs. flexibility

### 2. Parquet Format
**Choice**: Parquet for Silver/Gold layers
**Rationale**:
- Columnar storage (efficient analytics)
- Compression (smaller files)
- Schema enforcement
**Trade-off**: Not human-readable vs. performance

### 3. Partitioning Strategy
**Choice**: Partition by country and state
**Rationale**:
- Common query pattern (location-based analysis)
- Balanced partition sizes
- Efficient query pruning
**Trade-off**: More directories vs. query performance

### 4. Local Executor
**Choice**: LocalExecutor for simplicity
**Rationale**:
- Sufficient for daily batch processing
- Easier to debug locally
- Lower infrastructure complexity
**Trade-off**: Not scalable for high concurrency
**Production**: Use CeleryExecutor or KubernetesExecutor

### 5. Synchronous DAG
**Choice**: Linear task dependencies
**Rationale**:
- Data dependencies require sequential processing
- Simpler debugging and monitoring
- Clear data lineage
**Trade-off**: Longer total runtime vs. reliability

## 🔀 Implementation Comparison

### Airflow + Docker vs Databricks + Azure

| Aspect | Airflow + Docker | Databricks + Azure |
|--------|------------------|-------------------|
| **Location** | Root directory | `databricks_azure/` |
| **Orchestration** | Apache Airflow | Databricks Notebooks/Jobs |
| **Processing** | Pandas (single-node) | PySpark (distributed) |
| **Storage** | Local/S3 (Parquet) | Azure Blob (Delta Lake) |
| **Infrastructure** | Self-hosted Docker | Fully managed cloud |
| **Cost** | Infrastructure + maintenance | Pay-per-use (Free tier available) |
| **Scalability** | Limited (vertical) | High (horizontal) |
| **Setup Time** | 5-10 minutes | 20-30 minutes |
| **Best For** | Local dev, on-premise | Cloud-native, big data |
| **Data Volume** | < 100 GB | Any size |
| **Team Skill** | Python, Docker, DevOps | PySpark, Cloud, Data Engineering |

### When to Use Each

**Choose Airflow + Docker if you:**
- ✅ Need on-premise deployment
- ✅ Have existing Docker infrastructure
- ✅ Prefer full infrastructure control
- ✅ Work with smaller datasets (< 100 GB)
- ✅ Want simpler Python (Pandas) code
- ✅ Need to minimize cloud costs

**Choose Databricks + Azure if you:**
- ✅ Want cloud-native solution
- ✅ Need scalability for growing data
- ✅ Prefer managed services (less ops)
- ✅ Want Delta Lake features (ACID, time travel)
- ✅ Plan to integrate with Azure ecosystem
- ✅ Need distributed processing (PySpark)
- ✅ Want to leverage free tier for learning

**Both implementations provide:**
- ✅ Complete medallion architecture
- ✅ Data quality gates
- ✅ Character encoding support
- ✅ Comprehensive logging
- ✅ Production-ready code

### Quick Start Links

- **Airflow Setup**: See [Setup Instructions](#-getting-started) above
- **Databricks Setup**: [`databricks_azure/SETUP_GUIDE.md`](./databricks_azure/SETUP_GUIDE.md)
- **Databricks Docs**: [`databricks_azure/README.md`](./databricks_azure/README.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run full test suite
5. Submit pull request

## 📄 License

MIT License

## 👥 Authors

- **Paulo Victor Orlando** - Initial work

## 🙏 Acknowledgments

- Open Brewery DB for the public API
- Apache Airflow community
- Medallion architecture pattern

---

**For questions or issues, please open a GitHub issue or contact the data engineering team.**

# 🚀 Quick Reference - Brewery Pipeline

## Choose Your Implementation

| If you want... | Use | Location |
|---------------|-----|----------|
| 💻 Local development | **Airflow + Docker** | Root directory |
| ☁️ Cloud deployment | **Databricks + Azure** | `databricks_azure/` |
| 📦 Simple setup | **Airflow + Docker** | 5-10 min setup |
| 📈 Big data ready | **Databricks + Azure** | Scales to TB+ |
| 💰 Zero cost | **Airflow + Docker** | Run locally free |
| 🎓 Learning cloud | **Databricks + Azure** | Free tier available |

## Airflow + Docker - Quick Start

### Setup (5 minutes)
```powershell
# 1. Start services
cd docker
.\start-docker.ps1

# 2. Access Airflow
# Browser: http://localhost:8080
# Login: admin / admin

# 3. Trigger pipeline
# UI: Click 'brewery_pipeline' → Play button
```

### Run Standalone (no Docker)
```powershell
# Setup Python environment
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run pipeline
python run_pipeline_standalone.py
```

### Check Results
```powershell
# Gold layer output
dir data\gold\breweries_by_type_location\
# Example: breweries_by_type_location_20250120_143025.csv
```

### Stop Services
```powershell
cd docker
docker-compose down
```

## Databricks + Azure - Quick Start

### Setup (25 minutes)

**1. Azure Storage (5 min)**
```powershell
# Azure Portal → Storage Accounts → Create
# Name: brewerystorage<unique>
# Performance: Standard
# Redundancy: LRS

# Create containers:
# - brewery-raw
# - brewery-bronze
# - brewery-silver
# - brewery-gold

# Copy Access Key from Portal
```

**2. Databricks (5 min)**
```
# Visit: https://community.cloud.databricks.com/
# Sign up (free)
# Create workspace
```

**3. Configure (5 min)**
```python
# In notebook, set credentials:
storage_account = "brewerystorage<unique>"
storage_key = "YOUR_ACCESS_KEY_HERE"

spark.conf.set(
    f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
    storage_key
)
```

**4. Upload Notebooks (5 min)**
```
# Databricks Workspace → Import
# Upload: databricks_azure/notebooks/brewery_pipeline_main.py
```

**5. Create Cluster (3 min)**
```
# Compute → Create Cluster
# Runtime: 14.3 LTS
# Node: Single Node (Community Edition)
# Auto-terminate: 120 minutes
```

**6. Run Pipeline (2 min)**
```
# Open notebook → Run All
# Wait ~3-5 minutes
# Check execution summary at bottom
```

### Check Results
```python
# In Databricks notebook:

# List Gold files
display(dbutils.fs.ls("abfss://brewery-gold@brewerystorage.dfs.core.windows.net/breweries_by_type_location/"))

# Query Delta table
df = spark.read.format("delta").load("abfss://brewery-gold@brewerystorage.dfs.core.windows.net/breweries_by_type_location/")
display(df.limit(10))

# Download CSV
dbutils.fs.ls("abfss://brewery-gold@brewerystorage.dfs.core.windows.net/breweries_by_type_location/")
# Copy CSV URL → Download from Azure Portal
```

## Common Commands

### Airflow + Docker

**Check logs:**
```powershell
# DAG logs
docker-compose logs airflow-webserver

# Task logs
# UI: Click task → View Log
```

**Restart services:**
```powershell
docker-compose restart
```

**Clean data:**
```powershell
Remove-Item -Recurse -Force data\*
```

**Run tests:**
```powershell
pytest tests/ -v
```

**Check coverage:**
```powershell
pytest tests/ --cov=src --cov-report=html
```

### Databricks + Azure

**List files:**
```python
# List container contents
display(dbutils.fs.ls("abfss://brewery-bronze@<account>.dfs.core.windows.net/"))
```

**Query data:**
```python
# Read Delta table
df = spark.read.format("delta").load("<abfss-path>")
display(df)
```

**Check cluster:**
```python
# Get cluster info
spark.sparkContext.getConf().getAll()
```

**Clean data:**
```python
# Remove directory
dbutils.fs.rm("abfss://brewery-silver@<account>.dfs.core.windows.net/breweries/", recurse=True)
```

**Download files:**
```
# Option 1: Azure Portal → Storage Account → Containers → Download
# Option 2: Azure Storage Explorer (free tool)
# Option 3: Azure CLI
az storage blob download --account-name <name> --container-name brewery-gold --name <file> --file local.csv
```

## Data Flow

Both implementations follow the same pattern:

```
API (9,000 breweries)
    ↓
BRONZE (~5-6 MB JSON)
    ↓
SILVER (~2-3 MB Parquet/Delta)
    ↓
GOLD (~1-2 MB aggregations)
```

## Key Differences

| Aspect | Airflow + Docker | Databricks + Azure |
|--------|------------------|-------------------|
| **Format** | Parquet | Delta Lake |
| **Processing** | Pandas | PySpark |
| **Storage** | Local/S3 | Azure Blob |
| **Location** | `data/` folder | Azure containers |
| **Query** | Python scripts | PySpark/SQL |

## File Naming

### Airflow + Docker
```
data/gold/breweries_by_type_location/
  └─ breweries_by_type_location_20250120_143025.csv
  └─ summary_statistics_20250120_143025.json
```

### Databricks + Azure
```
brewery-gold/
  └─ breweries_by_type_location/
      └─ part-00000-xxx.snappy.parquet  (Delta format)
      └─ _delta_log/
      └─ breweries_by_type_location_20250120.csv
```

## Troubleshooting

### Airflow + Docker

**Docker not starting:**
```powershell
# Check Docker Desktop is running
docker ps

# Rebuild containers
docker-compose down
docker-compose up --build
```

**DAG not visible:**
```
# Check DAG file syntax
python dags/brewery_pipeline.py

# Refresh UI (wait 30 seconds)
```

**Task failed:**
```
# View logs in Airflow UI
# Check logs.txt in brewery_case folder
# Run standalone to debug:
python run_pipeline_standalone.py
```

### Databricks + Azure

**Authentication error:**
```python
# Verify storage key is correct
# Check account name matches
# Ensure no extra spaces in config
```

**Cluster timeout:**
```
# Increase timeout: Cluster → Edit → Auto-termination
# Or restart cluster manually
```

**Import error:**
```python
# Install missing package
%pip install <package>

# Restart Python kernel
dbutils.library.restartPython()
```

**File not found:**
```python
# Check container exists
display(dbutils.fs.ls("abfss://brewery-raw@<account>.dfs.core.windows.net/"))

# Verify path format (no typos)
```

## Cost Summary

### Airflow + Docker
- **Local**: FREE
- **Cloud VM**: $10-100/month
- **Storage**: < $1/month

### Databricks + Azure
- **Free Tier**: FREE (first year)
- **After free tier**: ~$2/month (light use)
- **Production**: ~$200-500/month

## Documentation Links

### Airflow + Docker
- 📖 [Main README](../README.md)
- 🏗️ [Architecture](../MEDALLION_GUIDE.md)
- 🚀 [CI/CD Setup](../CI_CD_GUIDE.md)
- 📊 [Monitoring](../MONITORING.md)

### Databricks + Azure
- 📖 [README](../databricks_azure/README.md)
- ⚡ [Setup Guide](../databricks_azure/SETUP_GUIDE.md)
- 📦 [Requirements](../databricks_azure/REQUIREMENTS.md)

### Comparison
- 🔀 [Implementation Guide](../IMPLEMENTATION_GUIDE.md)

## Quick Wins

### Test the Pipeline
**Airflow:**
```powershell
# ~30 seconds
python run_pipeline_standalone.py
```

**Databricks:**
```python
# ~3 minutes (first run)
# Run All cells in notebook
```

### Query Results
**Airflow:**
```python
import pandas as pd
df = pd.read_csv("data/gold/breweries_by_type_location/breweries_by_type_location_20250120_143025.csv")
print(df.head())
```

**Databricks:**
```python
df = spark.read.format("delta").load("abfss://brewery-gold@<account>.dfs.core.windows.net/breweries_by_type_location/")
display(df.limit(5))
```

### Stop Everything
**Airflow:**
```powershell
docker-compose down
```

**Databricks:**
```
# Cluster auto-terminates after 120 minutes
# Or manually: Compute → Terminate
```

## Next Steps

1. **Choose implementation** based on your needs
2. **Follow setup guide** for your choice
3. **Run pipeline** and verify results
4. **Query data** to explore breweries
5. **Customize** for your specific requirements

---

**Need help?** Check the detailed guides linked above! 🚀

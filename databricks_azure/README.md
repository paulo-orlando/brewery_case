# Brewery Data Pipeline - Databricks + Azure Blob Storage

A production-ready data pipeline implementation for **Databricks Community Edition** and **Azure Blob Storage**. This implementation mirrors the Airflow/Docker solution but uses Databricks notebooks and PySpark for distributed processing.

---

## 🏗️ Architecture

### Cloud-Native Medallion Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Open Brewery DB API                 │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│              AZURE BLOB STORAGE (RAW)                │
│              Raw JSON from API extraction            │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│           AZURE BLOB STORAGE (BRONZE)                │
│           JSON with ingestion metadata               │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│           AZURE BLOB STORAGE (SILVER)                │
│        Delta Lake Format (Partitioned)               │
│        Cleaned, validated, enriched data             │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼ (Quality Gate)
┌─────────────────────────────────────────────────────┐
│            AZURE BLOB STORAGE (GOLD)                 │
│     Delta Lake + CSV Analytical Aggregations         │
│         Ready for BI tools and visualization         │
└─────────────────────────────────────────────────────┘
```

---

## 🌟 Key Features

✅ **Databricks Community Edition Compatible**: Works with free tier
✅ **Azure Blob Storage Integration**: ABFS protocol support
✅ **Delta Lake Format**: ACID transactions, time travel, schema evolution
✅ **PySpark Distributed Processing**: Scalable for large datasets
✅ **Quality Gate Pattern**: Pipeline halts on data quality failures
✅ **Character Encoding Support**: Handles international characters (ä, ö, ü, ñ, é)
✅ **Partitioned Storage**: Optimized by country/state for query performance
✅ **Timestamped Outputs**: Unique file identification
✅ **Notebook-Based**: Easy to run and monitor in Databricks
✅ **Secrets Management**: Databricks Secrets for secure credentials

---

## 📁 Project Structure

```
databricks_azure/
├── notebooks/
│   └── brewery_pipeline_main.py       # Main orchestration notebook
├── src/
│   ├── api/
│   │   └── brewery_api_azure.py       # API extraction (PySpark)
│   ├── bronze/
│   │   └── bronze_layer_azure.py      # Bronze layer (PySpark)
│   ├── silver/
│   │   └── silver_layer_azure.py      # Silver layer (Delta Lake)
│   ├── gold/
│   │   └── gold_layer_azure.py        # Gold aggregations (Delta Lake)
│   └── common/
│       └── data_quality_azure.py      # Data quality checks
├── config/
│   └── azure_config.py                # Azure configuration
└── README.md                          # This file
```

---

## 🚀 Quick Start

### Prerequisites

1. **Databricks Account**
   - Free Community Edition: https://databricks.com/try-databricks
   - OR Azure Databricks workspace

2. **Azure Storage Account**
   - Free tier: https://azure.microsoft.com/free/
   - Create 4 containers: `brewery-raw`, `brewery-bronze`, `brewery-silver`, `brewery-gold`

3. **GitHub/Git Access**
   - For importing code to Databricks

---

### Step 1: Create Azure Storage Account

```bash
# Azure CLI (optional - you can also use Azure Portal)
az storage account create \
    --name <your-storage-account-name> \
    --resource-group <your-resource-group> \
    --location eastus \
    --sku Standard_LRS

# Create containers
for container in brewery-raw brewery-bronze brewery-silver brewery-gold
do
    az storage container create \
        --name $container \
        --account-name <your-storage-account-name>
done
```

**Or use Azure Portal**:
1. Go to portal.azure.com
2. Create Storage Account
3. Create 4 containers as listed above

---

### Step 2: Set Up Databricks Secrets

```python
# In Databricks notebook or CLI
databricks secrets create-scope --scope azure-scope

# Add storage account key
databricks secrets put --scope azure-scope --key storage-key
# (Enter your Azure Storage Account key when prompted)
```

**Get your storage key**:
- Azure Portal → Storage Account → Access Keys → Copy key1

---

### Step 3: Configure Azure Settings

Edit `config/azure_config.py`:

```python
# Replace with your Azure Storage Account name
AZURE_STORAGE_ACCOUNT = "your_storage_account_name"  # ← CHANGE THIS

# Containers (keep as-is if you used the names above)
AZURE_CONTAINER_BRONZE = "brewery-bronze"
AZURE_CONTAINER_SILVER = "brewery-silver"
AZURE_CONTAINER_GOLD = "brewery-gold"
AZURE_CONTAINER_RAW = "brewery-raw"
```

---

### Step 4: Import to Databricks

**Option A: Import from GitHub** (Recommended)

1. In Databricks, go to **Repos**
2. Click **Add Repo**
3. Enter repository URL: `https://github.com/paulo-orlando/brewery_case`
4. Navigate to `databricks_azure/` folder

**Option B: Upload Files**

1. Upload all files from `databricks_azure/` folder
2. Maintain the directory structure

---

### Step 5: Run the Pipeline

1. Open `notebooks/brewery_pipeline_main.py`
2. Attach to a cluster (or create new one)
   - **Cluster specs for Community Edition**:
     - Runtime: 13.3 LTS or later
     - Node type: Any available (single node is fine)
3. **Run All Cells** or use **Run All** button
4. Monitor progress in real-time

**Expected Duration**: 2-5 minutes for complete pipeline

---

## 📊 Pipeline Stages

### Stage 1: Extract (API)
- Fetches ~8,923 breweries from Open Brewery DB API
- Pagination with retry logic
- Saves to Azure Blob Storage (Raw layer)

### Stage 2: Bronze Layer
- Preserves raw JSON with metadata
- Adds ingestion timestamps
- Immutable source of truth

### Stage 3: Silver Layer
- Transforms JSON → Delta Lake format
- Removes duplicates
- Fixes character encoding
- Partitions by country/state
- Adds derived columns

### Stage 4: Quality Gate ⚠️
- Validates data quality
- **Pipeline halts if checks fail**
- Ensures only clean data reaches Gold

### Stage 5: Gold Layer
- Creates analytical aggregations
- Breweries by type and location
- Saves as Delta Lake + CSV
- Summary statistics

### Stage 6: Summary
- Displays execution metrics
- Returns status for scheduling

---

## 🔍 Querying Data

### Read Delta Tables

```python
# Silver layer
silver_df = spark.read.format("delta").load("/mnt/brewery-silver/breweries")
display(silver_df)

# Gold layer
gold_df = spark.read.format("delta").load("/mnt/brewery-gold/breweries_by_type_location")
display(gold_df)

# Query examples
# Top 10 states by brewery count
gold_df.orderBy(col("brewery_count").desc()).limit(10).display()

# Breweries in a specific country
silver_df.filter(col("country") == "United States").display()

# Average coordinates by state
gold_df.select("state", "avg_latitude", "avg_longitude").display()
```

---

## 📈 Delta Lake Features

### Time Travel

```python
# View historical versions
spark.read.format("delta").option("versionAsOf", 0).load(path)

# View as of timestamp
spark.read.format("delta").option("timestampAsOf", "2025-10-20").load(path)

# View history
spark.sql("DESCRIBE HISTORY delta.`/mnt/brewery-silver/breweries`")
```

### Schema Evolution

```python
# Delta Lake automatically handles schema changes
df.write.format("delta").mode("append").option("mergeSchema", "true").save(path)
```

---

## ⚙️ Configuration Options

### Using Mount Points vs ABFS

**Option 1: Mount (Recommended for ease of use)**
```python
# Mounted paths (simpler)
path = "/mnt/brewery-silver/breweries"
```

**Option 2: ABFS Direct (No mounting needed)**
```python
# Direct ABFS paths
path = "abfss://brewery-silver@youraccount.dfs.core.windows.net/breweries"
```

The notebook supports both! Just configure in `azure_config.py`.

---

## 🔒 Security Best Practices

### Databricks Secrets

```python
# Store secrets securely
storage_key = dbutils.secrets.get(scope="azure-scope", key="storage-key")

# Never hardcode credentials!
# ❌ BAD:  storage_key = "my-secret-key-123"
# ✅ GOOD: storage_key = dbutils.secrets.get(...)
```

### Azure Access

- Use **Managed Identity** (recommended for production)
- Use **Service Principal** for automated workflows
- Use **Storage Account Keys** for development only

---

## 📊 Monitoring & Logging

### Notebook Monitoring

- Databricks automatically tracks:
  - Cell execution time
  - Memory usage
  - Spark UI for job details

### Custom Logging

```python
# Logs appear in notebook output and cluster logs
logger.info("Processing 1000 records")
logger.warning("Duplicate rate: 5.2%")
logger.error("Quality check failed")
```

---

## 🔄 Scheduling

### Databricks Jobs

1. Go to **Jobs** → **Create Job**
2. Configure:
   - **Notebook**: `notebooks/brewery_pipeline_main.py`
   - **Cluster**: Use existing or create new
   - **Schedule**: Daily, hourly, or cron expression
3. **Save and Run**

**Example Schedule**:
- Daily at 2 AM: `0 2 * * *`
- Every 6 hours: `0 */6 * * *`

---

## 🐛 Troubleshooting

### Issue: "Mount point already exists"

```python
# Unmount first
dbutils.fs.unmount("/mnt/brewery-raw")
# Then re-mount
```

### Issue: "Access denied to Azure Blob Storage"

```python
# Check credentials
dbutils.secrets.get(scope="azure-scope", key="storage-key")

# Verify storage account name in config
print(config.AZURE_STORAGE_ACCOUNT)
```

### Issue: "Module import failed"

```python
# Check sys.path
import sys
print(sys.path)

# Add path manually if needed
sys.path.append("/Workspace/Repos/brewery_case/databricks_azure/src")
```

### Issue: "Delta table not found"

```python
# Check if path exists
dbutils.fs.ls("/mnt/brewery-silver/")

# Verify Delta table
spark.read.format("delta").load("/mnt/brewery-silver/breweries").count()
```

---

## 💰 Cost Considerations

### Databricks Community Edition
- **FREE** for learning and development
- Limitations:
  - Single node cluster
  - 15 GB RAM
  - Cluster auto-terminates after 2 hours
  - No advanced features (Jobs, RBAC, etc.)

### Azure Blob Storage
- **FREE** tier: First 5 GB
- **Cost**: ~$0.02 per GB/month (Standard LRS)
- **Estimate for this project**: < $1/month

### Azure Databricks (Production)
- **Costs vary** by region and instance type
- **Estimate**: $1-5/hour for small workloads
- **Tip**: Use spot instances to save 50-80%

---

## 📚 Comparison: Databricks vs Airflow

| Feature | Airflow/Docker | Databricks/Azure |
|---------|----------------|------------------|
| **Infrastructure** | Self-managed | Fully managed |
| **Scaling** | Manual | Auto-scaling |
| **Cost** | Fixed (VM/server) | Pay-per-use |
| **Setup** | Complex | Simple |
| **Processing** | Pandas (single-node) | PySpark (distributed) |
| **Storage** | Local/S3 | Azure Blob Storage |
| **Format** | Parquet | Delta Lake |
| **Scheduling** | Built-in | Jobs API |
| **Best For** | On-prem, custom infra | Cloud-native, big data |

---

## 🎓 Learning Resources

### Databricks
- [Community Edition Signup](https://databricks.com/try-databricks)
- [Databricks Academy (Free)](https://academy.databricks.com/)
- [Delta Lake Documentation](https://docs.delta.io/)

### Azure
- [Azure Free Account](https://azure.microsoft.com/free/)
- [Azure Blob Storage Docs](https://docs.microsoft.com/azure/storage/blobs/)
- [ABFS Protocol Guide](https://docs.microsoft.com/azure/databricks/data/data-sources/azure/azure-datalake-gen2)

---

## 🤝 Contributing

Both implementations (Airflow and Databricks) are maintained in parallel:
- **Airflow/Docker**: `brewery_case/` (root)
- **Databricks/Azure**: `brewery_case/databricks_azure/`

Feature parity is maintained between both solutions.

---

## 📄 License

MIT License

---

## 👥 Authors

- **Paulo Orlando** - Data Engineering Team

---

## 🙏 Acknowledgments

- Open Brewery DB for the public API
- Databricks Community Edition
- Azure Blob Storage Free Tier
- Delta Lake open-source project

---

**Questions? Open an issue on GitHub!** 🚀

---

## 🔗 Related Documentation

- [Main README](../../README.md) - Airflow/Docker implementation
- [QUICKSTART](../../QUICKSTART.md) - Quick start guide (Airflow)
- [SOLUTION_SUMMARY](../../SOLUTION_SUMMARY.md) - Complete solution overview

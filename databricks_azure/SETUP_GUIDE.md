# Databricks Azure - Quick Setup Guide

## 🎯 30-Minute Setup for Free Tier

This guide helps you set up the complete pipeline using **Databricks Community Edition** (free) and **Azure Free Tier**.

---

## Step 1: Create Azure Storage Account (10 minutes)

### Option A: Azure Portal (Easiest)

1. Go to [portal.azure.com](https://portal.azure.com)
2. Click **+ Create a resource** → Search "Storage account"
3. Click **Create**
4. Fill in:
   - **Resource group**: Create new (e.g., "brewery-pipeline-rg")
   - **Storage account name**: Choose unique name (e.g., "brewerydata2025")
   - **Region**: Choose nearest (e.g., "East US")
   - **Performance**: Standard
   - **Redundancy**: LRS (locally redundant - cheapest)
5. Click **Review + Create** → **Create**
6. Wait ~2 minutes for deployment

### Create Containers

1. Go to your storage account → **Containers**
2. Click **+ Container** for each:
   - `brewery-raw`
   - `brewery-bronze`
   - `brewery-silver`
   - `brewery-gold`
3. Keep "Private" access level

### Get Access Key

1. In storage account, go to **Security + networking** → **Access keys**
2. Click **Show** next to key1
3. Copy the **Key** value (save for later)

---

## Step 2: Sign Up for Databricks Community Edition (5 minutes)

1. Go to [databricks.com/try-databricks](https://databricks.com/try-databricks)
2. Select **Community Edition** (FREE)
3. Fill in signup form
4. Verify email
5. Log in to your workspace

---

## Step 3: Create Databricks Cluster (5 minutes)

1. In Databricks, click **Compute** (left sidebar)
2. Click **Create Cluster**
3. Configure:
   - **Cluster name**: "brewery-pipeline"
   - **Cluster mode**: Single Node
   - **Databricks runtime**: 13.3 LTS or later
   - **Node type**: Any available (default is fine for Community)
4. Click **Create Cluster**
5. Wait ~3-5 minutes for cluster to start

---

## Step 4: Set Up Databricks Secrets (5 minutes)

### Install Databricks CLI (Optional - or use Notebook)

```bash
# If you want to use CLI
pip install databricks-cli

# Configure
databricks configure --token
# Enter your Databricks workspace URL and personal access token
```

### Create Secret Scope

**Option A: Using Databricks CLI**
```bash
databricks secrets create-scope --scope azure-scope
databricks secrets put --scope azure-scope --key storage-key
# Paste your Azure storage key when prompted
```

**Option B: Using Notebook** (Easier for Community Edition)
```python
# Run this in a Databricks notebook
dbutils.secrets.help()  # Check available commands

# Note: Secret scopes require Azure Databricks (not Community Edition)
# For Community Edition, you'll need to use the config file approach
```

### Alternative for Community Edition

Since Community Edition doesn't support secret scopes, we'll use an alternative:

1. Create a notebook called `setup_credentials`
2. Add this code (replace with your values):

```python
# TEMPORARY SETUP - FOR DEVELOPMENT ONLY
# In production, use Databricks Secrets

# Your Azure Storage Account details
AZURE_STORAGE_ACCOUNT = "brewerydata2025"  # Replace with yours
AZURE_STORAGE_KEY = "your-storage-key-here"  # Replace with your key

# Configure Spark
spark.conf.set(
    f"fs.azure.account.key.{AZURE_STORAGE_ACCOUNT}.dfs.core.windows.net",
    AZURE_STORAGE_KEY
)

print("✅ Azure credentials configured")
```

3. Run this notebook BEFORE running the pipeline
4. Keep this notebook private!

---

## Step 5: Import Code to Databricks (5 minutes)

### Option A: Import from GitHub

1. In Databricks, go to **Repos** (left sidebar)
2. Click **Add Repo**
3. Enter:
   - **Git repository URL**: `https://github.com/paulo-orlando/brewery_case`
   - **Git provider**: GitHub
4. Click **Create Repo**
5. Navigate to `databricks_azure/` folder in the imported repo

### Option B: Manual Upload

1. Download all files from `databricks_azure/` folder
2. In Databricks, go to **Workspace** → Your home folder
3. Click **⋮** → **Import**
4. Upload each Python file
5. Maintain folder structure:
   ```
   /Users/your-email/
   ├── notebooks/
   │   └── brewery_pipeline_main.py
   ├── src/
   │   ├── api/
   │   ├── bronze/
   │   ├── silver/
   │   ├── gold/
   │   └── common/
   └── config/
       └── azure_config.py
   ```

---

## Step 6: Configure Settings (2 minutes)

1. Open `config/azure_config.py`
2. Update:

```python
# CHANGE THIS to your storage account name
AZURE_STORAGE_ACCOUNT = "brewerydata2025"  # ← Your account name here

# Keep these as-is (unless you used different container names)
AZURE_CONTAINER_BRONZE = "brewery-bronze"
AZURE_CONTAINER_SILVER = "brewery-silver"
AZURE_CONTAINER_GOLD = "brewery-gold"
AZURE_CONTAINER_RAW = "brewery-raw"
```

---

## Step 7: Run the Pipeline! (3 minutes)

1. Open `notebooks/brewery_pipeline_main.py`
2. Attach to your cluster (top-right dropdown)
3. **If using Community Edition**, first run your `setup_credentials` notebook
4. Click **Run All** button
5. Watch the magic happen! ✨

Expected output:
```
🎉 PIPELINE EXECUTED SUCCESSFULLY!
⏰ Start: 2025-10-20 10:00:00
⏰ End: 2025-10-20 10:03:25
⏱️  Total duration: 205.50 seconds (3.43 minutes)

📊 EXECUTION SUMMARY:
   1️⃣  EXTRACT:  8,923 records extracted
   2️⃣  BRONZE:   8,923 records saved
   3️⃣  SILVER:   8,923 records cleaned
   4️⃣  QUALITY:  100.0% quality (Status: PASSED)
   5️⃣  GOLD:     26,000 rows aggregated
```

---

## Verification Steps

### 1. Check Azure Blob Storage

Go to Azure Portal → Your storage account → Containers:
- `brewery-raw`: Should have JSON files
- `brewery-bronze`: Should have JSON files
- `brewery-silver`: Should have Delta Lake folders (`_delta_log/`, parquet files)
- `brewery-gold`: Should have Delta Lake + CSV files

### 2. Query Data in Databricks

```python
# In a new notebook
# Read Silver data
silver_df = spark.read.format("delta").load("abfss://brewery-silver@brewerydata2025.dfs.core.windows.net/breweries")
display(silver_df.limit(10))

# Read Gold data
gold_df = spark.read.format("delta").load("abfss://brewery-gold@brewerydata2025.dfs.core.windows.net/breweries_by_type_location")
display(gold_df.limit(10))
```

### 3. View in Azure Storage Explorer (Optional)

1. Download [Azure Storage Explorer](https://azure.microsoft.com/features/storage-explorer/)
2. Connect to your storage account
3. Browse containers and files

---

## Troubleshooting

### Error: "No module named 'api'"

**Fix**: Check that `sys.path` is set correctly in the notebook:

```python
import sys
sys.path.append("/Workspace/Repos/brewery_case/databricks_azure/src")
sys.path.append("/Workspace/Repos/brewery_case/databricks_azure/config")
```

### Error: "Access Denied" to Azure

**Fix**: Verify your storage key and account name are correct:

```python
# Test connection
dbutils.fs.ls(f"abfss://brewery-raw@{AZURE_STORAGE_ACCOUNT}.dfs.core.windows.net/")
```

### Error: "Cluster terminated"

**Fix**: Community Edition clusters auto-terminate after 2 hours of inactivity. Just restart it:
1. Go to **Compute** → Your cluster
2. Click **Start**

### Error: "Delta table not found"

**Fix**: Run the pipeline first to create the tables. The error occurs if you try to query before creating data.

---

## Next Steps

1. **Schedule the pipeline**: Set up Databricks Jobs (requires paid tier)
2. **Create visualizations**: Use Databricks SQL dashboards
3. **Optimize queries**: Add indexes, optimize file sizes
4. **Production deployment**: Move to Azure Databricks with proper secrets management

---

## Cost Tracking

### Free Tier Limits

**Databricks Community Edition**:
- ✅ Completely FREE forever
- ❌ Limited to 15 GB RAM, single node
- ❌ No Jobs scheduling
- ❌ No RBAC/secrets

**Azure Free Tier** (12 months):
- ✅ 5 GB Blob Storage free
- ✅ 250 GB bandwidth free
- ❌ After 12 months: ~$0.02/GB/month

**This Project**:
- Estimated storage: ~500 MB
- Monthly cost after free tier: < $1

---

## Production Upgrade Path

When ready for production:

1. **Upgrade to Azure Databricks** (~$3-10/hour)
2. **Use Databricks Secrets** for credentials
3. **Enable Jobs** for scheduling
4. **Add monitoring** with Azure Monitor
5. **Implement CI/CD** with Azure DevOps

---

## Questions?

- **GitHub Issues**: [github.com/paulo-orlando/brewery_case/issues](https://github.com/paulo-orlando/brewery_case/issues)
- **Databricks Community**: [community.databricks.com](https://community.databricks.com)
- **Azure Forums**: [docs.microsoft.com/answers](https://docs.microsoft.com/answers)

---

**Enjoy your cloud-native data pipeline! 🚀☁️**

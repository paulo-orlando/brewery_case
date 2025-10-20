# Databricks Azure - Requirements

## Databricks Runtime Requirements

This solution is designed for **Databricks Runtime 13.3 LTS or later**.

### Pre-installed in Databricks Runtime:
- pyspark==3.4.x
- delta-spark==2.4.x
- pandas==2.0.x
- numpy==1.24.x
- pyarrow==12.x

### Additional Libraries (auto-installed in notebook)

```python
# Install in notebook if needed
%pip install requests==2.31.0
%pip install tenacity==8.2.3
```

## Local Development (Optional)

If you want to test modules locally (not required for Databricks):

```bash
pip install pyspark==3.4.1
pip install delta-spark==2.4.0
pip install pandas==2.0.3
pip install requests==2.31.0
pip install tenacity==8.2.3
pip install pyarrow==12.0.1
```

**Note**: Local PySpark development is complex. We recommend developing directly in Databricks notebooks.

## Azure Requirements

### Azure Services:
- **Azure Storage Account** (Standard_LRS)
  - 4 containers: `brewery-raw`, `brewery-bronze`, `brewery-silver`, `brewery-gold`
  - Storage Account Key for authentication

### Databricks:
- **Community Edition** (FREE) - For learning/development
  - OR
- **Azure Databricks** (Paid) - For production
  - Standard or Premium tier for advanced features

## Compute Requirements

### Databricks Community Edition:
- **Cluster Type**: Single Node
- **Runtime**: 13.3 LTS or later (recommended: 14.3 LTS)
- **RAM**: 15 GB (fixed for Community)
- **Cores**: 2 cores (fixed for Community)
- **Auto-terminate**: 120 minutes

### Azure Databricks (Production):
- **Cluster Type**: Standard or High Concurrency
- **Runtime**: 13.3 LTS or later
- **Workers**: 2-8 (auto-scaling recommended)
- **Driver**: Standard_DS3_v2 or better
- **Workers**: Standard_DS3_v2 or better

## Storage Requirements

### For ~9,000 breweries:

| Layer | Format | Size (Approx) | Partitioning |
|-------|--------|---------------|--------------|
| Raw | JSON | ~5 MB | By date |
| Bronze | JSON | ~6 MB | By date |
| Silver | Delta Lake | ~8 MB | By country/state |
| Gold | Delta Lake + CSV | ~3 MB | None |
| **Total** | | **~22 MB** | |

### Growth Projection:

- **Daily runs**: ~25 MB/day (with duplicates)
- **Monthly**: ~750 MB (without cleanup)
- **Recommended**: Keep last 30 days = ~750 MB
- **With cleanup**: Stable at ~100-200 MB

## Network Requirements

### Outbound Access:
- **Open Brewery DB API**: `api.openbrewerydb.org` (HTTPS)
- **Azure Blob Storage**: `*.blob.core.windows.net` (HTTPS)
- **PyPI** (for package installation): `pypi.org` (HTTPS)

### Ports:
- **HTTPS**: 443 (outbound)
- All networking is managed by Databricks

## Authentication

### Supported Methods:

1. **Storage Account Key** (Development)
   ```python
   spark.conf.set(
       f"fs.azure.account.key.{account}.dfs.core.windows.net",
       storage_key
   )
   ```

2. **Databricks Secrets** (Recommended)
   ```python
   storage_key = dbutils.secrets.get(scope="azure-scope", key="storage-key")
   ```

3. **Managed Identity** (Production - Azure Databricks only)
   ```python
   spark.conf.set(
       f"fs.azure.account.auth.type.{account}.dfs.core.windows.net",
       "OAuth"
   )
   ```

4. **Service Principal** (CI/CD)
   ```python
   spark.conf.set(
       f"fs.azure.account.auth.type.{account}.dfs.core.windows.net",
       "OAuth"
   )
   spark.conf.set(
       f"fs.azure.account.oauth.provider.type.{account}.dfs.core.windows.net",
       "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider"
   )
   ```

## Development Tools (Optional)

### For local code editing:
- VS Code
- PyCharm
- Databricks extension for VS Code

### For testing:
- pytest (not required in Databricks)
- Azure Storage Explorer (for browsing data)

## Version Compatibility Matrix

| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| Databricks Runtime | 13.0 | 14.3 LTS | Latest stable |
| Python | 3.10 | 3.11 | Included in runtime |
| PySpark | 3.4 | 3.5 | Included in runtime |
| Delta Lake | 2.3 | 2.4 | Included in runtime |
| Azure Storage Account | V2 | V2 | Standard_LRS |

## Feature Requirements by Edition

| Feature | Community | Standard | Premium |
|---------|-----------|----------|---------|
| **Core Pipeline** | ✅ | ✅ | ✅ |
| **Delta Lake** | ✅ | ✅ | ✅ |
| **Jobs Scheduling** | ❌ | ✅ | ✅ |
| **Secrets Management** | ❌ | ✅ | ✅ |
| **RBAC** | ❌ | ✅ | ✅ |
| **Audit Logs** | ❌ | ❌ | ✅ |
| **Auto-scaling** | ❌ | ✅ | ✅ |

## Minimum Setup (Free Tier)

**Total Cost: $0/month**

- Databricks Community Edition (FREE)
- Azure Free Tier (First 12 months, 5 GB storage FREE)
- Total storage needed: ~500 MB

**After Free Tier**:
- Azure Blob Storage: ~$0.01/month (500 MB)

## Production Setup

**Estimated Monthly Cost: $200-500**

- Azure Databricks Standard: ~$100-300/month
- Azure Blob Storage: ~$1-5/month
- Compute (auto-scaling): ~$100-200/month
- Total: ~$200-500/month

## Next Steps

1. **Setup**: Follow [SETUP_GUIDE.md](./SETUP_GUIDE.md)
2. **Run**: Execute the main notebook
3. **Query**: Use Databricks SQL or notebooks
4. **Schedule**: Set up Jobs (requires paid tier)

---

**Ready to get started?** Go to [SETUP_GUIDE.md](./SETUP_GUIDE.md)!

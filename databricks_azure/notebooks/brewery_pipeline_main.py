# Databricks notebook source
# MAGIC %md
# MAGIC # Brewery Data Pipeline - Medallion Architecture
# MAGIC ## Databricks + Azure Blob Storage Implementation
# MAGIC 
# MAGIC This notebook orchestrates the complete data pipeline:
# MAGIC - **Extract**: Fetch data from Open Brewery DB API
# MAGIC - **Bronze**: Save raw data to Azure Blob Storage
# MAGIC - **Silver**: Transform and cleanse data (Delta Lake format)
# MAGIC - **Quality Gate**: Validate data quality before Gold layer
# MAGIC - **Gold**: Create analytical aggregations
# MAGIC 
# MAGIC **Duration**: ~2-5 minutes for complete pipeline

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup and Configuration

# COMMAND ----------

# Import required libraries
import sys
from datetime import datetime

# Add src to path
sys.path.append("/Workspace/Repos/brewery_case/databricks_azure/src")
sys.path.append("/Workspace/Repos/brewery_case/databricks_azure/config")

# Import pipeline modules
from api.brewery_api_azure import extract_to_azure_notebook
from bronze.bronze_layer_azure import bronze_layer_notebook
from silver.silver_layer_azure import silver_layer_notebook
from gold.gold_layer_azure import gold_layer_notebook
from common.data_quality_azure import quality_check_notebook

# Import configuration
import azure_config as config

# COMMAND ----------

# MAGIC %md
# MAGIC ## Mount Azure Blob Storage (One-time setup)
# MAGIC 
# MAGIC **Note**: Replace with your Azure Storage Account credentials

# COMMAND ----------

# MAGIC %python
# MAGIC # Mount configuration
# MAGIC storage_account_name = config.AZURE_STORAGE_ACCOUNT
# MAGIC storage_account_key = dbutils.secrets.get(scope="azure-scope", key="storage-key")  # Store key in Databricks Secrets
# MAGIC 
# MAGIC # Mount points
# MAGIC mounts = [
# MAGIC     (config.AZURE_CONTAINER_RAW, config.DATABRICKS_MOUNT_POINT_RAW),
# MAGIC     (config.AZURE_CONTAINER_BRONZE, config.DATABRICKS_MOUNT_POINT_BRONZE),
# MAGIC     (config.AZURE_CONTAINER_SILVER, config.DATABRICKS_MOUNT_POINT_SILVER),
# MAGIC     (config.AZURE_CONTAINER_GOLD, config.DATABRICKS_MOUNT_POINT_GOLD)
# MAGIC ]
# MAGIC 
# MAGIC # Mount each container
# MAGIC for container, mount_point in mounts:
# MAGIC     # Check if already mounted
# MAGIC     if not any(mount.mountPoint == mount_point for mount in dbutils.fs.mounts()):
# MAGIC         try:
# MAGIC             dbutils.fs.mount(
# MAGIC                 source=f"wasbs://{container}@{storage_account_name}.blob.core.windows.net",
# MAGIC                 mount_point=mount_point,
# MAGIC                 extra_configs={f"fs.azure.account.key.{storage_account_name}.blob.core.windows.net": storage_account_key}
# MAGIC             )
# MAGIC             print(f"✅ Mounted {container} to {mount_point}")
# MAGIC         except Exception as e:
# MAGIC             print(f"❌ Error mounting {container}: {e}")
# MAGIC     else:
# MAGIC         print(f"ℹ️  {mount_point} already mounted")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Alternative: Use ABFS (Without Mounting)
# MAGIC 
# MAGIC If you prefer not to mount, you can use ABFS paths directly

# COMMAND ----------

# Set up Spark configuration for Azure Blob Storage access
spark.conf.set(
    f"fs.azure.account.key.{config.AZURE_STORAGE_ACCOUNT}.dfs.core.windows.net",
    dbutils.secrets.get(scope="azure-scope", key="storage-key")
)

print("✅ Azure Blob Storage configured")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Pipeline Execution

# COMMAND ----------

# MAGIC %md
# MAGIC ### Stage 1/6: Extract - Fetch Data from API

# COMMAND ----------

print("=" * 100)
print("📡 STAGE 1/6 - EXTRACT: Fetch data from API")
print("=" * 100)

start_time = datetime.now()

try:
    extract_result = extract_to_azure_notebook(spark, config)
    
    print(f"✅ Extraction complete!")
    print(f"   • Total breweries: {extract_result['records_extracted']}")
    print(f"   • File saved: {extract_result['output_file']}")
    print(f"   • Timestamp: {extract_result['timestamp']}")
    
except Exception as e:
    print(f"❌ Extraction failed: {e}")
    dbutils.notebook.exit("EXTRACTION_FAILED")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Stage 2/6: Bronze - Save Raw Data

# COMMAND ----------

print("=" * 100)
print("🥉 STAGE 2/6 - BRONZE: Save raw data")
print("=" * 100)

try:
    bronze_result = bronze_layer_notebook(spark, config)
    
    print(f"✅ Bronze layer complete!")
    print(f"   • Total records: {bronze_result['total_records']}")
    print(f"   • Output path: {bronze_result['output_path']}")
    
except Exception as e:
    print(f"❌ Bronze layer failed: {e}")
    dbutils.notebook.exit("BRONZE_FAILED")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Stage 3/6: Silver - Transform and Cleanse

# COMMAND ----------

print("=" * 100)
print("🥈 STAGE 3/6 - SILVER: Transform and partition")
print("=" * 100)

try:
    silver_result = silver_layer_notebook(spark, config)
    
    print(f"✅ Silver layer complete!")
    print(f"   • Total records: {silver_result['total_records']}")
    print(f"   • Duplicates removed: {silver_result['duplicates_removed']}")
    print(f"   • Partition stats: {silver_result['partition_stats']}")
    print(f"   • Output directory: {silver_result['output_path']}")
    
except Exception as e:
    print(f"❌ Silver layer failed: {e}")
    dbutils.notebook.exit("SILVER_FAILED")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Stage 4/6: Quality Gate - Validate Data

# COMMAND ----------

print("=" * 100)
print("✅ STAGE 4/6 - QUALITY: Validate Silver data quality")
print("=" * 100)

try:
    quality_result = quality_check_notebook(spark, config)
    
    print(f"✅ Quality check complete!")
    print(f"   • Status: {quality_result['status']}")
    print(f"   • Total validated records: {quality_result['total_records']}")
    print(f"   • Checks performed: {quality_result['checks_performed']}")
    print(f"   • Checks passed: {quality_result['checks_passed']}")
    print(f"   • Success rate: {quality_result['success_rate']:.1f}%")
    
    if quality_result.get('issues'):
        print(f"\n   ⚠️  Issues found:")
        for issue in quality_result['issues']:
            print(f"      • {issue}")
    
    # HALT PIPELINE IF QUALITY CHECK FAILED
    if quality_result['status'] == 'FAILED':
        print("\n" + "=" * 100)
        print("❌ PIPELINE HALTED: Data quality check FAILED")
        print("=" * 100)
        print("Critical data quality issues detected. Gold layer will NOT be created.")
        print("Please review the issues above and fix the data problems.")
        dbutils.notebook.exit("QUALITY_CHECK_FAILED")
    
except Exception as e:
    print(f"❌ Quality check failed: {e}")
    dbutils.notebook.exit("QUALITY_CHECK_ERROR")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Stage 5/6: Gold - Create Aggregations

# COMMAND ----------

print("=" * 100)
print("🥇 STAGE 5/6 - GOLD: Create aggregations")
print("=" * 100)

try:
    gold_result = gold_layer_notebook(spark, config)
    
    print(f"✅ Gold layer complete!")
    print(f"   • Source records: {gold_result['source_records']}")
    print(f"   • Aggregated rows: {gold_result['aggregated_rows']}")
    print(f"   • Generated files:")
    for file_type, path in gold_result['output_files'].items():
        print(f"      - {file_type}: {path}")
    
except Exception as e:
    print(f"❌ Gold layer failed: {e}")
    dbutils.notebook.exit("GOLD_FAILED")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Stage 6/6: Summary

# COMMAND ----------

print("=" * 100)
print("🎉 STAGE 6/6 - SUMMARY: Pipeline completed")
print("=" * 100)

end_time = datetime.now()
duration = (end_time - start_time).total_seconds()

print("\n" + "=" * 100)
print("🎉 PIPELINE EXECUTED SUCCESSFULLY!")
print("=" * 100)
print(f"\n⏰ Start: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"⏰ End: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"⏱️  Total duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
print("\n" + "-" * 100)
print("\n📊 EXECUTION SUMMARY:")
print(f"\n   1️⃣  EXTRACT:  {extract_result['records_extracted']:,} records extracted")
print(f"   2️⃣  BRONZE:   {bronze_result['total_records']:,} records saved")
print(f"   3️⃣  SILVER:   {silver_result['total_records']:,} records cleaned")
print(f"   4️⃣  QUALITY:  {quality_result['success_rate']:.1f}% quality (Status: {quality_result['status']})")
print(f"   5️⃣  GOLD:     {gold_result['aggregated_rows']:,} rows aggregated")

print("\n📁 DATA STRUCTURE CREATED:")
print("\n   📂 Azure Blob Storage/")
print(f"   ├── 📂 {config.AZURE_CONTAINER_RAW}/ (Raw JSON)")
print(f"   ├── 📂 {config.AZURE_CONTAINER_BRONZE}/ (Bronze JSON)")
print(f"   ├── 📂 {config.AZURE_CONTAINER_SILVER}/ (Delta Lake, partitioned)")
print(f"   └── 📂 {config.AZURE_CONTAINER_GOLD}/ (Delta Lake + CSV)")

print("\n🔍 NEXT STEPS:")
print("\n   • Query Delta tables with: spark.read.format('delta').load(path)")
print(f"   • View CSV files in Azure Portal: {config.AZURE_STORAGE_ACCOUNT}")
print("   • Create visualizations in Databricks dashboards")
print("   • Schedule this notebook with Databricks Jobs")

print("\n" + "=" * 100)

# Return summary for downstream processing
dbutils.notebook.exit(json.dumps({
    "status": "SUCCESS",
    "duration_seconds": duration,
    "records": {
        "extracted": extract_result['records_extracted'],
        "bronze": bronze_result['total_records'],
        "silver": silver_result['total_records'],
        "gold": gold_result['aggregated_rows']
    },
    "quality_score": quality_result['success_rate'],
    "timestamp": end_time.isoformat()
}))

"""
Azure Blob Storage configuration for Databricks.
"""

# Azure Blob Storage Configuration
AZURE_STORAGE_ACCOUNT = "your_storage_account_name"  # Replace with your storage account
AZURE_CONTAINER_BRONZE = "brewery-bronze"
AZURE_CONTAINER_SILVER = "brewery-silver"
AZURE_CONTAINER_GOLD = "brewery-gold"
AZURE_CONTAINER_RAW = "brewery-raw"

# Storage paths (ABFS - Azure Blob File System)
ABFS_BRONZE_PATH = f"abfss://{AZURE_CONTAINER_BRONZE}@{AZURE_STORAGE_ACCOUNT}.dfs.core.windows.net/"
ABFS_SILVER_PATH = f"abfss://{AZURE_CONTAINER_SILVER}@{AZURE_STORAGE_ACCOUNT}.dfs.core.windows.net/"
ABFS_GOLD_PATH = f"abfss://{AZURE_CONTAINER_GOLD}@{AZURE_STORAGE_ACCOUNT}.dfs.core.windows.net/"
ABFS_RAW_PATH = f"abfss://{AZURE_CONTAINER_RAW}@{AZURE_STORAGE_ACCOUNT}.dfs.core.windows.net/"

# API Configuration
BREWERY_API_URL = "https://api.openbrewerydb.org/v1/breweries"
API_TIMEOUT = 30
API_RETRY_ATTEMPTS = 3
PER_PAGE = 200

# Data Quality Thresholds
DQ_MIN_RECORDS = 100
DQ_MAX_DUPLICATE_PCT = 5.0
DQ_MIN_COMPLETENESS_PCT = 70.0
DQ_MIN_COORDINATE_PCT = 50.0

# Databricks Configuration
DATABRICKS_MOUNT_POINT_BRONZE = "/mnt/brewery-bronze"
DATABRICKS_MOUNT_POINT_SILVER = "/mnt/brewery-silver"
DATABRICKS_MOUNT_POINT_GOLD = "/mnt/brewery-gold"
DATABRICKS_MOUNT_POINT_RAW = "/mnt/brewery-raw"

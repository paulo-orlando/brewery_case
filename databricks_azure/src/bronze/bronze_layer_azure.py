"""
Bronze layer module for Databricks + Azure Blob Storage.
Preserves raw data with minimal transformation.
Uses PySpark for distributed processing.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import lit, current_timestamp, input_file_name
from pyspark.sql.types import StructType, StringType
from datetime import datetime
from typing import Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BronzeLayerError(Exception):
    """Custom exception for bronze layer errors."""
    pass


def save_to_bronze_azure(
    spark: SparkSession,
    input_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Save raw JSON data to Bronze layer in Azure Blob Storage.
    Preserves original structure with added metadata.
    
    Args:
        spark: Active SparkSession
        input_path: Path to raw JSON files in Azure (abfss:// or /mnt/)
        output_path: Path to Bronze layer in Azure
        
    Returns:
        Dictionary with operation metadata
        
    Raises:
        BronzeLayerError: If bronze layer creation fails
    """
    try:
        logger.info(f"Reading raw data from {input_path}")
        
        # Read JSON files from Azure
        # Pattern to match all JSON files in the directory
        json_pattern = f"{input_path}/*.json" if not input_path.endswith('/') else f"{input_path}*.json"
        
        # Read JSON - each file contains a full extraction with metadata
        raw_df = spark.read.option("multiline", "true").json(json_pattern)
        
        # If the JSON has a "records" array, explode it
        if "records" in raw_df.columns:
            from pyspark.sql.functions import explode
            df = raw_df.select(
                explode("records").alias("record"),
                "extraction_timestamp",
                "execution_date",
                "total_records"
            )
            # Flatten the record structure
            from pyspark.sql.functions import col
            record_cols = [col(f"record.{c}").alias(c) for c in df.select("record.*").columns]
            df = df.select(
                *record_cols,
                col("extraction_timestamp").alias("raw_extraction_timestamp"),
                col("execution_date").alias("raw_execution_date")
            )
        else:
            df = raw_df
        
        # Add bronze layer metadata
        df_with_metadata = df \
            .withColumn("bronze_ingestion_timestamp", current_timestamp()) \
            .withColumn("bronze_ingestion_date", lit(datetime.utcnow().strftime('%Y-%m-%d'))) \
            .withColumn("source_file", input_file_name())
        
        # Count records
        record_count = df_with_metadata.count()
        logger.info(f"Processing {record_count} records to bronze layer")
        
        # Save to Bronze layer as JSON (preserving original structure)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        output_file = f"{output_path}/bronze_breweries_{timestamp}.json"
        
        df_with_metadata \
            .coalesce(1) \
            .write \
            .mode("overwrite") \
            .json(output_file)
        
        logger.info(f"✅ Saved {record_count} records to bronze layer: {output_file}")
        
        return {
            "status": "success",
            "total_records": record_count,
            "output_path": output_file,
            "timestamp": timestamp,
            "files_processed": 1
        }
        
    except Exception as e:
        logger.error(f"Error in bronze layer processing: {e}")
        raise BronzeLayerError(f"Failed to create bronze layer: {e}")


def bronze_layer_notebook(spark, config):
    """
    Convenience function for Databricks notebooks.
    
    Args:
        spark: SparkSession from notebook
        config: Configuration dictionary or module
        
    Returns:
        Bronze layer result dictionary
    """
    from datetime import datetime
    
    execution_date = datetime.utcnow().strftime('%Y-%m-%d')
    
    # Use mounted paths or ABFS paths
    if hasattr(config, 'DATABRICKS_MOUNT_POINT_RAW'):
        input_path = f"{config.DATABRICKS_MOUNT_POINT_RAW}/{execution_date}"
        output_path = f"{config.DATABRICKS_MOUNT_POINT_BRONZE}/{execution_date}"
    else:
        input_path = f"{config.ABFS_RAW_PATH}{execution_date}"
        output_path = f"{config.ABFS_BRONZE_PATH}{execution_date}"
    
    return save_to_bronze_azure(
        spark=spark,
        input_path=input_path,
        output_path=output_path
    )


if __name__ == "__main__":
    print("This module requires a Spark session. Use in Databricks notebook.")
    print("Example usage:")
    print("  result = bronze_layer_notebook(spark, config)")

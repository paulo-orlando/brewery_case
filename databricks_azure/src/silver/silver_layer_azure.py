"""
Silver layer module for Databricks + Azure Blob Storage.
Transforms and cleanses data using PySpark, saves as Delta Lake format.
Partitioned by country and state for optimal query performance.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, trim, upper, when, lit, current_timestamp,
    regexp_replace, to_date, monotonically_increasing_id, concat_ws
)
from pyspark.sql.types import DoubleType
from datetime import datetime
from typing import Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SilverLayerError(Exception):
    """Custom exception for silver layer errors."""
    pass


def fix_encoding_spark(df, text_columns):
    """
    Fix character encoding issues in PySpark DataFrame.
    Handles German umlauts, Spanish/French accents, etc.
    
    Args:
        df: PySpark DataFrame
        text_columns: List of column names to fix
        
    Returns:
        DataFrame with fixed encoding
    """
    encoding_fixes = {
        'Ã¤': 'ä', 'Ã¶': 'ö', 'Ã¼': 'ü',
        'Ã': 'Ä', 'Ã': 'Ö', 'Ã': 'Ü',
        'Ã±': 'ñ', 'Ã©': 'é', 'Ã¡': 'á',
        'Ã­': 'í', 'Ã³': 'ó', 'Ãº': 'ú',
        'Ã ': 'à', 'Ã¨': 'è', 'Ã¬': 'ì',
        'Ã²': 'ò', 'Ã¹': 'ù', 'Ã§': 'ç',
        'Ã£': 'ã', 'Ãµ': 'õ', 'â': 'â',
        # Special cases
        'KÃ¤rnten': 'Kärnten',
        'MÃ¼nchen': 'München',
        'ZÃ¼rich': 'Zürich'
    }
    
    for column in text_columns:
        if column in df.columns:
            for bad, good in encoding_fixes.items():
                df = df.withColumn(column, regexp_replace(col(column), bad, good))
    
    return df


def transform_to_silver_azure(
    spark: SparkSession,
    input_path: str,
    output_path: str,
    partition_cols: list = None
) -> Dict[str, Any]:
    """
    Transform bronze data to silver layer with PySpark.
    Saves as Delta Lake format in Azure Blob Storage.
    
    Args:
        spark: Active SparkSession
        input_path: Path to bronze JSON files in Azure
        output_path: Path to silver layer in Azure
        partition_cols: Columns to partition by (default: ['country', 'state'])
        
    Returns:
        Dictionary with operation metadata
        
    Raises:
        SilverLayerError: If transformation fails
    """
    try:
        if partition_cols is None:
            partition_cols = ['country', 'state']
        
        logger.info(f"Reading bronze data from {input_path}")
        
        json_pattern = f"{input_path}/*.json" if not input_path.endswith('/') else f"{input_path}*.json"
        df = spark.read.option("multiline", "true").json(json_pattern)
        
        initial_count = df.count()
        logger.info(f"Loaded {initial_count} total records from bronze layer")
        
        if 'id' in df.columns:
            df_deduplicated = df.dropDuplicates(['id'])
            duplicates_removed = initial_count - df_deduplicated.count()
            if duplicates_removed > 0:
                logger.warning(f"Removed {duplicates_removed} duplicate records")
            df = df_deduplicated
        
        logger.info(f"Starting transformation on {df.count()} records")
        
        text_columns = [
            'name', 'brewery_type', 'address_1', 'address_2', 'address_3',
            'city', 'state_province', 'postal_code', 'country',
            'state', 'street', 'phone', 'website_url'
        ]
        
        for col_name in text_columns:
            if col_name in df.columns:
                df = df.withColumn(col_name, trim(col(col_name)))
                df = df.withColumn(col_name, when(col(col_name) == "", None).otherwise(col(col_name)))
        
        df = fix_encoding_spark(df, text_columns)
        
        if 'latitude' in df.columns:
            df = df.withColumn('latitude', col('latitude').cast(DoubleType()))
        
        if 'longitude' in df.columns:
            df = df.withColumn('longitude', col('longitude').cast(DoubleType()))
        
        df = df.withColumn('ingestion_timestamp', current_timestamp())
        df = df.withColumn('ingestion_date', lit(datetime.utcnow().strftime('%Y-%m-%d')))
        
        df = df.withColumn(
            'location_key',
            when(col('country').isNotNull() & col('state').isNotNull(),
                 concat_ws('-', col('country'), col('state'))
            ).otherwise(None)
        )
        
        df = df.withColumn(
            'has_complete_address',
            when(
                col('address_1').isNotNull() &
                col('city').isNotNull() &
                col('state').isNotNull() &
                col('postal_code').isNotNull(),
                lit(True)
            ).otherwise(lit(False))
        )
        
        df = df.withColumn(
            'has_coordinates',
            when(
                col('latitude').isNotNull() & col('longitude').isNotNull(),
                lit(True)
            ).otherwise(lit(False))
        )
        
        for part_col in partition_cols:
            if part_col in df.columns:
                df = df.withColumn(
                    part_col,
                    when(col(part_col).isNull(), lit('UNKNOWN')).otherwise(col(part_col))
                )
        
        final_count = df.count()
        logger.info(f"Transformation complete: {final_count} records")
        
        partition_stats = {}
        for part_col in partition_cols:
            if part_col in df.columns:
                unique_count = df.select(part_col).distinct().count()
                partition_stats[f"unique_{part_col}"] = unique_count
                logger.info(f"   Unique {part_col}: {unique_count}")
        
        logger.info(f"Writing to silver layer: {output_path}")
        df.write \
            .format("delta") \
            .mode("overwrite") \
            .partitionBy(*partition_cols) \
            .save(output_path)
        
        logger.info(f"✅ Silver layer transformation complete: {final_count} records written")
        
        return {
            "status": "success",
            "total_records": final_count,
            "duplicates_removed": initial_count - final_count,
            "output_path": output_path,
            "partition_stats": partition_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in silver layer transformation: {e}")
        raise SilverLayerError(f"Silver layer transformation failed: {e}")


def silver_layer_notebook(spark, config):
    """
    Convenience function for Databricks notebooks.
    
    Args:
        spark: SparkSession from notebook
        config: Configuration dictionary or module
        
    Returns:
        Silver layer result dictionary
    """
    from datetime import datetime
    
    execution_date = datetime.utcnow().strftime('%Y-%m-%d')
    
    # Use mounted paths or ABFS paths
    if hasattr(config, 'DATABRICKS_MOUNT_POINT_BRONZE'):
        input_path = f"{config.DATABRICKS_MOUNT_POINT_BRONZE}/{execution_date}"
        output_path = f"{config.DATABRICKS_MOUNT_POINT_SILVER}/breweries"
    else:
        input_path = f"{config.ABFS_BRONZE_PATH}{execution_date}"
        output_path = f"{config.ABFS_SILVER_PATH}breweries"
    
    return transform_to_silver_azure(
        spark=spark,
        input_path=input_path,
        output_path=output_path,
        partition_cols=['country', 'state']
    )


if __name__ == "__main__":
    print("This module requires a Spark session. Use in Databricks notebook.")
    print("Example usage:")
    print("  result = silver_layer_notebook(spark, config)")

"""
Gold layer module for Databricks + Azure Blob Storage.
Creates analytical aggregations using PySpark.
Saves as Delta Lake format for optimal query performance.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, count, countDistinct, avg, sum as spark_sum,
    when, lit, round as spark_round, current_timestamp
)
from datetime import datetime
from typing import Dict, Any
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GoldLayerError(Exception):
    """Custom exception for gold layer errors."""
    pass


def create_gold_aggregations_azure(
    spark: SparkSession,
    input_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Create aggregated views from silver layer data using PySpark.
    Saves as Delta Lake format in Azure Blob Storage.
    
    Args:
        spark: Active SparkSession
        input_path: Path to silver Delta table in Azure
        output_path: Path to gold layer in Azure
        
    Returns:
        Dictionary with operation metadata
        
    Raises:
        GoldLayerError: If aggregation fails
    """
    try:
        logger.info(f"Reading silver layer data from {input_path}")
        
        # Read Delta Lake table from Silver layer
        df = spark.read.format("delta").load(input_path)
        
        record_count = df.count()
        logger.info(f"Loaded {record_count} records from silver layer")
        
        if record_count == 0:
            raise GoldLayerError("No data found in silver layer")
        
        # Create aggregation: breweries by type and location
        logger.info("Creating type and location aggregation")
        
        agg_df = df.groupBy('country', 'state', 'brewery_type').agg(
            count('id').alias('brewery_count'),
            countDistinct('city').alias('unique_cities'),
            avg('latitude').alias('avg_latitude'),
            avg('longitude').alias('avg_longitude'),
            (spark_sum(when(col('has_coordinates') == True, 1).otherwise(0)) / count('*') * 100).alias('pct_with_coordinates'),
            (spark_sum(when(col('has_complete_address') == True, 1).otherwise(0)) / count('*') * 100).alias('pct_with_address')
        )
        
        # Round numeric columns
        agg_df = agg_df \
            .withColumn('avg_latitude', spark_round(col('avg_latitude'), 4)) \
            .withColumn('avg_longitude', spark_round(col('avg_longitude'), 4)) \
            .withColumn('pct_with_coordinates', spark_round(col('pct_with_coordinates'), 2)) \
            .withColumn('pct_with_address', spark_round(col('pct_with_address'), 2))
        
        # Add aggregation metadata
        agg_df = agg_df.withColumn('aggregation_timestamp', current_timestamp())
        
        # Sort by country, state, and brewery count
        agg_df = agg_df.orderBy('country', 'state', col('brewery_count').desc())
        
        agg_count = agg_df.count()
        logger.info(f"Created aggregation with {agg_count} rows")
        
        # Save aggregation as Delta Lake
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        aggregation_path = f"{output_path}/breweries_by_type_location"
        
        agg_df.write \
            .format("delta") \
            .mode("overwrite") \
            .save(aggregation_path)
        
        logger.info(f"✅ Saved aggregation to {aggregation_path}")
        
        # Also save as CSV for easy viewing
        csv_path = f"{output_path}/breweries_by_type_location_{timestamp}.csv"
        agg_df.coalesce(1) \
            .write \
            .mode("overwrite") \
            .option("header", "true") \
            .option("encoding", "UTF-8") \
            .csv(csv_path)
        
        logger.info(f"✅ Saved CSV version to {csv_path}")
        
        # Create summary statistics
        logger.info("Creating summary statistics")
        
        summary = {
            "total_breweries": record_count,
            "unique_countries": df.select('country').distinct().count(),
            "unique_states": df.select('state').distinct().count(),
            "unique_cities": df.select('city').distinct().count(),
            "brewery_types": {
                row['brewery_type']: row['count']
                for row in df.groupBy('brewery_type').count().collect()
            },
            "top_10_states": {
                row['state']: row['count']
                for row in df.groupBy('state').count().orderBy(col('count').desc()).limit(10).collect()
            },
            "top_10_cities": {
                row['city']: row['count']
                for row in df.groupBy('city').count().orderBy(col('count').desc()).limit(10).collect()
            },
            "data_quality": {
                "records_with_coordinates": df.filter(col('has_coordinates') == True).count(),
                "pct_with_coordinates": round(df.filter(col('has_coordinates') == True).count() / record_count * 100, 2),
                "records_with_complete_address": df.filter(col('has_complete_address') == True).count(),
                "pct_with_complete_address": round(df.filter(col('has_complete_address') == True).count() / record_count * 100, 2)
            },
            "generated_at": datetime.utcnow().isoformat(),
            "timestamp": timestamp
        }
        
        # Save summary as JSON
        summary_path = f"{output_path}/summary_statistics_{timestamp}.json"
        summary_json = json.dumps(summary, indent=2, ensure_ascii=False)
        spark.sparkContext.parallelize([summary_json]).saveAsTextFile(summary_path)
        
        logger.info(f"✅ Saved summary statistics to {summary_path}")
        logger.info(f"✅ Gold layer aggregation complete: {agg_count} aggregated rows")
        
        return {
            "status": "success",
            "source_records": record_count,
            "aggregated_rows": agg_count,
            "output_files": {
                "delta": aggregation_path,
                "csv": csv_path,
                "summary": summary_path
            },
            "summary": summary,
            "timestamp": timestamp
        }
        
    except GoldLayerError:
        raise
    except Exception as e:
        logger.error(f"Error in gold layer aggregation: {e}")
        raise GoldLayerError(f"Gold layer aggregation failed: {e}")


def gold_layer_notebook(spark, config):
    """
    Convenience function for Databricks notebooks.
    
    Args:
        spark: SparkSession from notebook
        config: Configuration dictionary or module
        
    Returns:
        Gold layer result dictionary
    """
    # Use mounted paths or ABFS paths
    if hasattr(config, 'DATABRICKS_MOUNT_POINT_SILVER'):
        input_path = f"{config.DATABRICKS_MOUNT_POINT_SILVER}/breweries"
        output_path = config.DATABRICKS_MOUNT_POINT_GOLD
    else:
        input_path = f"{config.ABFS_SILVER_PATH}breweries"
        output_path = config.ABFS_GOLD_PATH
    
    return create_gold_aggregations_azure(
        spark=spark,
        input_path=input_path,
        output_path=output_path
    )


if __name__ == "__main__":
    print("This module requires a Spark session. Use in Databricks notebook.")
    print("Example usage:")
    print("  result = gold_layer_notebook(spark, config)")

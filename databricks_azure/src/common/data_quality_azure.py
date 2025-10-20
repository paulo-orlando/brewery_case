"""
Data quality module for Databricks + Azure Blob Storage.
Validates data quality using PySpark DataFrame operations.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, when, isnan
from datetime import datetime
from typing import Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataQualityError(Exception):
    """Custom exception for critical data quality failures."""
    pass


def check_data_quality_azure(
    spark: SparkSession,
    input_path: str,
    layer: str = "silver",
    thresholds: Dict[str, float] = None
) -> Dict[str, Any]:
    """
    Perform data quality checks on Delta Lake table using PySpark.
    
    Args:
        spark: Active SparkSession
        input_path: Path to Delta table in Azure
        layer: Layer name (for logging)
        thresholds: Quality thresholds dictionary
        
    Returns:
        Dictionary with quality check results
        
    Raises:
        DataQualityError: If critical quality checks fail
    """
    try:
        if thresholds is None:
            thresholds = {
                "min_records": 100,
                "max_duplicate_pct": 5.0,
                "min_completeness_pct": 70.0,
                "min_coordinate_pct": 50.0
            }
        
        logger.info(f"Running data quality checks on {layer} layer: {input_path}")
        
        df = spark.read.format("delta").load(input_path)
        
        checks = []
        
        record_count = df.count()
        check_1_passed = record_count >= thresholds["min_records"]
        checks.append({
            "check": "minimum_record_count",
            "passed": check_1_passed,
            "value": record_count,
            "threshold": thresholds["min_records"],
            "severity": "critical" if not check_1_passed else "info"
        })
        
        if 'id' in df.columns:
            total_records = record_count
            unique_records = df.select('id').distinct().count()
            duplicate_count = total_records - unique_records
            duplicate_pct = (duplicate_count / total_records * 100) if total_records > 0 else 0
            check_2_passed = duplicate_pct <= thresholds["max_duplicate_pct"]
            checks.append({
                "check": "duplicate_records",
                "passed": check_2_passed,
                "value": f"{duplicate_pct:.2f}%",
                "threshold": f"{thresholds['max_duplicate_pct']}%",
                "severity": "warning" if not check_2_passed else "info"
            })
        
        critical_cols = ['id', 'name', 'brewery_type', 'country', 'state']
        available_critical_cols = [c for c in critical_cols if c in df.columns]
        
        if available_critical_cols:
            completeness_scores = {}
            for col_name in available_critical_cols:
                non_null_count = df.filter(col(col_name).isNotNull()).count()
                non_null_pct = (non_null_count / record_count * 100) if record_count > 0 else 0
                completeness_scores[col_name] = round(non_null_pct, 2)
            
            avg_completeness = sum(completeness_scores.values()) / len(completeness_scores)
            check_3_passed = avg_completeness >= thresholds["min_completeness_pct"]
            checks.append({
                "check": "data_completeness",
                "passed": check_3_passed,
                "value": f"{avg_completeness:.2f}%",
                "threshold": f"{thresholds['min_completeness_pct']}%",
                "severity": "critical" if not check_3_passed else "info",
                "details": completeness_scores
            })
        
        if 'latitude' in df.columns and 'longitude' in df.columns:
            coords_available = df.filter(
                col('latitude').isNotNull() & col('longitude').isNotNull()
            ).count()
            coords_pct = (coords_available / record_count * 100) if record_count > 0 else 0
            check_4_passed = coords_pct >= thresholds["min_coordinate_pct"]
            checks.append({
                "check": "coordinate_availability",
                "passed": check_4_passed,
                "value": f"{coords_pct:.2f}%",
                "threshold": f"{thresholds['min_coordinate_pct']}%",
                "severity": "warning" if not check_4_passed else "info"
            })
        
        expected_cols = ['id', 'name', 'brewery_type']
        missing_cols = [c for c in expected_cols if c not in df.columns]
        check_5_passed = len(missing_cols) == 0
        checks.append({
            "check": "schema_validation",
            "passed": check_5_passed,
            "value": "all required columns present" if check_5_passed else f"missing: {missing_cols}",
            "severity": "critical" if not check_5_passed else "info"
        })
        
        critical_failures = [c for c in checks if c["severity"] == "critical" and not c["passed"]]
        warnings = [c for c in checks if c["severity"] == "warning" and not c["passed"]]
        
        if critical_failures:
            status = "FAILED"
        elif warnings:
            status = "WARNING"
        else:
            status = "PASSED"
        
        result = {
            "status": status,
            "layer": layer,
            "total_records": record_count,
            "checks": checks,
            "critical_failures": len(critical_failures),
            "warnings": len(warnings),
            "passed_checks": len([c for c in checks if c["passed"]]),
            "total_checks": len(checks),
            "checks_performed": len(checks),
            "checks_passed": len([c for c in checks if c["passed"]]),
            "success_rate": (len([c for c in checks if c["passed"]]) / len(checks) * 100) if checks else 0,
            "issues": [f"{f['check']}: {f['value']}" for f in critical_failures + warnings],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Quality check result: {status}")
        logger.info(f"Passed: {result['passed_checks']}/{result['total_checks']}")
        
        if critical_failures:
            logger.error(f"Critical failures: {len(critical_failures)}")
            for failure in critical_failures:
                logger.error(f"  - {failure['check']}: {failure['value']}")
        
        if warnings:
            logger.warning(f"Warnings: {len(warnings)}")
            for warning in warnings:
                logger.warning(f"  - {warning['check']}: {warning['value']}")
        
        if critical_failures:
            raise DataQualityError(f"Data quality check failed with {len(critical_failures)} critical issue(s)")
        
        return result
        
    except DataQualityError:
        raise
    except Exception as e:
        logger.error(f"❌ Data quality check failed: {e}")
        raise DataQualityError(f"Failed to perform quality checks: {e}")


def quality_check_notebook(spark, config):
    """
    Convenience function for Databricks notebooks.
    
    Args:
        spark: SparkSession from notebook
        config: Configuration dictionary or module
        
    Returns:
        Quality check result dictionary
    """
    if hasattr(config, 'DATABRICKS_MOUNT_POINT_SILVER'):
        input_path = f"{config.DATABRICKS_MOUNT_POINT_SILVER}/breweries"
    else:
        input_path = f"{config.ABFS_SILVER_PATH}breweries"
    
    thresholds = {
        "min_records": getattr(config, 'DQ_MIN_RECORDS', 100),
        "max_duplicate_pct": getattr(config, 'DQ_MAX_DUPLICATE_PCT', 5.0),
        "min_completeness_pct": getattr(config, 'DQ_MIN_COMPLETENESS_PCT', 70.0),
        "min_coordinate_pct": getattr(config, 'DQ_MIN_COORDINATE_PCT', 50.0)
    }
    
    return check_data_quality_azure(
        spark=spark,
        input_path=input_path,
        layer='silver',
        thresholds=thresholds
    )


if __name__ == "__main__":
    print("This module requires a Spark session. Use in Databricks notebook.")
    print("Example usage:")
    print("  result = quality_check_notebook(spark, config)")

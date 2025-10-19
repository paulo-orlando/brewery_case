"""
Data quality validation module.
Performs quality checks on data at different layers.
"""
from pathlib import Path
from typing import Dict, Any, List
import logging
import pandas as pd
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataQualityError(Exception):
    """Custom exception for data quality errors."""
    pass


def check_data_quality(input_path: str, layer: str = "silver", thresholds: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Perform data quality checks on specified layer.
    
    Args:
        input_path: Path to data layer
        layer: Layer name (bronze/silver/gold)
        thresholds: Dictionary of quality thresholds
        
    Returns:
        Dictionary with quality check results
        
    Raises:
        DataQualityError: If critical quality checks fail
    """
    if thresholds is None:
        thresholds = {
            "min_records": 100,
            "min_completeness_pct": 70.0,
            "max_duplicate_pct": 5.0,
            "min_coordinate_pct": 50.0
        }
    
    try:
        input_dir = Path(input_path)
        
        if not input_dir.exists():
            raise DataQualityError(f"Input path does not exist: {input_path}")
        
        logger.info(f"Running data quality checks on {layer} layer: {input_path}")
        
        # Load data based on layer
        if layer == "silver" or layer == "gold":
            df = pd.read_parquet(input_dir)
        elif layer == "bronze":
            # Read JSON files
            json_files = list(input_dir.glob("*.json"))
            if not json_files:
                raise DataQualityError("No JSON files found in bronze layer")
            
            records = []
            for json_file in json_files:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, dict) and "data" in data:
                    records.extend(data["data"])
                elif isinstance(data, list):
                    records.extend(data)
            
            df = pd.DataFrame(records)
        else:
            raise DataQualityError(f"Unknown layer: {layer}")
        
        if df.empty:
            raise DataQualityError(f"No data found in {layer} layer")
        
        # Run quality checks
        checks = []
        
        # Check 1: Minimum record count
        record_count = len(df)
        check_1_passed = record_count >= thresholds["min_records"]
        checks.append({
            "check": "minimum_record_count",
            "passed": check_1_passed,
            "value": record_count,
            "threshold": thresholds["min_records"],
            "severity": "critical" if not check_1_passed else "info"
        })
        
        # Check 2: Duplicate records (if id column exists)
        if 'id' in df.columns:
            duplicate_count = df['id'].duplicated().sum()
            duplicate_pct = (duplicate_count / len(df) * 100) if len(df) > 0 else 0
            check_2_passed = duplicate_pct <= thresholds["max_duplicate_pct"]
            checks.append({
                "check": "duplicate_records",
                "passed": check_2_passed,
                "value": f"{duplicate_pct:.2f}%",
                "threshold": f"{thresholds['max_duplicate_pct']}%",
                "severity": "warning" if not check_2_passed else "info"
            })
        
        # Check 3: Data completeness (non-null percentage)
        completeness_scores = {}
        critical_cols = ['id', 'name', 'brewery_type', 'country', 'state']
        available_critical_cols = [col for col in critical_cols if col in df.columns]
        
        if available_critical_cols:
            for col in available_critical_cols:
                non_null_pct = (df[col].notna().sum() / len(df) * 100) if len(df) > 0 else 0
                completeness_scores[col] = round(non_null_pct, 2)
            
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
        
        # Check 4: Coordinate availability (for silver/gold layers)
        if 'latitude' in df.columns and 'longitude' in df.columns:
            coords_available = ((df['latitude'].notna()) & (df['longitude'].notna())).sum()
            coords_pct = (coords_available / len(df) * 100) if len(df) > 0 else 0
            check_4_passed = coords_pct >= thresholds["min_coordinate_pct"]
            checks.append({
                "check": "coordinate_availability",
                "passed": check_4_passed,
                "value": f"{coords_pct:.2f}%",
                "threshold": f"{thresholds['min_coordinate_pct']}%",
                "severity": "warning" if not check_4_passed else "info"
            })
        
        # Check 5: Schema validation
        expected_cols = ['id', 'name', 'brewery_type']
        missing_cols = [col for col in expected_cols if col not in df.columns]
        check_5_passed = len(missing_cols) == 0
        checks.append({
            "check": "schema_validation",
            "passed": check_5_passed,
            "value": "all required columns present" if check_5_passed else f"missing: {missing_cols}",
            "severity": "critical" if not check_5_passed else "info"
        })
        
        # Determine overall status
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
            "timestamp": pd.Timestamp.utcnow().isoformat()
        }
        
        # Log results
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
        
        # Raise error if critical failures
        if critical_failures:
            raise DataQualityError(f"Data quality check failed with {len(critical_failures)} critical issue(s)")
        
        return result
        
    except DataQualityError:
        raise
    except Exception as e:
        logger.error(f"❌ Data quality check failed: {e}")
        raise DataQualityError(f"Failed to perform quality checks: {e}")


if __name__ == "__main__":
    # Test the module
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python data_quality.py <input_path> [layer]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    layer = sys.argv[2] if len(sys.argv) > 2 else "silver"
    
    try:
        result = check_data_quality(input_path, layer)
        print(f"\nQuality check {result['status']}")
        print(json.dumps(result, indent=2))
    except DataQualityError as e:
        print(f"Quality check failed: {e}")
        sys.exit(1)

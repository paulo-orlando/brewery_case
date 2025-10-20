"""
Bronze layer: Raw data persistence.
Handles copying raw JSON data to bronze layer with minimal transformation.
"""
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BronzeLayerError(Exception):
    """Custom exception for bronze layer errors."""
    pass


def save_to_bronze(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Save raw data to bronze layer with validation.
    
    The bronze layer stores data in its raw format (JSON) with:
    - Original structure preserved
    - Timestamp and lineage metadata
    - No transformations applied
    
    Args:
        input_path: Directory containing raw JSON files from API
        output_path: Bronze layer output directory
        
    Returns:
        Dictionary with operation metadata
        
    Raises:
        BronzeLayerError: If save operation fails
    """
    try:
        input_dir = Path(input_path)
        output_dir = Path(output_path)
        
        if not input_dir.exists():
            raise BronzeLayerError(f"Input path does not exist: {input_path}")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        json_files = list(input_dir.glob("*.json"))
        
        if not json_files:
            raise BronzeLayerError(f"No JSON files found in {input_path}")
        
        logger.info(f"Found {len(json_files)} JSON file(s) to process")
        
        total_records = 0
        processed_files = []
        
        for json_file in json_files:
            logger.info(f"Processing {json_file.name}")
            
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                records = data
                metadata = {}
            elif isinstance(data, dict) and "data" in data:
                records = data["data"]
                metadata = data.get("metadata", {})
            else:
                raise BronzeLayerError(f"Unexpected data format in {json_file.name}")
            
            if not records:
                logger.warning(f"No records found in {json_file.name}")
                continue
            
            bronze_data = {
                "bronze_metadata": {
                    "ingestion_timestamp": datetime.utcnow().isoformat(),
                    "source_file": json_file.name,
                    "record_count": len(records),
                    "layer": "bronze"
                },
                "source_metadata": metadata,
                "data": records
            }
            
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"bronze_breweries_{timestamp}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(bronze_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Saved {len(records)} records to {output_file.name}")
            
            total_records += len(records)
            processed_files.append(str(output_file))
        
        result = {
            "status": "success",
            "total_records": total_records,
            "files_processed": len(json_files),
            "output_files": processed_files,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Bronze layer processing complete: {total_records} total records")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Bronze layer processing failed: {e}")
        raise BronzeLayerError(f"Failed to save to bronze layer: {e}")


def validate_bronze_data(file_path: str) -> Dict[str, Any]:
    """
    Validate bronze layer data file.
    
    Args:
        file_path: Path to bronze JSON file
        
    Returns:
        Validation results dictionary
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        required_keys = ["bronze_metadata", "data"]
        missing_keys = [k for k in required_keys if k not in data]
        
        if missing_keys:
            return {
                "valid": False,
                "error": f"Missing required keys: {missing_keys}"
            }
        
        records = data["data"]
        
        return {
            "valid": True,
            "record_count": len(records),
            "metadata": data.get("bronze_metadata", {})
        }
        
    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python bronze_layer.py <input_path> <output_path>")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    try:
        result = save_to_bronze(input_path, output_path)
        print(f"Bronze layer save complete: {result}")
    except BronzeLayerError as e:
        print(f"Bronze layer save failed: {e}")
        sys.exit(1)

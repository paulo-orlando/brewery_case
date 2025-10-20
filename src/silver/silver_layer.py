"""
Silver layer: Curated data with transformations.
Converts JSON to Parquet format, partitions by location, and applies data quality rules.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SilverLayerError(Exception):
    """Custom exception for silver layer errors."""
    pass


def fix_encoding(text: str) -> str:
    """
    Fix common character encoding issues in text.
    
    Args:
        text: Input text that may have encoding issues
        
    Returns:
        Text with fixed encoding
    """
    if not isinstance(text, str) or text is None:
        return text
    
    # Common encoding replacements (ISO-8859-1 to UTF-8 issues)
    replacements = {
        'Ã¤': 'ä', 'Ã¶': 'ö', 'Ã¼': 'ü', 'ÃŸ': 'ß',  # German
        'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ã³': 'ó', 'Ãº': 'ú', 'Ã±': 'ñ',  # Spanish
        'Ã ': 'à', 'Ã¨': 'è', 'Ã¬': 'ì', 'Ã²': 'ò', 'Ã¹': 'ù',  # Italian/French
        'Ã§': 'ç', 'Ã£': 'ã', 'Ãµ': 'õ',  # Portuguese
        'Ã‰': 'É', 'Ã': 'Á', 'Ã"': 'Ó',  # Uppercase accented
        'K�rnten': 'Kärnten',  # Specific fix for Kärnten
        '�': ''  # Remove replacement character
    }
    
    result = text
    for wrong, correct in replacements.items():
        result = result.replace(wrong, correct)
    
    # Try to decode if still has issues
    try:
        # If text contains replacement character, try to fix
        if '�' in result:
            # Attempt to encode as latin-1 and decode as utf-8
            result = result.encode('latin-1', errors='ignore').decode('utf-8', errors='ignore')
    except (UnicodeDecodeError, UnicodeEncodeError, AttributeError):
        pass
    
    return result


def clean_and_transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply data quality transformations to brewery data.
    
    Transformations applied:
    1. Standardize column names (lowercase, underscores)
    2. Handle missing values
    3. Fix character encoding issues
    4. Standardize location fields
    5. Add derived columns
    6. Remove duplicates
    7. Validate data types
    
    Args:
        df: Raw brewery DataFrame
        
    Returns:
        Transformed DataFrame
    """
    logger.info(f"Starting transformation on {len(df)} records")
    
    # Create a copy to avoid modifying original
    df = df.copy()
    
    # 1. Standardize column names (already snake_case from API)
    df.columns = df.columns.str.lower().str.replace(' ', '_')
    
    # 2. Handle missing values
    # Fill empty strings with None for proper null handling
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].replace('', None)
            df[col] = df[col].replace('null', None)
    
    # 3. Fix character encoding issues in text columns
    text_columns = ['name', 'city', 'state', 'state_province', 'country', 
                    'address_1', 'address_2', 'address_3', 'street']
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: fix_encoding(x) if pd.notna(x) else x)
    
    # 4. Standardize location fields
    # Ensure country is properly set (default to "United States" if missing and state is US state)
    if 'country' in df.columns:
        df['country'] = df['country'].fillna('Unknown')
        df['country'] = df['country'].str.strip()
    else:
        df['country'] = 'Unknown'
    
    if 'state' in df.columns:
        df['state'] = df['state'].fillna('Unknown')
        df['state'] = df['state'].str.strip()
    else:
        df['state'] = 'Unknown'
    
    # Handle missing state_province (standardize to state column)
    if 'state_province' in df.columns and 'state' in df.columns:
        df['state'] = df['state'].fillna(df['state_province'])
    
    # 5. Add derived columns
    df['ingestion_date'] = datetime.utcnow().date()
    df['ingestion_timestamp'] = datetime.utcnow()
    
    # Add location composite key
    df['location_key'] = df['country'] + '_' + df['state']
    
    # Parse coordinates
    if 'latitude' in df.columns:
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    if 'longitude' in df.columns:
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    
    # Add flag for records with complete address
    address_cols = ['address_1', 'city', 'state', 'postal_code']
    available_cols = [col for col in address_cols if col in df.columns]
    if available_cols:
        df['has_complete_address'] = df[available_cols].notna().all(axis=1)
    
    # Add flag for records with coordinates
    if 'latitude' in df.columns and 'longitude' in df.columns:
        df['has_coordinates'] = df[['latitude', 'longitude']].notna().all(axis=1)
    
    # 6. Remove duplicates based on ID
    if 'id' in df.columns:
        initial_count = len(df)
        df = df.drop_duplicates(subset=['id'], keep='last')
        duplicates_removed = initial_count - len(df)
        if duplicates_removed > 0:
            logger.warning(f"Removed {duplicates_removed} duplicate records")
    
    # 7. Validate brewery_type
    if 'brewery_type' in df.columns:
        df['brewery_type'] = df['brewery_type'].fillna('unknown')
    
    logger.info(f"Transformation complete: {len(df)} records")
    
    return df


def transform_to_silver(
    input_path: str,
    output_path: str,
    partition_cols: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Transform bronze data to silver layer (Parquet format with partitioning).
    
    Args:
        input_path: Bronze layer input directory
        output_path: Silver layer output directory
        partition_cols: Columns to partition by (default: ['country', 'state'])
        
    Returns:
        Dictionary with operation metadata
        
    Raises:
        SilverLayerError: If transformation fails
    """
    try:
        if partition_cols is None:
            partition_cols = ['country', 'state']
        
        input_dir = Path(input_path)
        output_dir = Path(output_path)
        
        # Validate input
        if not input_dir.exists():
            raise SilverLayerError(f"Input path does not exist: {input_path}")
        
        # Find JSON files
        json_files = list(input_dir.glob("*.json"))
        
        if not json_files:
            raise SilverLayerError(f"No JSON files found in {input_path}")
        
        logger.info(f"Found {len(json_files)} JSON file(s) to process")
        
        # Collect all records
        all_records = []
        
        for json_file in json_files:
            logger.info(f"Reading {json_file.name}")
            
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract records
            if isinstance(data, dict) and "data" in data:
                records = data["data"]
            elif isinstance(data, list):
                records = data
            else:
                logger.warning(f"Unexpected format in {json_file.name}, skipping")
                continue
            
            all_records.extend(records)
        
        if not all_records:
            raise SilverLayerError("No records found in input files")
        
        logger.info(f"Loaded {len(all_records)} total records")
        
        # Convert to DataFrame
        df = pd.DataFrame(all_records)
        
        # Apply transformations
        df = clean_and_transform_data(df)
        
        # Validate partition columns exist
        missing_cols = [col for col in partition_cols if col not in df.columns]
        if missing_cols:
            logger.warning(f"Partition columns not found in data: {missing_cols}. Available columns: {df.columns.tolist()}")
            raise SilverLayerError(f"Partition columns not found in data: {missing_cols}. Available columns: {df.columns.tolist()}")
        
        logger.info(f"DataFrame has {len(df)} records with columns: {df.columns.tolist()}")
        logger.info(f"Partition columns verified: {partition_cols}")
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Reset index to avoid __index_level_0__ column in Parquet
        df = df.reset_index(drop=True)
        
        # Convert date columns to proper pandas datetime types before schema inference
        if 'ingestion_date' in df.columns:
            df['ingestion_date'] = pd.to_datetime(df['ingestion_date']).dt.date
        if 'ingestion_timestamp' in df.columns:
            df['ingestion_timestamp'] = pd.to_datetime(df['ingestion_timestamp'])
        
        # Ensure all string columns have consistent schema (replace NaN with empty string, then back to None)
        # This prevents schema inconsistencies where some partitions have null type instead of string
        for col in df.columns:
            if df[col].dtype == 'object' and col not in partition_cols:
                # Check if this is actually a date/datetime column
                if col in ['ingestion_date']:
                    continue  # Skip date columns
                # Fill NaN with empty string temporarily
                df[col] = df[col].fillna('')
                # Convert empty strings back to None for proper null handling
                df[col] = df[col].replace('', None)
        
        # Define explicit schema to ensure consistency across partitions
        schema_fields = []
        for col in df.columns:
            # Note: Partition columns need to be in the schema for write_to_dataset
            
            # Special handling for known date columns
            if col == 'ingestion_date':
                schema_fields.append(pa.field(col, pa.date32(), nullable=True))
            elif col == 'ingestion_timestamp':
                schema_fields.append(pa.field(col, pa.timestamp('us'), nullable=True))
            elif df[col].dtype == 'object':
                # String type (nullable)
                schema_fields.append(pa.field(col, pa.string(), nullable=True))
            elif df[col].dtype == 'float64':
                # Double type (nullable)
                schema_fields.append(pa.field(col, pa.float64(), nullable=True))
            elif df[col].dtype == 'int64':
                # Int64 type (nullable)
                schema_fields.append(pa.field(col, pa.int64(), nullable=True))
            elif df[col].dtype == 'bool':
                # Boolean type (nullable)
                schema_fields.append(pa.field(col, pa.bool_(), nullable=True))
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                # Timestamp type
                schema_fields.append(pa.field(col, pa.timestamp('us'), nullable=True))
            else:
                # Default to string for unknown types
                schema_fields.append(pa.field(col, pa.string(), nullable=True))
        
        # Create schema
        schema = pa.schema(schema_fields)
        
        # Write partitioned Parquet with explicit schema
        table = pa.Table.from_pandas(df, schema=schema, preserve_index=False)
        
        pq.write_to_dataset(
            table,
            root_path=str(output_dir),
            partition_cols=partition_cols,
            compression='snappy',
            use_dictionary=False,  # Disable dictionary encoding to avoid issues
            write_statistics=False,  # Disable statistics to avoid corruption
            existing_data_behavior='overwrite_or_ignore'
        )
        
        # Generate statistics
        stats = {
            "status": "success",
            "total_records": len(df),
            "partition_columns": partition_cols,
            "unique_countries": df['country'].nunique() if 'country' in df.columns else 0,
            "unique_states": df['state'].nunique() if 'state' in df.columns else 0,
            "brewery_types": df['brewery_type'].value_counts().to_dict() if 'brewery_type' in df.columns else {},
            "records_with_coordinates": int(df['has_coordinates'].sum()) if 'has_coordinates' in df.columns else 0,
            "records_with_complete_address": int(df['has_complete_address'].sum()) if 'has_complete_address' in df.columns else 0,
            "output_path": str(output_dir),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Silver layer transformation complete: {len(df)} records written to {output_dir}")
        logger.info(f"   Partitioned by: {partition_cols}")
        logger.info(f"   Unique countries: {stats['unique_countries']}")
        logger.info(f"   Unique states: {stats['unique_states']}")
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Silver layer transformation failed: {e}")
        raise SilverLayerError(f"Failed to transform to silver layer: {e}")


if __name__ == "__main__":
    # Test the module
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python silver_layer.py <input_path> <output_path> [partition_col1 partition_col2 ...]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    partition_cols = sys.argv[3:] if len(sys.argv) > 3 else None
    
    try:
        result = transform_to_silver(input_path, output_path, partition_cols)
        print(f"Silver layer transformation complete: {result}")
    except SilverLayerError as e:
        print(f"Silver layer transformation failed: {e}")
        sys.exit(1)

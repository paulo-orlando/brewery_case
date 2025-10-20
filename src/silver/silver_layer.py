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
    
    replacements = {
        'Ã¤': 'ä', 'Ã¶': 'ö', 'Ã¼': 'ü', 'ÃŸ': 'ß',
        'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ã³': 'ó', 'Ãº': 'ú', 'Ã±': 'ñ',
        'Ã ': 'à', 'Ã¨': 'è', 'Ã¬': 'ì', 'Ã²': 'ò', 'Ã¹': 'ù',
        'Ã§': 'ç', 'Ã£': 'ã', 'Ãµ': 'õ',
        'Ã‰': 'É', 'Ã': 'Á', 'Ã"': 'Ó',
        'K�rnten': 'Kärnten',
        '�': ''
    }
    
    result = text
    for wrong, correct in replacements.items():
        result = result.replace(wrong, correct)
    
    try:
        if '�' in result:
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
    
    df = df.copy()
    
    df.columns = df.columns.str.lower().str.replace(' ', '_')
    
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].replace('', None)
            df[col] = df[col].replace('null', None)
    
    text_columns = ['name', 'city', 'state', 'state_province', 'country', 
                    'address_1', 'address_2', 'address_3', 'street']
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: fix_encoding(x) if pd.notna(x) else x)
    
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
    
    if 'state_province' in df.columns and 'state' in df.columns:
        df['state'] = df['state'].fillna(df['state_province'])
    
    df['ingestion_date'] = datetime.utcnow().date()
    df['ingestion_timestamp'] = datetime.utcnow()
    
    df['location_key'] = df['country'] + '_' + df['state']
    
    if 'latitude' in df.columns:
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    if 'longitude' in df.columns:
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    
    address_cols = ['address_1', 'city', 'state', 'postal_code']
    available_cols = [col for col in address_cols if col in df.columns]
    if available_cols:
        df['has_complete_address'] = df[available_cols].notna().all(axis=1)
    
    if 'latitude' in df.columns and 'longitude' in df.columns:
        df['has_coordinates'] = df[['latitude', 'longitude']].notna().all(axis=1)
    
    if 'id' in df.columns:
        initial_count = len(df)
        df = df.drop_duplicates(subset=['id'], keep='last')
        duplicates_removed = initial_count - len(df)
        if duplicates_removed > 0:
            logger.warning(f"Removed {duplicates_removed} duplicate records")
    
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
        
        if not input_dir.exists():
            raise SilverLayerError(f"Input path does not exist: {input_path}")
        
        json_files = list(input_dir.glob("*.json"))
        
        if not json_files:
            raise SilverLayerError(f"No JSON files found in {input_path}")
        
        logger.info(f"Found {len(json_files)} JSON file(s) to process")
        
        all_records = []
        
        for json_file in json_files:
            logger.info(f"Reading {json_file.name}")
            
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
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
        
        df = pd.DataFrame(all_records)
        
        df = clean_and_transform_data(df)
        
        missing_cols = [col for col in partition_cols if col not in df.columns]
        if missing_cols:
            logger.warning(f"Partition columns not found in data: {missing_cols}. Available columns: {df.columns.tolist()}")
            raise SilverLayerError(f"Partition columns not found in data: {missing_cols}. Available columns: {df.columns.tolist()}")
        
        logger.info(f"DataFrame has {len(df)} records with columns: {df.columns.tolist()}")
        logger.info(f"Partition columns verified: {partition_cols}")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        df = df.reset_index(drop=True)
        
        if 'ingestion_date' in df.columns:
            df['ingestion_date'] = pd.to_datetime(df['ingestion_date']).dt.date
        if 'ingestion_timestamp' in df.columns:
            df['ingestion_timestamp'] = pd.to_datetime(df['ingestion_timestamp'])
        
        for col in df.columns:
            if df[col].dtype == 'object' and col not in partition_cols:
                if col in ['ingestion_date']:
                    continue
                df[col] = df[col].fillna('')
                df[col] = df[col].replace('', None)
        
        schema_fields = []
        for col in df.columns:
            if col == 'ingestion_date':
                schema_fields.append(pa.field(col, pa.date32(), nullable=True))
            elif col == 'ingestion_timestamp':
                schema_fields.append(pa.field(col, pa.timestamp('us'), nullable=True))
            elif df[col].dtype == 'object':
                schema_fields.append(pa.field(col, pa.string(), nullable=True))
            elif df[col].dtype == 'float64':
                schema_fields.append(pa.field(col, pa.float64(), nullable=True))
            elif df[col].dtype == 'int64':
                schema_fields.append(pa.field(col, pa.int64(), nullable=True))
            elif df[col].dtype == 'bool':
                schema_fields.append(pa.field(col, pa.bool_(), nullable=True))
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                schema_fields.append(pa.field(col, pa.timestamp('us'), nullable=True))
            else:
                schema_fields.append(pa.field(col, pa.string(), nullable=True))
        
        schema = pa.schema(schema_fields)
        
        table = pa.Table.from_pandas(df, schema=schema, preserve_index=False)
        
        pq.write_to_dataset(
            table,
            root_path=str(output_dir),
            partition_cols=partition_cols,
            compression='snappy',
            use_dictionary=False,
            write_statistics=False,
            existing_data_behavior='overwrite_or_ignore'
        )
        
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

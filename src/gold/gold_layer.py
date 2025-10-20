"""
Gold layer: Analytical aggregations.
Creates aggregated views for business intelligence and analytics.
"""
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import logging
import pandas as pd
import pyarrow.parquet as pq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GoldLayerError(Exception):
    """Custom exception for gold layer errors."""
    pass


def create_gold_aggregations(
    input_path: str,
    output_path: str,
    aggregation_type: str = "type_location"
) -> Dict[str, Any]:
    """
    Create aggregated views from silver layer data.
    
    Creates the following aggregations:
    1. Breweries by type and location (country, state)
    2. Additional metrics: avg coordinates, address completeness, etc.
    
    Args:
        input_path: Silver layer input directory (partitioned Parquet)
        output_path: Gold layer output directory
        aggregation_type: Type of aggregation to create
        
    Returns:
        Dictionary with operation metadata
        
    Raises:
        GoldLayerError: If aggregation fails
    """
    try:
        input_dir = Path(input_path)
        output_dir = Path(output_path)
        
        # Validate input
        if not input_dir.exists():
            raise GoldLayerError(f"Input path does not exist: {input_path}")
        
        # Read silver layer data (partitioned Parquet)
        logger.info(f"Reading silver layer data from {input_dir}")
        
        try:
            # Use pandas to read partitioned Parquet with schema unification
            import pandas as pd
            import pyarrow.parquet as pq
            
            # Read the entire partitioned dataset - pandas handles schema differences
            df = pd.read_parquet(str(input_dir), engine='pyarrow', use_nullable_dtypes=False)
            
            logger.info(f"Successfully loaded {len(df)} records from silver layer")
            logger.info(f"Columns: {list(df.columns)}")
            
        except Exception as e:
            logger.error(f"Failed to read partitioned Parquet with dataset API: {e}")
            logger.info("Falling back to manual partition reading...")
            
            try:
                # Fallback: Read files manually and extract partition info from paths
                import pyarrow.parquet as pq
                import pyarrow as pa
                
                parquet_files = list(input_dir.rglob('*.parquet'))
                if not parquet_files:
                    raise GoldLayerError("No Parquet files found in silver layer")
                
                logger.info(f"Found {len(parquet_files)} Parquet file(s) to read")
                
                dataframes = []
                
                for i, pq_file in enumerate(parquet_files):
                    try:
                        # Read directly to pandas to avoid schema concatenation issues
                        df_temp = pd.read_parquet(pq_file, engine='pyarrow')
                        
                        # Extract partition values from path
                        # Path format: .../country=USA/state=California/file.parquet
                        parts = pq_file.parts
                        partition_info = {}
                        
                        for part in parts:
                            if '=' in part:
                                key, value = part.split('=', 1)
                                partition_info[key] = value
                        
                        # Add partition columns
                        for key, value in partition_info.items():
                            df_temp[key] = value
                        
                        dataframes.append(df_temp)
                        
                        if (i + 1) % 20 == 0:
                            logger.info(f"Processed {i + 1}/{len(parquet_files)} files...")
                            
                    except Exception as file_error:
                        logger.warning(f"Skipping file {pq_file.name}: {file_error}")
                        continue
                
                if not dataframes:
                    raise GoldLayerError("No valid Parquet files could be read")
                
                # Concatenate all dataframes (pandas handles schema differences better)
                logger.info(f"Concatenating {len(dataframes)} dataframes...")
                df = pd.concat(dataframes, ignore_index=True)
                
                logger.info(f"Successfully loaded {len(df)} records from silver layer")
                logger.info(f"Columns: {list(df.columns)}")
                
            except Exception as fallback_error:
                raise GoldLayerError(f"Failed to read silver layer Parquet: {fallback_error}")
        
        if df.empty:
            raise GoldLayerError("No data found in silver layer")
        
        logger.info(f"Loaded {len(df)} records from silver layer")
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create primary aggregation: breweries by type and location
        agg_df = create_type_location_aggregation(df)
        
        # Save aggregation with timestamp (date and time for uniqueness)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"breweries_by_type_location_{timestamp}.parquet"
        
        agg_df.to_parquet(
            output_file,
            compression='snappy',
            index=False
        )
        
        logger.info(f"✅ Saved aggregation to {output_file}")
        
        # Also save as CSV for easy viewing with proper UTF-8 encoding
        csv_file = output_dir / f"breweries_by_type_location_{timestamp}.csv"
        agg_df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        logger.info(f"✅ Saved CSV version to {csv_file}")
        
        # Create additional summary statistics
        summary = create_summary_statistics(df)
        summary_file = output_dir / f"summary_statistics_{timestamp}.json"
        
        import json
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Saved summary statistics to {summary_file}")
        
        result = {
            "status": "success",
            "aggregation_type": aggregation_type,
            "source_records": len(df),
            "aggregated_rows": len(agg_df),
            "output_files": {
                "parquet": str(output_file),
                "csv": str(csv_file),
                "summary": str(summary_file)
            },
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Gold layer aggregation complete: {len(agg_df)} aggregated rows")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Gold layer aggregation failed: {e}")
        raise GoldLayerError(f"Failed to create gold layer aggregations: {e}")


def create_type_location_aggregation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create aggregation by brewery type and location.
    
    Args:
        df: Silver layer DataFrame
        
    Returns:
        Aggregated DataFrame with counts by type and location
    """
    logger.info("Creating type and location aggregation")
    
    # Ensure required columns exist
    required_cols = ['brewery_type', 'country', 'state']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise GoldLayerError(f"Missing required columns for aggregation: {missing_cols}")
    
    # Group by type, country, and state
    agg_df = df.groupby(['country', 'state', 'brewery_type']).agg(
        brewery_count=('id', 'count'),
        unique_cities=('city', 'nunique'),
        avg_latitude=('latitude', 'mean'),
        avg_longitude=('longitude', 'mean'),
        pct_with_coordinates=('has_coordinates', lambda x: (x.sum() / len(x) * 100) if len(x) > 0 else 0),
        pct_with_address=('has_complete_address', lambda x: (x.sum() / len(x) * 100) if len(x) > 0 else 0)
    ).reset_index()
    
    # Round numeric columns
    agg_df['avg_latitude'] = agg_df['avg_latitude'].round(4)
    agg_df['avg_longitude'] = agg_df['avg_longitude'].round(4)
    agg_df['pct_with_coordinates'] = agg_df['pct_with_coordinates'].round(2)
    agg_df['pct_with_address'] = agg_df['pct_with_address'].round(2)
    
    # Sort by country, state, and brewery count
    agg_df = agg_df.sort_values(['country', 'state', 'brewery_count'], ascending=[True, True, False])
    
    # Add aggregation metadata
    agg_df['aggregation_date'] = datetime.utcnow().date()
    
    logger.info(f"Created aggregation with {len(agg_df)} rows")
    
    return agg_df


def create_summary_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Create summary statistics from silver layer data.
    
    Args:
        df: Silver layer DataFrame
        
    Returns:
        Dictionary with summary statistics
    """
    logger.info("Creating summary statistics")
    
    stats = {
        "total_breweries": len(df),
        "unique_countries": int(df['country'].nunique()) if 'country' in df.columns else 0,
        "unique_states": int(df['state'].nunique()) if 'state' in df.columns else 0,
        "unique_cities": int(df['city'].nunique()) if 'city' in df.columns else 0,
        "brewery_types": df['brewery_type'].value_counts().to_dict() if 'brewery_type' in df.columns else {},
        "top_10_states": df['state'].value_counts().head(10).to_dict() if 'state' in df.columns else {},
        "top_10_cities": df['city'].value_counts().head(10).to_dict() if 'city' in df.columns else {},
        "data_quality": {
            "records_with_coordinates": int(df['has_coordinates'].sum()) if 'has_coordinates' in df.columns else 0,
            "pct_with_coordinates": float((df['has_coordinates'].sum() / len(df) * 100).round(2)) if 'has_coordinates' in df.columns and len(df) > 0 else 0,
            "records_with_complete_address": int(df['has_complete_address'].sum()) if 'has_complete_address' in df.columns else 0,
            "pct_with_complete_address": float((df['has_complete_address'].sum() / len(df) * 100).round(2)) if 'has_complete_address' in df.columns and len(df) > 0 else 0
        },
        "generated_at": datetime.utcnow().isoformat()
    }
    
    return stats


if __name__ == "__main__":
    # Test the module
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python gold_layer.py <input_path> <output_path>")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    try:
        result = create_gold_aggregations(input_path, output_path)
        print(f"Gold layer aggregation complete: {result}")
    except GoldLayerError as e:
        print(f"Gold layer aggregation failed: {e}")
        sys.exit(1)

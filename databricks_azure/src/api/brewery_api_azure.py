"""
Brewery API extraction module for Databricks + Azure Blob Storage.
Handles data fetching from Open Brewery DB with retry logic and error handling.
Saves data directly to Azure Blob Storage.
"""
import requests
import json
from typing import List, Dict, Any
from datetime import datetime
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

# Databricks/Spark imports
from pyspark.sql import SparkSession

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BreweryAPIError(Exception):
    """Custom exception for brewery API errors."""
    pass


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def fetch_page(page: int, per_page: int = 200, base_url: str = "https://api.openbrewerydb.org/v1/breweries") -> List[Dict[str, Any]]:
    """
    Fetch a single page of brewery data with retry logic.
    
    Args:
        page: Page number to fetch
        per_page: Number of records per page (max 200)
        base_url: API base URL
        
    Returns:
        List of brewery dictionaries
        
    Raises:
        HTTPError: If API returns error status code
        RequestException: For network-related errors
    """
    params = {"page": page, "per_page": per_page}
    logger.info(f"Fetching page {page} from brewery API")
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Successfully fetched page {page}: {len(data)} records")
        return data
    except requests.HTTPError as e:
        logger.error(f"HTTP error on page {page}: {e}")
        raise
    except requests.RequestException as e:
        logger.error(f"Request error on page {page}: {e}")
        raise


def fetch_brewery_data_to_azure(
    spark: SparkSession,
    base_url: str,
    output_path: str,
    per_page: int = 200
) -> Dict[str, Any]:
    """
    Fetch all brewery data from API and save to Azure Blob Storage.
    
    Args:
        spark: Active SparkSession
        base_url: API base URL
        output_path: Azure Blob Storage path (abfss:// or /mnt/)
        per_page: Records per page
        
    Returns:
        Dictionary with metadata about the extraction
        
    Raises:
        BreweryAPIError: If extraction fails after retries
    """
    try:
        # Fetch all pages
        all_breweries = []
        page = 1
        empty_pages = 0
        
        while True:
            try:
                data = fetch_page(page, per_page, base_url)
                
                if not data:
                    empty_pages += 1
                    if empty_pages >= 2:  # Stop after 2 consecutive empty pages
                        logger.info("Reached end of data (2 consecutive empty pages)")
                        break
                else:
                    empty_pages = 0
                    all_breweries.extend(data)
                
                page += 1
                
            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                if page == 1:  # Critical error on first page
                    raise BreweryAPIError(f"Failed to fetch initial data: {e}")
                break
        
        if not all_breweries:
            raise BreweryAPIError("No data fetched from API")
        
        # Create metadata
        timestamp = datetime.utcnow()
        timestamp_str = timestamp.isoformat()
        execution_date = timestamp.strftime('%Y-%m-%d')
        
        # Prepare data with metadata
        extraction_metadata = {
            "extraction_timestamp": timestamp_str,
            "execution_date": execution_date,
            "total_records": len(all_breweries),
            "api_url": base_url,
            "records": all_breweries
        }
        
        # Save to Azure Blob Storage using Spark
        output_file = f"{output_path}/breweries_{timestamp.strftime('%Y-%m-%dT%H-%M-%S')}.json"
        
        # Convert to RDD and save as JSON
        json_str = json.dumps(extraction_metadata, indent=2, ensure_ascii=False)
        rdd = spark.sparkContext.parallelize([json_str])
        rdd.saveAsTextFile(output_file)
        
        logger.info(f"✅ Successfully extracted {len(all_breweries)} breweries to {output_file}")
        
        return {
            "status": "success",
            "records_extracted": len(all_breweries),
            "output_file": output_file,
            "timestamp": timestamp_str,
            "execution_date": execution_date
        }
        
    except BreweryAPIError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during extraction: {e}")
        raise BreweryAPIError(f"Extraction failed: {e}")


# For Databricks notebook usage
def extract_to_azure_notebook(spark, config):
    """
    Convenience function for Databricks notebooks.
    
    Args:
        spark: SparkSession from notebook
        config: Configuration dictionary or module
        
    Returns:
        Extraction result dictionary
    """
    from datetime import datetime
    
    base_url = getattr(config, 'BREWERY_API_URL', 'https://api.openbrewerydb.org/v1/breweries')
    execution_date = datetime.utcnow().strftime('%Y-%m-%d')
    
    # Use mounted path or ABFS path
    if hasattr(config, 'DATABRICKS_MOUNT_POINT_RAW'):
        output_path = f"{config.DATABRICKS_MOUNT_POINT_RAW}/{execution_date}"
    else:
        output_path = f"{config.ABFS_RAW_PATH}{execution_date}"
    
    return fetch_brewery_data_to_azure(
        spark=spark,
        base_url=base_url,
        output_path=output_path,
        per_page=getattr(config, 'PER_PAGE', 200)
    )


if __name__ == "__main__":
    # For local testing (requires Spark session)
    print("This module requires a Spark session. Use in Databricks notebook.")
    print("Example usage:")
    print("  result = extract_to_azure_notebook(spark, config)")

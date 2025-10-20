"""
Brewery API extraction module.
Handles data fetching from Open Brewery DB with retry logic and error handling.
"""
import requests
import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError
from requests.exceptions import HTTPError, RequestException

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
    except HTTPError as e:
        logger.error(f"HTTP error on page {page}: {e}")
        raise
    except RequestException as e:
        logger.error(f"Request error on page {page}: {e}")
        raise


def fetch_brewery_data(base_url: str, output_path: str, per_page: int = 200) -> Dict[str, Any]:
    """
    Fetch all brewery data from API and save to output path.
    
    Args:
        base_url: API base URL
        output_path: Directory path to save raw JSON data
        per_page: Records per page
        
    Returns:
        Dictionary with metadata about the extraction
        
    Raises:
        BreweryAPIError: If extraction fails after retries
    """
    try:
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        all_breweries = []
        page = 1
        empty_pages = 0
        
        while True:
            try:
                data = fetch_page(page, per_page, base_url)
                
                if not data:
                    empty_pages += 1
                    if empty_pages >= 2:  
                        logger.info("Reached end of data (2 consecutive empty pages)")
                        break
                else:
                    empty_pages = 0
                    all_breweries.extend(data)
                
                page += 1
                
                if page > 1000:
                    logger.warning("Reached safety limit of 1000 pages")
                    break
                    
            except (HTTPError, RequestException) as e:
                if page == 1:
                    raise BreweryAPIError(f"Failed to fetch first page: {e}")
                else:
                    logger.warning(f"Failed to fetch page {page}, stopping pagination: {e}")
                    break
        
        if not all_breweries:
            raise BreweryAPIError("No data retrieved from API")
        
        timestamp = datetime.utcnow().isoformat()
        output_file = output_dir / f"breweries_{timestamp.replace(':', '-')}.json"
        
        data_package = {
            "metadata": {
                "extraction_timestamp": timestamp,
                "total_records": len(all_breweries),
                "source_url": base_url,
                "pages_fetched": page - 1
            },
            "data": all_breweries
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data_package, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Successfully extracted {len(all_breweries)} breweries to {output_file}")
        
        return {
            "status": "success",
            "records_extracted": len(all_breweries),
            "output_file": str(output_file),
            "timestamp": timestamp
        }
        
    except Exception as e:
        logger.error(f"❌ Extraction failed: {e}")
        raise BreweryAPIError(f"Failed to extract brewery data: {e}")


if __name__ == "__main__":
    import sys
    
    output_path = sys.argv[1] if len(sys.argv) > 1 else "./data/raw"
    
    try:
        result = fetch_brewery_data(
            base_url="https://api.openbrewerydb.org/v1/breweries",
            output_path=output_path
        )
        print(f"Extraction complete: {result}")
    except BreweryAPIError as e:
        print(f"Extraction failed: {e}")
        sys.exit(1)

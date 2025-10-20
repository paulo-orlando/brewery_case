"""
Unit tests for bronze layer module.
"""
import pytest
import json
from pathlib import Path
from src.bronze.bronze_layer import (
    save_to_bronze,
    validate_bronze_data,
    BronzeLayerError
)


@pytest.fixture
def sample_raw_data(tmp_path):
    """Create sample raw data file."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    
    data = {
        "metadata": {
            "extraction_timestamp": "2025-01-01T00:00:00",
            "total_records": 2
        },
        "data": [
            {
                "id": "test-1",
                "name": "Test Brewery 1",
                "brewery_type": "micro"
            },
            {
                "id": "test-2",
                "name": "Test Brewery 2",
                "brewery_type": "brewpub"
            }
        ]
    }
    
    json_file = raw_dir / "breweries_test.json"
    with open(json_file, 'w') as f:
        json.dump(data, f)
    
    return str(raw_dir)


@pytest.fixture
def bronze_output_dir(tmp_path):
    """Create bronze output directory."""
    return str(tmp_path / "bronze")


class TestSaveToBronze:
    """Tests for save_to_bronze function."""
    
    def test_save_to_bronze_success(self, sample_raw_data, bronze_output_dir):
        """Test successful bronze layer save."""
        result = save_to_bronze(sample_raw_data, bronze_output_dir)
        
        assert result["status"] == "success"
        assert result["total_records"] == 2
        assert result["files_processed"] == 1
        
        bronze_dir = Path(bronze_output_dir)
        json_files = list(bronze_dir.glob("*.json"))
        assert len(json_files) == 1
        
        with open(json_files[0], 'r') as f:
            data = json.load(f)
        
        assert "bronze_metadata" in data
        assert "data" in data
        assert len(data["data"]) == 2
    
    def test_save_to_bronze_no_input(self, bronze_output_dir):
        """Test error when input path doesn't exist."""
        with pytest.raises(BronzeLayerError, match="does not exist"):
            save_to_bronze("/nonexistent/path", bronze_output_dir)
    
    def test_save_to_bronze_no_json_files(self, tmp_path, bronze_output_dir):
        """Test error when no JSON files found."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        
        with pytest.raises(BronzeLayerError, match="No JSON files found"):
            save_to_bronze(str(empty_dir), bronze_output_dir)


class TestValidateBronzeData:
    """Tests for validate_bronze_data function."""
    
    def test_validate_bronze_data_success(self, tmp_path):
        """Test successful validation."""
        bronze_file = tmp_path / "bronze_test.json"
        data = {
            "bronze_metadata": {
                "ingestion_timestamp": "2025-01-01T00:00:00",
                "record_count": 1
            },
            "data": [{"id": "test-1", "name": "Test"}]
        }
        
        with open(bronze_file, 'w') as f:
            json.dump(data, f)
        
        result = validate_bronze_data(str(bronze_file))
        
        assert result["valid"] is True
        assert result["record_count"] == 1
    
    def test_validate_bronze_data_missing_keys(self, tmp_path):
        """Test validation failure for missing keys."""
        bronze_file = tmp_path / "bronze_invalid.json"
        data = {"data": [{"id": "test"}]} 
        
        with open(bronze_file, 'w') as f:
            json.dump(data, f)
        
        result = validate_bronze_data(str(bronze_file))
        
        assert result["valid"] is False
        assert "Missing required keys" in result["error"]

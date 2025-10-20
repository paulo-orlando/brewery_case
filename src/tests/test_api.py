"""
Unit tests for API extraction module.
"""
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.api.brewery_api import (
    fetch_page,
    fetch_brewery_data,
    BreweryAPIError
)


@pytest.fixture
def sample_brewery_data():
    """Sample brewery API response."""
    return [
        {
            "id": "test-brewery-1",
            "name": "Test Brewery 1",
            "brewery_type": "micro",
            "city": "San Francisco",
            "state": "California",
            "country": "United States"
        },
        {
            "id": "test-brewery-2",
            "name": "Test Brewery 2",
            "brewery_type": "brewpub",
            "city": "Portland",
            "state": "Oregon",
            "country": "United States"
        }
    ]


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory."""
    return str(tmp_path / "test_output")


class TestFetchPage:
    """Tests for fetch_page function."""
    
    @patch('src.api.brewery_api.requests.get')
    def test_fetch_page_success(self, mock_get, sample_brewery_data):
        """Test successful page fetch."""
        mock_response = Mock()
        mock_response.json.return_value = sample_brewery_data
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = fetch_page(1, per_page=200)
        
        assert result == sample_brewery_data
        mock_get.assert_called_once()
    
    @patch('src.api.brewery_api.requests.get')
    def test_fetch_page_http_error(self, mock_get):
        """Test HTTP error handling."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 500")
        mock_get.return_value = mock_response
        
        with pytest.raises(Exception):
            fetch_page(1)
    
    @patch('src.api.brewery_api.requests.get')
    def test_fetch_page_empty_response(self, mock_get):
        """Test empty response handling."""
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = fetch_page(1)
        
        assert result == []


class TestFetchBreweryData:
    """Tests for fetch_brewery_data function."""
    
    @patch('src.api.brewery_api.fetch_page')
    def test_fetch_brewery_data_success(self, mock_fetch_page, sample_brewery_data, temp_output_dir):
        """Test successful data extraction."""
        mock_fetch_page.side_effect = [
            sample_brewery_data,
            sample_brewery_data,
            [],
            []
        ]
        
        result = fetch_brewery_data(
            base_url="https://api.test.com",
            output_path=temp_output_dir
        )
        
        assert result["status"] == "success"
        assert result["records_extracted"] == 4  
        
        output_dir = Path(temp_output_dir)
        json_files = list(output_dir.glob("*.json"))
        assert len(json_files) == 1
        
        with open(json_files[0], 'r') as f:
            data = json.load(f)
        
        assert "metadata" in data
        assert "data" in data
        assert len(data["data"]) == 4
    
    @patch('src.api.brewery_api.fetch_page')
    def test_fetch_brewery_data_no_data(self, mock_fetch_page, temp_output_dir):
        """Test error when no data retrieved."""
        mock_fetch_page.return_value = []
        
        with pytest.raises(BreweryAPIError, match="No data retrieved"):
            fetch_brewery_data(
                base_url="https://api.test.com",
                output_path=temp_output_dir
            )
    
    @patch('src.api.brewery_api.fetch_page')
    def test_fetch_brewery_data_first_page_fails(self, mock_fetch_page, temp_output_dir):
        """Test error when first page fails."""
        mock_fetch_page.side_effect = Exception("Network error")
        
        with pytest.raises(BreweryAPIError):
            fetch_brewery_data(
                base_url="https://api.test.com",
                output_path=temp_output_dir
            )

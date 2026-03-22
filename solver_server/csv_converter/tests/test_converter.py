"""
Tests for CSV Converter Module
Author: Muhammad Bhutta
"""

import pytest
import os
from solver_server.csv_converter.converter import CSVConverter, CSVConversionResult


def test_converter_initialization():
    """Test converter can be initialized"""
    converter = CSVConverter()
    assert converter.temp_dir is not None
    converter.cleanup()


def test_valid_conversion():
    """Test conversion with valid CSV data"""
    converter = CSVConverter()
    
    data = {
        "preferences_csv": "section,faculty,score\nCSC150,Alice,3\n",
        "time_blocks_csv": "section,pattern,start_time\nCSC150,MWF,08:00\n",
        "workload_csv": "faculty,min,max\nAlice,1,2\n"
    }
    
    result = converter.convert_from_json(data)
    
    assert result.success is True
    assert os.path.exists(result.preferences_path)
    assert os.path.exists(result.time_blocks_path)
    assert os.path.exists(result.workload_path)
    
    converter.cleanup()


def test_missing_data():
    """Test conversion fails with missing data"""
    converter = CSVConverter()
    
    data = {
        "preferences_csv": "section,faculty,score\n"
        # Missing time_blocks_csv and workload_csv
    }
    
    result = converter.convert_from_json(data)
    
    assert result.success is False
    assert "Missing required" in result.error_message
    
    converter.cleanup()


def test_cleanup():
    """Test cleanup removes temporary directory"""
    converter = CSVConverter()
    temp_dir = converter.temp_dir
    
    assert os.path.exists(temp_dir)
    
    converter.cleanup()
    
    assert not os.path.exists(temp_dir)

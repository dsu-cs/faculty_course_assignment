"""
Tests for CSV Converter Module
Author: Muhammad Bhutta
Updated: March 29, 2026 - To match PR #24 format
"""

import pytest
import os
from solver_server.csv_converter.converter import CSVConverter, CSVConversionResult


def test_converter_initialization():
    """Test converter can be initialized"""
    converter = CSVConverter()
    assert converter.temp_dir is not None
    converter.cleanup()


def test_valid_conversion_with_all_files():
    """Test conversion with all CSV files (including optional workload)"""
    converter = CSVConverter()
    
    # PR #24 format with title rows
    data = {
        "sections_csv": "Sections\nCRN,Sub,Num,Seq,Crd,Desc,Seats,Waitlist,Days,Time,Room,Faculty,Current Workload\n71464,INFS,890,D01,1,Seminar,19/25,0,W,1100-1150,East Hall 201,,5\n",
        "time_blocks_csv": "Time\nCRN,Sub,Days,Start Time,End Time,Room\n71464,INFS,W,11:00,11:50,East Hall 201\n",
        "preferences_csv": "Preferences\nCRN,Alice,Bob\n71464,3,1\n",
        "workload_csv": "Workload\nFaculty,Research Units\nAlice,15\n"
    }
    
    result = converter.convert_from_json(data)
    
    assert result.success is True
    assert os.path.exists(result.sections_path)
    assert os.path.exists(result.preferences_path)
    assert os.path.exists(result.time_blocks_path)
    assert os.path.exists(result.workload_path)
    
    # Verify content was written correctly
    with open(result.sections_path, 'r') as f:
        content = f.read()
        assert "Sections" in content
        assert "CRN,Sub,Num" in content
    
    converter.cleanup()


def test_valid_conversion_without_workload():
    """Test conversion works without optional workload.csv"""
    converter = CSVConverter()
    
    data = {
        "sections_csv": "Sections\nCRN,Sub,Num,Seq,Crd,Desc,Seats,Waitlist,Days,Time,Room,Faculty,Current Workload\n71464,INFS,890,D01,1,Seminar,19/25,0,W,1100-1150,East Hall 201,,5\n",
        "time_blocks_csv": "Time\nCRN,Sub,Days,Start Time,End Time,Room\n71464,INFS,W,11:00,11:50,East Hall 201\n",
        "preferences_csv": "Preferences\nCRN,Alice,Bob\n71464,3,1\n"
    }
    
    result = converter.convert_from_json(data)
    
    assert result.success is True
    assert os.path.exists(result.sections_path)
    assert os.path.exists(result.preferences_path)
    assert os.path.exists(result.time_blocks_path)
    assert result.workload_path == ""
    
    converter.cleanup()


def test_missing_required_data():
    """Test conversion fails when required data is missing"""
    converter = CSVConverter()
    
    data = {
        "sections_csv": "Sections\nCRN,Sub,Num\n"
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
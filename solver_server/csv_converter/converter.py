"""
CSV Converter Module
Converts JSON data from Communications Server to CSV files for Anto's solver

Author: Muhammad Bhutta
Feature: CSV to CSP Converter
Manager: Anto Shibu
"""

import csv
import tempfile
import os
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class CSVConversionResult:
    """Result of CSV conversion operation"""
    success: bool
    preferences_path: str = ""
    time_blocks_path: str = ""
    workload_path: str = ""
    error_message: str = ""
    temp_dir: str = ""


class CSVConverter:
    """Converts JSON data to CSV files for the solver"""
    
    def __init__(self, temp_dir: str = None):
        """Initialize converter with optional temp directory"""
        self.temp_dir = temp_dir or tempfile.mkdtemp()
        
    def convert_from_json(self, data: Dict) -> CSVConversionResult:
        """
        Convert JSON data to CSV files
        
        Args:
            data: Dictionary with keys:
                - preferences_csv: CSV string or list of dicts
                - time_blocks_csv: CSV string or list of dicts
                - workload_csv: CSV string or list of dicts
        
        Returns:
            CSVConversionResult with file paths or error
        """
        try:
            # Validate input
            if not self._validate_input(data):
                return CSVConversionResult(
                    success=False,
                    error_message="Missing required CSV data fields"
                )
            
            # Create file paths
            preferences_path = os.path.join(self.temp_dir, 'preferences.csv')
            time_blocks_path = os.path.join(self.temp_dir, 'time_blocks.csv')
            workload_path = os.path.join(self.temp_dir, 'workload.csv')
            
            # Write CSV files
            self._write_csv_file(preferences_path, data['preferences_csv'])
            self._write_csv_file(time_blocks_path, data['time_blocks_csv'])
            self._write_csv_file(workload_path, data['workload_csv'])
            
            return CSVConversionResult(
                success=True,
                preferences_path=preferences_path,
                time_blocks_path=time_blocks_path,
                workload_path=workload_path,
                temp_dir=self.temp_dir
            )
            
        except Exception as e:
            return CSVConversionResult(
                success=False,
                error_message=f"Conversion failed: {str(e)}"
            )
    
    def _validate_input(self, data: Dict) -> bool:
        """Validate that all required CSV data is present"""
        required = ['preferences_csv', 'time_blocks_csv', 'workload_csv']
        return all(key in data for key in required)
    
    def _write_csv_file(self, filepath: str, csv_data: str):
        """Write CSV string to file"""
        with open(filepath, 'w', newline='') as f:
            f.write(csv_data)
    
    def cleanup(self):
        """Clean up temporary directory"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

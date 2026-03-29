"""
CSV Converter Module
Converts JSON data from Communications Server to CSV files for Anto's solver

Author: Muhammad Bhutta
Feature: CSV to CSP Converter
Manager: Anto Shibu
Updated: March 29, 2026 - To match PR #24 format
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
    sections_path: str = ""
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
        Convert JSON data to CSV files matching PR #24 format
        
        Args:
            data: Dictionary with keys:
                - sections_csv: CSV string (REQUIRED)
                - preferences_csv: CSV string (REQUIRED)
                - time_blocks_csv: CSV string (REQUIRED)
                - workload_csv: CSV string (OPTIONAL)
        
        Returns:
            CSVConversionResult with file paths or error
        """
        try:
            # Validate input - sections, preferences, and time_blocks are required
            if not self._validate_input(data):
                return CSVConversionResult(
                    success=False,
                    error_message="Missing required CSV data fields (sections_csv, preferences_csv, time_blocks_csv)"
                )
            
            # Create file paths
            sections_path = os.path.join(self.temp_dir, 'sections.csv')
            preferences_path = os.path.join(self.temp_dir, 'preferences.csv')
            time_blocks_path = os.path.join(self.temp_dir, 'time_blocks.csv')
            workload_path = os.path.join(self.temp_dir, 'workload.csv')
            
            # Write CSV files
            self._write_csv_file(sections_path, data['sections_csv'])
            self._write_csv_file(preferences_path, data['preferences_csv'])
            self._write_csv_file(time_blocks_path, data['time_blocks_csv'])
            
            # Workload is optional
            if 'workload_csv' in data and data['workload_csv']:
                self._write_csv_file(workload_path, data['workload_csv'])
            else:
                workload_path = ""
            
            return CSVConversionResult(
                success=True,
                sections_path=sections_path,
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
        # PR #24 format: sections, preferences, and time_blocks are REQUIRED
        # workload is OPTIONAL
        required = ['sections_csv', 'preferences_csv', 'time_blocks_csv']
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
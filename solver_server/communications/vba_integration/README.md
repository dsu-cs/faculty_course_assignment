# VBA Integration Module

Excel VBA code to call the Communications Server API.

## Author
Muhammad Bhutta (Manager - Communications Feature)

## For
Lindsey Crow (Developer - Communications Feature)

## Files
- SolverAPI.bas - Main VBA module with API functions

## Installation

1. Open Excel workbook
2. Press Alt+F11 to open VBA Editor
3. Go to File > Import File
4. Select SolverAPI.bas
5. Module will appear in your project

## Usage

### Test the Connection
```vb
Sub TestConnection()
    SolverAPI.TestAPI
End Sub
```

This will:
- Check if server is running
- Send sample data
- Show response in message box

### Use in Your Code
```vb
' Check server is running
If SolverAPI.CheckServerHealth() Then
    
    ' Build CSV strings from your Excel data
    Dim prefCSV As String
    Dim timeCSV As String  
    Dim workCSV As String
    
    ' TODO: Build CSV from Excel sheets
    prefCSV = BuildPreferencesCSV()
    timeCSV = BuildTimeBlocksCSV()
    workCSV = BuildWorkloadCSV()
    
    ' Call solver
    Dim response As String
    response = SolverAPI.CallSolver(prefCSV, timeCSV, workCSV)
    
    ' Parse response and update Excel
    ParseAndDisplayResults response
    
End If
```

## API Details

See API_SPEC.md for complete endpoint documentation.

## Server Must Be Running

Before using this module, the Flask server must be running:
- Local: http://localhost:5000
- Production: Update API_BASE_URL in SolverAPI.bas

## Next Steps for Lindsey

1. Import SolverAPI.bas into workbook
2. Test with TestAPI() function
3. Build functions to read Excel data into CSV format
4. Build functions to parse JSON response
5. Build functions to write results to Excel

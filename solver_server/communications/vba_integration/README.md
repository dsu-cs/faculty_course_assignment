# Complete VBA Integration for Excel Workbook

Complete Excel VBA integration for Faculty Course Assignment Solver.

## Author
Muhammad Bhutta (Manager - Communications Feature)

## For
Lindsey Crow (Developer - Communications Feature)

## Files

1. SolverAPI.bas - API communication module
2. ExcelDataHelper.bas - Excel data reader and CSV builder
3. MainController.bas - Main orchestrator

## Excel Workbook Structure

Your workbook needs these sheets:

1. Preferences - Faculty preferences
   - Column A: Section
   - Column B: Faculty
   - Column C: Score (0-3 or X)

2. TimeBlocks - Section meeting times
   - Column A: Section
   - Column B: Pattern (MWF, TTh, MW)
   - Column C: Start Time (HH:MM)

3. Workload - Faculty min/max load
   - Column A: Faculty
   - Column B: Min sections
   - Column C: Max sections

4. Results - Output sheet (auto-created)

## Installation

1. Open your Excel workbook
2. Press Alt+F11 to open VBA Editor
3. Go to File > Import File
4. Import all three .bas files:
   - SolverAPI.bas
   - ExcelDataHelper.bas
   - MainController.bas

## Usage

### Option 1: Run from VBA

Press Alt+F11, then in Immediate Window:
```vb
MainController.RunSolver
```

### Option 2: Add Button to Excel

1. Developer tab > Insert > Button
2. Assign macro: MainController.RunSolver
3. Click button to run solver

### Option 3: Quick Test
```vb
MainController.QuickTest
```

## Complete Workflow

1. User fills data in Preferences, TimeBlocks, Workload sheets
2. User clicks "Run Solver" button
3. VBA checks server is running
4. VBA reads Excel data and builds CSV strings
5. VBA calls API POST /solve endpoint
6. API calls Anto's solver
7. Solver returns assignments
8. VBA writes results to Results sheet
9. User sees assignments

## Server Requirements

Flask server must be running:
- Local development: http://localhost:5000
- Production: Update API_BASE_URL in SolverAPI.bas

Start server:
```bash
python solver_server/communications/server.py
```

## Troubleshooting

- "Server not running" - Start Flask server first
- "Error reading data" - Check sheet names match exactly
- "Invalid JSON" - Check data has no special characters

## Next Steps

1. Create sample Excel workbook with correct sheet structure
2. Import all three VBA modules
3. Add data to sheets
4. Test with Quick Test first
5. Run full solver with RunSolver

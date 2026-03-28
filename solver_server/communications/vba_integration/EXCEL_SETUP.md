# Excel Workbook Setup Instructions

Complete guide to create the Faculty Course Assignment workbook.

## Step 1: Create New Workbook

1. Open Excel
2. Create new blank workbook
3. Save as: FacultyCourseAssignment.xlsm (macro-enabled)

## Step 2: Import Sample Data

Import the three CSV files from sample_data folder:

1. Data > Get Data > From File > From Text/CSV
2. Import preferences_sample.csv to sheet named "Preferences"
3. Import time_blocks_sample.csv to sheet named "TimeBlocks"
4. Import workload_sample.csv to sheet named "Workload"
5. Create empty sheet named "Results"

## Step 3: Import VBA Modules

1. Press Alt+F11 (open VBA Editor)
2. File > Import File
3. Import these three files:
   - SolverAPI.bas
   - ExcelDataHelper.bas
   - MainController.bas

## Step 4: Add Run Button

1. Go to Developer tab (enable if needed: File > Options > Customize Ribbon > Developer)
2. Insert > Button (Form Control)
3. Draw button on sheet
4. Assign macro: MainController.RunSolver
5. Label button: "Generate Course Assignments"

## Step 5: Test

1. Click "Generate Course Assignments" button
2. If server not running, you'll get error
3. Start server: python solver_server/communications/server.py
4. Click button again
5. Check Results sheet for output

## Done

Workbook is ready for Lindsey to customize and integrate with actual DSU data.

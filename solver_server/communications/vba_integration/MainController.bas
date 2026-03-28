Attribute VB_Name = "MainController"
' Main Controller Module
' Orchestrates the complete Excel to Solver workflow
' Author: Muhammad Bhutta (Manager - Communications Feature)

Option Explicit

' Main function - call this from a button or menu
Public Sub RunSolver()
    On Error GoTo ErrorHandler
    
    ' Step 1: Check server is running
    If Not SolverAPI.CheckServerHealth() Then
        MsgBox "Solver server is not running. Please start the server first.", vbCritical, "Server Not Running"
        Exit Sub
    End If
    
    ' Step 2: Build CSV data from Excel sheets
    Dim prefCSV As String
    Dim timeCSV As String
    Dim workCSV As String
    
    prefCSV = ExcelDataHelper.BuildPreferencesCSV("Preferences")
    timeCSV = ExcelDataHelper.BuildTimeBlocksCSV("TimeBlocks")
    workCSV = ExcelDataHelper.BuildWorkloadCSV("Workload")
    
    ' Step 3: Call solver API
    Dim response As String
    response = SolverAPI.CallSolver(prefCSV, timeCSV, workCSV)
    
    ' Step 4: Write results to Excel
    ExcelDataHelper.WriteResultsToSheet response, "Results"
    
    ' Step 5: Notify user
    MsgBox "Solver completed successfully. Check Results sheet.", vbInformation, "Success"
    
    Exit Sub
    
ErrorHandler:
    MsgBox "Error running solver: " & Err.Description, vbCritical, "Error"
End Sub

' Quick test with sample data
Public Sub QuickTest()
    SolverAPI.TestAPI
End Sub

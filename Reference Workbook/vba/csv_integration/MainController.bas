Attribute VB_Name = "MainController"
' Main Controller Module
' Orchestrates the current Excel to Solver workflow
' Current workbook structure:
'   - Sections
'   - Time
'   - Preferences

Option Explicit

' Main function - call this from a button or menu
Public Sub RunSolver()
    On Error GoTo ErrorHandler
    
    ' Step 1: Check server is running
    If Not SolverAPI.CheckServerHealth() Then
        MsgBox "Solver server is not running. Please start the server first.", vbCritical, "Server Not Running"
        Exit Sub
    End If
    
    ' Step 2: Build CSV data from current workbook sheets
    Dim prefCSV As String
    Dim timeCSV As String
    Dim sectionsCSV As String
    
    prefCSV = ExcelDataHelper.BuildPreferencesCSV("Preferences")
    timeCSV = ExcelDataHelper.BuildTimeBlocksCSV("Time")
    sectionsCSV = ExcelDataHelper.BuildSectionsCSV("Sections")
    
    ' Step 3: Call solver API
    Dim response As String
    response = SolverAPI.CallSolver(prefCSV, timeCSV, sectionsCSV)
    
    ' Step 4: Notify user based on response
    If Len(response) >= 6 And Left$(response, 6) = "ERROR:" Then
        MsgBox "Solver request failed." & vbCrLf & vbCrLf & _
               "Server error response:" & vbCrLf & Left$(response, 500), _
               vbCritical, "Solver Error"
        Exit Sub
    End If
    
    MsgBox "Solver request completed successfully." & vbCrLf & vbCrLf & _
           "Server response preview:" & vbCrLf & Left$(response, 500), _
           vbInformation, "Success"
    
    Exit Sub
    
ErrorHandler:
    MsgBox "Error running solver: " & Err.Description, vbCritical, "Error"
End Sub

' Quick test with sample data
Public Sub QuickTest()
    SolverAPI.TestAPI
End Sub


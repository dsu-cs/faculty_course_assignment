Attribute VB_Name = "SolverAPI"
' Faculty Course Assignment Solver API Module
' Author: Muhammad Bhutta (Manager - Communications Feature)
' Purpose: VBA integration with Flask Communications Server
' For: Lindsey Crow (Developer - Communications Feature)

Option Explicit

' API Configuration
Private Const API_BASE_URL As String = "http://localhost:5000"
Private Const API_SOLVE_ENDPOINT As String = "/solve"
Private Const API_HEALTH_ENDPOINT As String = "/health"

' Check if solver server is running
Public Function CheckServerHealth() As Boolean
    On Error GoTo ErrorHandler
    
    Dim http As Object
    Set http = CreateObject("MSXML2.XMLHTTP")
    
    http.Open "GET", API_BASE_URL & API_HEALTH_ENDPOINT, False
    http.send
    
    If http.Status = 200 Then
        CheckServerHealth = True
        Debug.Print "Server is healthy"
    Else
        CheckServerHealth = False
        Debug.Print "Server health check failed: " & http.Status
    End If
    
    Exit Function
    
ErrorHandler:
    CheckServerHealth = False
    Debug.Print "Error checking server health: " & Err.Description
End Function

' Main function to call solver
Public Function CallSolver(preferencesCSV As String, timeBlocksCSV As String, workloadCSV As String) As String
    On Error GoTo ErrorHandler
    
    Dim http As Object
    Set http = CreateObject("MSXML2.XMLHTTP")
    
    ' Build JSON request
    Dim jsonRequest As String
    jsonRequest = BuildJSONRequest(preferencesCSV, timeBlocksCSV, workloadCSV)
    
    ' Send POST request
    http.Open "POST", API_BASE_URL & API_SOLVE_ENDPOINT, False
    http.setRequestHeader "Content-Type", "application/json"
    http.send jsonRequest
    
    ' Return response
    If http.Status = 200 Then
        CallSolver = http.responseText
        Debug.Print "Solver call successful"
    Else
        CallSolver = "ERROR: " & http.Status & " - " & http.responseText
        Debug.Print "Solver call failed: " & http.Status
    End If
    
    Exit Function
    
ErrorHandler:
    CallSolver = "ERROR: " & Err.Description
    Debug.Print "Error calling solver: " & Err.Description
End Function

' Helper function to build JSON request
Private Function BuildJSONRequest(preferencesCSV As String, timeBlocksCSV As String, workloadCSV As String) As String
    Dim runID As String
    runID = "run_" & Format(Now, "yyyymmdd_hhnnss")
    
    ' Escape CSV data for JSON
    Dim prefJSON As String
    Dim timeJSON As String
    Dim workJSON As String
    
    prefJSON = EscapeJSONString(preferencesCSV)
    timeJSON = EscapeJSONString(timeBlocksCSV)
    workJSON = EscapeJSONString(workloadCSV)
    
    ' Build JSON
    BuildJSONRequest = "{" & _
        """run_id"": """ & runID & """," & _
        """preferences_csv"": """ & prefJSON & """," & _
        """time_blocks_csv"": """ & timeJSON & """," & _
        """workload_csv"": """ & workJSON & """" & _
End Function

    result = text
    
    ' Escape special characters
    result = Replace(result, "\", "\\")
    result = Replace(result, """", "\""")
    result = Replace(result, vbCrLf, "\n")
    result = Replace(result, vbCr, "\n")
    result = Replace(result, vbLf, "\n")
    
    EscapeJSONString = result
End Function

' Example: Test the API with sample data
Public Sub TestAPI()
    ' Check server health first
    If Not CheckServerHealth() Then
        MsgBox "Solver server is not running!", vbCritical
        Exit Sub
    End If
    
    ' Sample CSV data
    Dim prefCSV As String
    Dim timeCSV As String
    Dim workCSV As String
    
    prefCSV = "section,faculty,score" & vbCrLf & _
              "CSC150,Alice,3" & vbCrLf & _
              "CSC150,Bob,1" & vbCrLf & _
              "CSC250,Alice,2" & vbCrLf & _
              "CSC250,Bob,3"
    
    timeCSV = "section,pattern,start_time" & vbCrLf & _
              "CSC150,MWF,08:00" & vbCrLf & _
              "CSC250,TTh,10:00"
    
    workCSV = "faculty,min,max" & vbCrLf & _
              "Alice,1,2" & vbCrLf & _
              "Bob,1,2"
    
    ' Call solver
    Dim response As String
    response = CallSolver(prefCSV, timeCSV, workCSV)
    
    ' Show response
    MsgBox response, vbInformation, "Solver Response"
End Sub' Helper function to escape strings for JSON
Private Function EscapeJSONString(text As String) As String
    Dim result As String


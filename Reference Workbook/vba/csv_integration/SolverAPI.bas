Attribute VB_Name = "SolverAPI"
' Faculty Course Assignment Solver API Module
' Updated to match current workbook/controller flow:
'   - preferences_csv
'   - time_blocks_csv
'   - sections_csv

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
Public Function CallSolver(preferencesCSV As String, timeBlocksCSV As String, sectionsCSV As String) As String
    On Error GoTo ErrorHandler
    
    Dim http As Object
    Set http = CreateObject("MSXML2.XMLHTTP")
    
    ' Build JSON request
    Dim jsonRequest As String
    jsonRequest = BuildJSONRequest(preferencesCSV, timeBlocksCSV, sectionsCSV)
    
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
Private Function BuildJSONRequest(preferencesCSV As String, timeBlocksCSV As String, sectionsCSV As String) As String
    Dim runID As String
    runID = "run_" & Format(Now, "yyyymmdd_hhnnss")
    
    Dim prefJSON As String
    Dim timeJSON As String
    Dim sectionsJSON As String
    
    prefJSON = EscapeJSONString(preferencesCSV)
    timeJSON = EscapeJSONString(timeBlocksCSV)
    sectionsJSON = EscapeJSONString(sectionsCSV)
    
    BuildJSONRequest = "{" & _
        """run_id"":""" & runID & """," & _
        """preferences_csv"":""" & prefJSON & """," & _
        """time_blocks_csv"":""" & timeJSON & """," & _
        """sections_csv"":""" & sectionsJSON & """" & _
        "}"
End Function

' Helper function to escape strings for JSON
Private Function EscapeJSONString(text As String) As String
    Dim result As String
    result = text
    
    result = Replace(result, "\", "\\")
    result = Replace(result, """", "\""")
    result = Replace(result, vbCrLf, "\n")
    result = Replace(result, vbCr, "\n")
    result = Replace(result, vbLf, "\n")
    
    EscapeJSONString = result
End Function

' Example: Test the API with sample data
Public Sub TestAPI()
    If Not CheckServerHealth() Then
        MsgBox "Solver server is not running!", vbCritical
        Exit Sub
    End If
    
    Dim prefCSV As String
    Dim timeCSV As String
    Dim sectionsCSV As String
    
    prefCSV = "section_id,Faculty A,Faculty B" & vbCrLf & _
              "10001,3,x" & vbCrLf & _
              "10002,2,1"
    
    timeCSV = "section_id,pattern,start_time,end_time,room" & vbCrLf & _
              "10001,MWF,09:00,09:50,EH 101" & vbCrLf & _
              "10002,TuTh,11:00,12:15,EH 102"
    
    sectionsCSV = "section_id,subject,course_number,sequence,credits,title,current_seats,max_seats,waitlist,faculty" & vbCrLf & _
                  "10001,CSC,105,D01,3,Intro to Computing,20,24,0," & vbCrLf & _
                  "10002,CSC,105,D02,3,Intro to Computing,18,24,1,"
    
    Dim response As String
    response = CallSolver(prefCSV, timeCSV, sectionsCSV)
    
    MsgBox response, vbInformation, "Solver Response"
End Sub


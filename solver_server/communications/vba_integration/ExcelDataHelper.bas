Attribute VB_Name = "ExcelDataHelper"
' Excel Data Helper Module
' Reads data from Excel sheets and builds CSV strings for solver
' Author: Muhammad Bhutta (Manager - Communications Feature)

Option Explicit

' Build preferences CSV from Excel sheet
Public Function BuildPreferencesCSV(sheetName As String) As String
    Dim ws As Worksheet
    Set ws = ThisWorkbook.Sheets(sheetName)
    
    Dim csv As String
    csv = "section,faculty,score" & vbCrLf
    
    Dim lastRow As Long
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    
    Dim i As Long
    For i = 2 To lastRow
        Dim section As String
        Dim faculty As String
        Dim score As String
        
        section = Trim(ws.Cells(i, 1).Value)
        faculty = Trim(ws.Cells(i, 2).Value)
        score = Trim(ws.Cells(i, 3).Value)
        
        If section <> "" And faculty <> "" And score <> "" Then
            csv = csv & section & "," & faculty & "," & score & vbCrLf
        End If
    Next i
    
    BuildPreferencesCSV = csv
End Function

' Build time blocks CSV from Excel sheet
Public Function BuildTimeBlocksCSV(sheetName As String) As String
    Dim ws As Worksheet
    Set ws = ThisWorkbook.Sheets(sheetName)
    
    Dim csv As String
    csv = "section,pattern,start_time" & vbCrLf
    
    Dim lastRow As Long
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    
    Dim i As Long
    For i = 2 To lastRow
        Dim section As String
        Dim pattern As String
        Dim startTime As String
        
        section = Trim(ws.Cells(i, 1).Value)
        pattern = Trim(ws.Cells(i, 2).Value)
        startTime = Trim(ws.Cells(i, 3).Value)
        
        If section <> "" And pattern <> "" And startTime <> "" Then
            csv = csv & section & "," & pattern & "," & startTime & vbCrLf
        End If
    Next i
    
    BuildTimeBlocksCSV = csv
End Function

' Build workload CSV from Excel sheet
Public Function BuildWorkloadCSV(sheetName As String) As String
    Dim ws As Worksheet
    Set ws = ThisWorkbook.Sheets(sheetName)
    
    Dim csv As String
    csv = "faculty,min,max" & vbCrLf
    
    Dim lastRow As Long
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    
    Dim i As Long
    For i = 2 To lastRow
        Dim faculty As String
        Dim minLoad As String
        Dim maxLoad As String
        
        faculty = Trim(ws.Cells(i, 1).Value)
        minLoad = Trim(ws.Cells(i, 2).Value)
        maxLoad = Trim(ws.Cells(i, 3).Value)
        
        If faculty <> "" And minLoad <> "" And maxLoad <> "" Then
            csv = csv & faculty & "," & minLoad & "," & maxLoad & vbCrLf
        End If
    Next i
    
    BuildWorkloadCSV = csv
End Function

' Parse JSON response and write to Excel
Public Sub WriteResultsToSheet(jsonResponse As String, sheetName As String)
    On Error GoTo ErrorHandler
    
    Dim ws As Worksheet
    Set ws = ThisWorkbook.Sheets(sheetName)
    
    ' Clear existing results
    ws.Cells.Clear
    
    ' Write headers
    ws.Cells(1, 1).Value = "Section"
    ws.Cells(1, 2).Value = "Assigned Faculty"
    ws.Cells(1, 3).Value = "Status"
    
    ' Simple JSON parsing - extract assignments
    Dim assignments As String
    assignments = ExtractJSONField(jsonResponse, "assignments")
    
    If assignments <> "" Then
        ws.Cells(2, 1).Value = "Results received"
        ws.Cells(2, 2).Value = "See response below"
        ws.Cells(4, 1).Value = jsonResponse
    Else
        ws.Cells(2, 1).Value = "No results"
        ws.Cells(4, 1).Value = jsonResponse
    End If
    
    Exit Sub
    
ErrorHandler:
    MsgBox "Error writing results: " & Err.Description, vbCritical
End Sub

' Helper to extract field from JSON
Private Function ExtractJSONField(json As String, fieldName As String) As String
    Dim startPos As Long
    Dim endPos As Long
    
    startPos = InStr(json, """" & fieldName & """")
    If startPos > 0 Then
        ExtractJSONField = "found"
    Else
        ExtractJSONField = ""
    End If
End Function

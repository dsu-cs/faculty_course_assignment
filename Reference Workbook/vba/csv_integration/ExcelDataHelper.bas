Attribute VB_Name = "ExcelDataHelper"
' Excel Data Helper Module
' Reads data from the current workbook sheets and builds CSV strings for solver
' Current workbook structure:
'   - Sections
'   - Time
'   - Preferences

Option Explicit

Private Const HEADER_ROW As Long = 2
Private Const FIRST_DATA_ROW As Long = 3

' Build preferences CSV from matrix-style Preferences sheet
' Workbook layout:
'   Row 2: CRN, Faculty1, Faculty2, ...
'   Row 3+: CRN, score1, score2, ...
'
' Output:
'   section_id,Faculty1,Faculty2,...
'   12345,x,2,3,...
Public Function BuildPreferencesCSV(sheetName As String) As String
    Dim ws As Worksheet
    Set ws = ThisWorkbook.Sheets(sheetName)
    
    Dim csv As String
    Dim lastRow As Long
    Dim lastCol As Long
    Dim i As Long
    Dim j As Long
    Dim headerValue As String
    Dim cellValue As String
    Dim crn As String
    
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    lastCol = ws.Cells(HEADER_ROW, ws.Columns.Count).End(xlToLeft).Column
    
    csv = "section_id"
    
    For j = 2 To lastCol
        headerValue = Trim(CStr(ws.Cells(HEADER_ROW, j).Value))
        If headerValue <> "" Then
            csv = csv & "," & EscapeCSV(headerValue)
        End If
    Next j
    csv = csv & vbCrLf
    
    For i = FIRST_DATA_ROW To lastRow
        crn = Trim(CStr(ws.Cells(i, 1).Value))
        
        If crn <> "" Then
            csv = csv & EscapeCSV(crn)
            
            For j = 2 To lastCol
                cellValue = Trim(CStr(ws.Cells(i, j).Value))
                If cellValue = "" Then cellValue = "x"
                csv = csv & "," & EscapeCSV(cellValue)
            Next j
            
            csv = csv & vbCrLf
        End If
    Next i
    
    BuildPreferencesCSV = csv
End Function

' Build time_blocks CSV from current Time sheet
' Workbook layout:
'   A = CRN
'   B = Sub
'   C = Days
'   D = Start Time
'   E = End Time
'   F = Room
'
' Output:
'   section_id,pattern,start_time,end_time,room
Public Function BuildTimeBlocksCSV(sheetName As String) As String
    Dim ws As Worksheet
    Set ws = ThisWorkbook.Sheets(sheetName)
    
    Dim csv As String
    Dim lastRow As Long
    Dim i As Long
    
    Dim crn As String
    Dim pattern As String
    Dim startTime As String
    Dim endTime As String
    Dim room As String
    
    csv = "section_id,pattern,start_time,end_time,room" & vbCrLf
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    
    For i = FIRST_DATA_ROW To lastRow
        crn = Trim(CStr(ws.Cells(i, 1).Value))
        pattern = Trim(CStr(ws.Cells(i, 3).Value))
        startTime = Trim(CStr(ws.Cells(i, 4).Value))
        endTime = Trim(CStr(ws.Cells(i, 5).Value))
        room = Trim(CStr(ws.Cells(i, 6).Value))
        
        If crn <> "" Then
            csv = csv & EscapeCSV(crn) _
                      & "," & EscapeCSV(pattern) _
                      & "," & EscapeCSV(startTime) _
                      & "," & EscapeCSV(endTime) _
                      & "," & EscapeCSV(room) _
                      & vbCrLf
        End If
    Next i
    
    BuildTimeBlocksCSV = csv
End Function

' Build sections CSV from current Sections sheet
' Workbook layout:
'   A = CRN
'   B = Sub
'   C = Num
'   D = Seq
'   E = Crd
'   F = Desc
'   G = Current Seats
'   H = Max Seats
'   I = Waitlist
'   J = Faculty
'
' Output:
'   section_id,subject,course_number,sequence,credits,title,current_seats,max_seats,waitlist,faculty
Public Function BuildSectionsCSV(sheetName As String) As String
    Dim ws As Worksheet
    Set ws = ThisWorkbook.Sheets(sheetName)
    
    Dim csv As String
    Dim lastRow As Long
    Dim i As Long
    
    csv = "section_id,subject,course_number,sequence,credits,title,current_seats,max_seats,waitlist,faculty" & vbCrLf
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    
    For i = FIRST_DATA_ROW To lastRow
        Dim crn As String
        Dim subj As String
        Dim courseNum As String
        Dim seq As String
        Dim credits As String
        Dim title As String
        Dim currentSeats As String
        Dim maxSeats As String
        Dim waitlist As String
        Dim faculty As String
        
        crn = Trim(CStr(ws.Cells(i, 1).Value))
        subj = Trim(CStr(ws.Cells(i, 2).Value))
        courseNum = Trim(CStr(ws.Cells(i, 3).Value))
        seq = Trim(CStr(ws.Cells(i, 4).Value))
        credits = Trim(CStr(ws.Cells(i, 5).Value))
        title = Trim(CStr(ws.Cells(i, 6).Value))
        currentSeats = Trim(CStr(ws.Cells(i, 7).Value))
        maxSeats = Trim(CStr(ws.Cells(i, 8).Value))
        waitlist = Trim(CStr(ws.Cells(i, 9).Value))
        faculty = Trim(CStr(ws.Cells(i, 10).Value))
        
        If crn <> "" Then
            csv = csv & EscapeCSV(crn) _
                      & "," & EscapeCSV(subj) _
                      & "," & EscapeCSV(courseNum) _
                      & "," & EscapeCSV(seq) _
                      & "," & EscapeCSV(credits) _
                      & "," & EscapeCSV(title) _
                      & "," & EscapeCSV(currentSeats) _
                      & "," & EscapeCSV(maxSeats) _
                      & "," & EscapeCSV(waitlist) _
                      & "," & EscapeCSV(faculty) _
                      & vbCrLf
        End If
    Next i
    
    BuildSectionsCSV = csv
End Function

' Escape CSV values only when needed
Private Function EscapeCSV(ByVal valueText As String) As String
    If InStr(valueText, ",") > 0 Or InStr(valueText, """") > 0 Or InStr(valueText, vbCr) > 0 Or InStr(valueText, vbLf) > 0 Then
        valueText = Replace(valueText, """", """""")
        EscapeCSV = """" & valueText & """"
    Else
        EscapeCSV = valueText
    End If
End Function


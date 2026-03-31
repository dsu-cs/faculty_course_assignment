Attribute VB_Name = "AssignmentWriter"
Option Explicit

Private Const SECTIONS_SHEET_NAME As String = "Sections"
Private Const SECTION_CRN_COLUMN As Long = 1      ' Column A
Private Const SECTION_FACULTY_COLUMN As Long = 10 ' Column J
Private Const HEADER_ROW As Long = 2
Private Const FIRST_DATA_ROW As Long = 3

' Main entry point for applying returned assignments into Sections!Faculty
' Expected scheduleCsv format:
'   CRN,Assigned Faculty
'   70346,Erich Matthew Eischen
'   70377,Someone Else
Public Sub ApplyAssignmentsFromCSVText(ByVal scheduleCsv As String)
    On Error GoTo ErrorHandler
    
    Dim crnList As Collection
    Dim facultyList As Collection
    
    Set crnList = New Collection
    Set facultyList = New Collection
    
    ParseScheduleCSV scheduleCsv, crnList, facultyList
    
    If crnList.Count = 0 Then
        MsgBox "No assignments were parsed from schedule.csv.", vbExclamation, "AssignmentWriter"
        Exit Sub
    End If
    
    WriteAssignmentsToSections crnList, facultyList
    
    MsgBox "Assignments applied to Sections successfully.", vbInformation, "AssignmentWriter"
    Exit Sub

ErrorHandler:
    MsgBox "Error applying assignments: " & Err.Description, vbCritical, "AssignmentWriter"
End Sub

' Parse two-column schedule CSV into parallel collections:
'   crnList(i)     = CRN
'   facultyList(i) = Assigned Faculty
Private Sub ParseScheduleCSV(ByVal scheduleCsv As String, ByRef crnList As Collection, ByRef facultyList As Collection)
    Dim normalizedText As String
    normalizedText = Replace(scheduleCsv, vbCrLf, vbLf)
    normalizedText = Replace(normalizedText, vbCr, vbLf)
    
    Dim lines() As String
    lines = Split(normalizedText, vbLf)
    
    Dim i As Long
    For i = LBound(lines) To UBound(lines)
        Dim lineText As String
        lineText = Trim$(lines(i))
        
        If lineText <> "" Then
            If LCase$(Left$(lineText, 3)) <> "crn" Then
                Dim parts() As String
                parts = SplitCSVLine(lineText)
                
                If UBound(parts) >= 1 Then
                    Dim crn As String
                    Dim assignedFaculty As String
                    
                    crn = Trim$(parts(0))
                    assignedFaculty = Trim$(parts(1))
                    
                    If crn <> "" Then
                        crnList.Add crn
                        facultyList.Add assignedFaculty
                    End If
                End If
            End If
        End If
    Next i
End Sub

' Write assignments into Sections!J by matching CRN in Sections!A
Private Sub WriteAssignmentsToSections(ByVal crnList As Collection, ByVal facultyList As Collection)
    Dim ws As Worksheet
    Set ws = ThisWorkbook.Worksheets(SECTIONS_SHEET_NAME)
    
    Dim lastRow As Long
    lastRow = ws.Cells(ws.Rows.Count, SECTION_CRN_COLUMN).End(xlUp).Row
    
    Application.ScreenUpdating = False
    
    Dim i As Long
    For i = FIRST_DATA_ROW To lastRow
        Dim sectionCrn As String
        sectionCrn = Trim$(CStr(ws.Cells(i, SECTION_CRN_COLUMN).Value))
        
        If sectionCrn <> "" Then
            Dim matchedFaculty As String
            matchedFaculty = FindAssignedFaculty(sectionCrn, crnList, facultyList)
            
            If matchedFaculty <> "" Then
                ws.Cells(i, SECTION_FACULTY_COLUMN).Value = matchedFaculty
            End If
        End If
    Next i
    
    Application.ScreenUpdating = True
End Sub

' Find faculty by CRN from the parallel collections
Private Function FindAssignedFaculty(ByVal targetCrn As String, ByVal crnList As Collection, ByVal facultyList As Collection) As String
    Static crnToFaculty As Object              ' Scripting.Dictionary cache: CRN -> Faculty
    Static cachedCrnList As Collection         ' Collections used to build the cache
    Static cachedFacultyList As Collection
    
    Dim i As Long
    Dim key As String
    
    ' Lazily create the dictionary object
    If crnToFaculty Is Nothing Then
        Set crnToFaculty = CreateObject("Scripting.Dictionary")
    End If
    
    ' Rebuild cache if the input collections differ from the cached ones
    If (cachedCrnList Is Nothing) _
       Or Not (cachedCrnList Is crnList) _
       Or Not (cachedFacultyList Is facultyList) Then
        
        crnToFaculty.RemoveAll
        
        For i = 1 To crnList.Count
            key = Trim$(CStr(crnList(i)))
            ' Last occurrence wins if duplicate CRNs exist
            crnToFaculty(key) = Trim$(CStr(facultyList(i)))
        Next i
        
        Set cachedCrnList = crnList
        Set cachedFacultyList = facultyList
    End If
    
    key = Trim$(targetCrn)
    If crnToFaculty.Exists(key) Then
        FindAssignedFaculty = crnToFaculty(key)
    Else
        FindAssignedFaculty = ""
    End If
End Function

' Minimal CSV splitter that supports quoted values with commas
Private Function SplitCSVLine(ByVal lineText As String) As String()
    Dim values As Collection
    Set values = New Collection
    
    Dim currentValue As String
    currentValue = ""
    
    Dim inQuotes As Boolean
    inQuotes = False
    
    Dim i As Long
    For i = 1 To Len(lineText)
        Dim ch As String
        ch = Mid$(lineText, i, 1)
        
        Select Case ch
            Case """"
                If inQuotes And i < Len(lineText) And Mid$(lineText, i + 1, 1) = """" Then
                    currentValue = currentValue & """"
                    i = i + 1
                Else
                    inQuotes = Not inQuotes
                End If
                
            Case ","
                If inQuotes Then
                    currentValue = currentValue & ch
                Else
                    values.Add currentValue
                    currentValue = ""
                End If
                
            Case Else
                currentValue = currentValue & ch
        End Select
    Next i
    
    values.Add currentValue
    
    Dim result() As String
    ReDim result(0 To values.Count - 1)
    
    For i = 1 To values.Count
        result(i - 1) = values(i)
    Next i
    
    SplitCSVLine = result
End Function

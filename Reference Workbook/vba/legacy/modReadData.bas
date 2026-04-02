Attribute VB_Name = "modReadData"
Option Explicit

Public Function ReadSectionsJsonArray() As String
    Dim ws As Worksheet
    Dim lastRow As Long
    Dim r As Long
    Dim cSectionID As Long, cCourse As Long, cTitle As Long
    Dim cCredits As Long, cMaxSeats As Long, cLevel As Long, cDept As Long
    Dim json As String

    Set ws = ThisWorkbook.Worksheets("Sections")
    lastRow = GetLastRow(ws, 1)

    cSectionID = GetHeaderColumn(ws, "Section ID")
    cCourse = GetHeaderColumn(ws, "Course #")
    cTitle = GetHeaderColumn(ws, "Course Title")
    cCredits = GetHeaderColumn(ws, "Credits")
    cMaxSeats = GetHeaderColumn(ws, "Max Seats")
    cLevel = GetHeaderColumn(ws, "Level")
    cDept = GetHeaderColumn(ws, "Department")

    json = "["

    For r = FIRST_DATA_ROW To lastRow
        If NzText(ws.Cells(r, cSectionID).value) <> "" Then
            json = json & "{"
            json = json & """sectionId"":" & JsonString(ws.Cells(r, cSectionID).value) & ","
            json = json & """courseNumber"":" & JsonString(ws.Cells(r, cCourse).value) & ","
            json = json & """courseTitle"":" & JsonString(ws.Cells(r, cTitle).value) & ","
            json = json & """credits"":" & JsonNumber(ws.Cells(r, cCredits).value) & ","
            json = json & """maxSeats"":" & JsonNumber(ws.Cells(r, cMaxSeats).value) & ","
            json = json & """level"":" & JsonString(ws.Cells(r, cLevel).value) & ","
            json = json & """department"":" & JsonString(ws.Cells(r, cDept).value)
            json = json & "},"
        End If
    Next r

    If Right$(json, 1) = "," Then json = Left$(json, Len(json) - 1)
    json = json & "]"

    ReadSectionsJsonArray = json
End Function

Public Function ReadTimeBlocksJsonArray() As String
    Dim ws As Worksheet
    Dim lastRow As Long
    Dim r As Long
    Dim cSectionID As Long, cDays As Long, cStart As Long, cEnd As Long, cRoom As Long
    Dim json As String

    Set ws = ThisWorkbook.Worksheets("Time Blocks")
    lastRow = GetLastRow(ws, 1)

    cSectionID = GetHeaderColumn(ws, "Section ID")
    cDays = GetHeaderColumn(ws, "Days")
    cStart = GetHeaderColumn(ws, "Start Time")
    cEnd = GetHeaderColumn(ws, "End Time")
    cRoom = GetHeaderColumn(ws, "Room")

    json = "["

    For r = FIRST_DATA_ROW To lastRow
        If NzText(ws.Cells(r, cSectionID).value) <> "" Then
            json = json & "{"
            json = json & """sectionId"":" & JsonString(ws.Cells(r, cSectionID).value) & ","
            json = json & """days"":" & JsonString(ws.Cells(r, cDays).value) & ","
            json = json & """startTime"":" & JsonString(ws.Cells(r, cStart).value) & ","
            json = json & """endTime"":" & JsonString(ws.Cells(r, cEnd).value) & ","
            json = json & """room"":" & JsonString(ws.Cells(r, cRoom).value)
            json = json & "},"
        End If
    Next r

    If Right$(json, 1) = "," Then json = Left$(json, Len(json) - 1)
    json = json & "]"

    ReadTimeBlocksJsonArray = json
End Function

Public Function ReadFacultyJsonArrayFromPreferences() As String
    Dim ws As Worksheet
    Dim lastCol As Long
    Dim c As Long
    Dim json As String

    Set ws = ThisWorkbook.Worksheets("Preferences")
    lastCol = GetLastCol(ws, HEADER_ROW)

    json = "["

    For c = 2 To lastCol
        If NzText(ws.Cells(HEADER_ROW, c).value) <> "" Then
            json = json & "{"
            json = json & """facultyName"":" & JsonString(ws.Cells(HEADER_ROW, c).value)
            json = json & "},"
        End If
    Next c

    If Right$(json, 1) = "," Then json = Left$(json, Len(json) - 1)
    json = json & "]"

    ReadFacultyJsonArrayFromPreferences = json
End Function

Public Function ReadPreferencesJsonArray() As String
    Dim ws As Worksheet
    Dim lastRow As Long, lastCol As Long
    Dim r As Long, c As Long
    Dim sectionId As String, facultyName As String
    Dim json As String

    Set ws = ThisWorkbook.Worksheets("Preferences")
    lastRow = GetLastRow(ws, 1)
    lastCol = GetLastCol(ws, HEADER_ROW)

    json = "["

    For r = FIRST_DATA_ROW To lastRow
        sectionId = NzText(ws.Cells(r, 1).value)

        If sectionId <> "" Then
            For c = 2 To lastCol
                facultyName = NzText(ws.Cells(HEADER_ROW, c).value)

                If facultyName <> "" Then
                    json = json & "{"
                    json = json & """sectionId"":" & JsonString(sectionId) & ","
                    json = json & """facultyName"":" & JsonString(facultyName) & ","
                    json = json & """score"":" & JsonNumber(ws.Cells(r, c).value)
                    json = json & "},"
                End If
            Next c
        End If
    Next r

    If Right$(json, 1) = "," Then json = Left$(json, Len(json) - 1)
    json = json & "]"

    ReadPreferencesJsonArray = json
End Function

Public Function ReadWorkloadJsonArray() As String
    Dim ws As Worksheet
    Dim lastRow As Long
    Dim r As Long
    Dim cFaculty As Long, cMin As Long, cMax As Long, cType As Long, cNotes As Long
    Dim json As String

    Set ws = ThisWorkbook.Worksheets("Workload")
    lastRow = GetLastRow(ws, 1)

    cFaculty = GetHeaderColumn(ws, "Faculty Name")
    cMin = GetHeaderColumn(ws, "Min Sections")
    cMax = GetHeaderColumn(ws, "Max Sections")
    cType = GetHeaderColumn(ws, "Type")
    cNotes = GetHeaderColumn(ws, "Notes")

    json = "["

    For r = FIRST_DATA_ROW To lastRow
        If NzText(ws.Cells(r, cFaculty).value) <> "" Then
            json = json & "{"
            json = json & """facultyName"":" & JsonString(ws.Cells(r, cFaculty).value) & ","
            json = json & """minSections"":" & JsonNumber(ws.Cells(r, cMin).value) & ","
            json = json & """maxSections"":" & JsonNumber(ws.Cells(r, cMax).value) & ","
            json = json & """facultyType"":" & JsonString(ws.Cells(r, cType).value) & ","
            json = json & """notes"":" & JsonString(ws.Cells(r, cNotes).value)
            json = json & "},"
        End If
    Next r

    If Right$(json, 1) = "," Then json = Left$(json, Len(json) - 1)
    json = json & "]"

    ReadWorkloadJsonArray = json
End Function

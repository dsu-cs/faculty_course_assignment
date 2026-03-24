Attribute VB_Name = "modJSONParser"
Option Explicit

Private Function ExtractJsonValue(ByVal jsonText As String, ByVal keyName As String) As String
    Dim token As String
    Dim startPos As Long
    Dim valuePos As Long
    Dim endPos As Long
    Dim rawValue As String

    token = """" & keyName & """:"
    startPos = InStr(1, jsonText, token, vbTextCompare)
    If startPos = 0 Then Exit Function

    valuePos = startPos + Len(token)

    Do While valuePos <= Len(jsonText) And Mid$(jsonText, valuePos, 1) = " "
        valuePos = valuePos + 1
    Loop

    If valuePos > Len(jsonText) Then Exit Function

    If Mid$(jsonText, valuePos, 1) = """" Then
        valuePos = valuePos + 1
        endPos = InStr(valuePos, jsonText, """")
        If endPos > 0 Then
            rawValue = Mid$(jsonText, valuePos, endPos - valuePos)
        End If
    Else
        endPos = InStr(valuePos, jsonText, ",")
        If endPos = 0 Then endPos = InStr(valuePos, jsonText, "}")
        If endPos > 0 Then
            rawValue = Mid$(jsonText, valuePos, endPos - valuePos)
        End If
    End If

    ExtractJsonValue = Trim$(rawValue)
End Function

Private Function ExtractAssignmentsBlock(ByVal jsonText As String) As String
    Dim token As String
    Dim startPos As Long
    Dim arrayStart As Long
    Dim depth As Long
    Dim i As Long
    Dim ch As String

    token = """assignments"":["
    startPos = InStr(1, jsonText, token, vbTextCompare)
    If startPos = 0 Then Exit Function

    arrayStart = startPos + Len(token) - 1

    depth = 0
    For i = arrayStart To Len(jsonText)
        ch = Mid$(jsonText, i, 1)

        If ch = "[" Then
            depth = depth + 1
        ElseIf ch = "]" Then
            depth = depth - 1
            If depth = 0 Then
                ExtractAssignmentsBlock = Mid$(jsonText, arrayStart + 1, i - arrayStart - 1)
                Exit Function
            End If
        End If
    Next i
End Function

Private Function FindScheduleRow(ByVal ws As Worksheet, ByVal sectionId As String) As Long
    Dim lastRow As Long
    Dim r As Long

    lastRow = GetLastRow(ws, 1)

    For r = FIRST_DATA_ROW To lastRow
        If NzText(ws.Cells(r, 1).value) = sectionId Then
            FindScheduleRow = r
            Exit Function
        End If
    Next r
End Function

Private Function FindFacultyColumn(ByVal ws As Worksheet, ByVal facultyName As String, ByVal rowSumCol As Long) As Long
    Dim c As Long

    For c = 2 To rowSumCol - 1
        If StrComp(NzText(ws.Cells(HEADER_ROW, c).value), facultyName, vbTextCompare) = 0 Then
            FindFacultyColumn = c
            Exit Function
        End If
    Next c
End Function

Public Function ParseAndApplySolverResponse(ByVal responseText As String) As Long
    Dim ws As Worksheet
    Dim rowSumCol As Long
    Dim blockText As String
    Dim parts() As String
    Dim i As Long
    Dim itemText As String
    Dim sectionId As String
    Dim facultyName As String
    Dim scheduleRow As Long
    Dim facultyCol As Long

    Set ws = ThisWorkbook.Worksheets("Schedule")
    rowSumCol = GetHeaderColumn(ws, "Row Sum")

    ClearScheduleAssignmentsOnly
    blockText = ExtractAssignmentsBlock(responseText)

    If Trim$(blockText) = "" Then
        AddMessage "WARNING", "ParseAndApplySolverResponse", "NO_ASSIGNMENTS", _
            "No assignments array was found in the solver response."
        Exit Function
    End If

    parts = Split(blockText, "},{")

    For i = LBound(parts) To UBound(parts)
        itemText = parts(i)

        If Left$(itemText, 1) <> "{" Then itemText = "{" & itemText
        If Right$(itemText, 1) <> "}" Then itemText = itemText & "}"

        sectionId = ExtractJsonValue(itemText, "sectionId")
        facultyName = ExtractJsonValue(itemText, "facultyName")

        scheduleRow = FindScheduleRow(ws, sectionId)
        facultyCol = FindFacultyColumn(ws, facultyName, rowSumCol)

        If scheduleRow > 0 And facultyCol > 0 Then
            ws.Cells(scheduleRow, facultyCol).value = 1
            ws.Cells(scheduleRow, rowSumCol).Formula = "=SUM(" & _
                ws.Cells(scheduleRow, 2).Address(False, False) & ":" & _
                ws.Cells(scheduleRow, rowSumCol - 1).Address(False, False) & ")"
            ParseAndApplySolverResponse = ParseAndApplySolverResponse + 1
        Else
            AddMessage "WARNING", "ParseAndApplySolverResponse", "ASSIGNMENT_SKIPPED", _
                "Assignment could not be applied.", _
                "Section=" & sectionId & "; Faculty=" & facultyName
        End If
    Next i
End Function


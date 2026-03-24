Attribute VB_Name = "modResultsWriter"
Option Explicit

Private Function GetCourseTitleBySection(ByVal sectionId As String) As String
    Dim ws As Worksheet
    Dim lastRow As Long
    Dim r As Long
    Dim cSectionID As Long, cCourseTitle As Long

    Set ws = ThisWorkbook.Worksheets("Sections")
    lastRow = GetLastRow(ws, 1)

    cSectionID = GetHeaderColumn(ws, "Section ID")
    cCourseTitle = GetHeaderColumn(ws, "Course Title")

    For r = FIRST_DATA_ROW To lastRow
        If NzText(ws.Cells(r, cSectionID).value) = sectionId Then
            GetCourseTitleBySection = NzText(ws.Cells(r, cCourseTitle).value)
            Exit Function
        End If
    Next r

    GetCourseTitleBySection = ""
End Function

Private Function GetDaysBySection(ByVal sectionId As String) As String
    Dim ws As Worksheet
    Dim lastRow As Long
    Dim r As Long
    Dim cSectionID As Long, cDays As Long

    Set ws = ThisWorkbook.Worksheets("Time Blocks")
    lastRow = GetLastRow(ws, 1)

    cSectionID = GetHeaderColumn(ws, "Section ID")
    cDays = GetHeaderColumn(ws, "Days")

    For r = FIRST_DATA_ROW To lastRow
        If NzText(ws.Cells(r, cSectionID).value) = sectionId Then
            GetDaysBySection = NzText(ws.Cells(r, cDays).value)
            Exit Function
        End If
    Next r

    GetDaysBySection = ""
End Function

Private Function GetTimeBySection(ByVal sectionId As String) As String
    Dim ws As Worksheet
    Dim lastRow As Long
    Dim r As Long
    Dim cSectionID As Long, cStart As Long, cEnd As Long
    Dim startTxt As String, endTxt As String

    Set ws = ThisWorkbook.Worksheets("Time Blocks")
    lastRow = GetLastRow(ws, 1)

    cSectionID = GetHeaderColumn(ws, "Section ID")
    cStart = GetHeaderColumn(ws, "Start Time")
    cEnd = GetHeaderColumn(ws, "End Time")

    For r = FIRST_DATA_ROW To lastRow
        If NzText(ws.Cells(r, cSectionID).value) = sectionId Then
            startTxt = NzText(ws.Cells(r, cStart).Text)
            endTxt = NzText(ws.Cells(r, cEnd).Text)
            GetTimeBySection = startTxt & " - " & endTxt
            Exit Function
        End If
    Next r

    GetTimeBySection = ""
End Function

Private Function GetAssignedFacultyBySection(ByVal sectionId As String) As String
    Dim ws As Worksheet
    Dim lastRow As Long
    Dim rowSumCol As Long
    Dim facultyStartCol As Long
    Dim facultyEndCol As Long
    Dim r As Long, c As Long

    Set ws = ThisWorkbook.Worksheets("Schedule")
    lastRow = GetLastRow(ws, 1)
    rowSumCol = GetHeaderColumn(ws, "Row Sum")

    facultyStartCol = 2
    facultyEndCol = rowSumCol - 1

    For r = FIRST_DATA_ROW To lastRow
        If NzText(ws.Cells(r, 1).value) = sectionId Then
            For c = facultyStartCol To facultyEndCol
                If Val(ws.Cells(r, c).value) = 1 Then
                    GetAssignedFacultyBySection = NzText(ws.Cells(HEADER_ROW, c).value)
                    Exit Function
                End If
            Next c
            Exit Function
        End If
    Next r

    GetAssignedFacultyBySection = ""
End Function

Private Function GetPreferenceScore(ByVal sectionId As String, ByVal facultyName As String) As Variant
    Dim ws As Worksheet
    Dim lastRow As Long
    Dim lastCol As Long
    Dim r As Long, c As Long

    Set ws = ThisWorkbook.Worksheets("Preferences")
    lastRow = GetLastRow(ws, 1)
    lastCol = GetLastCol(ws, HEADER_ROW)

    For r = FIRST_DATA_ROW To lastRow
        If NzText(ws.Cells(r, 1).value) = sectionId Then
            For c = 2 To lastCol
                If NzText(ws.Cells(HEADER_ROW, c).value) = facultyName Then
                    GetPreferenceScore = ws.Cells(r, c).value
                    Exit Function
                End If
            Next c
        End If
    Next r

    GetPreferenceScore = ""
End Function

Private Function CountFacultyAssignments(ByVal facultyName As String) As Long
    Dim ws As Worksheet
    Dim lastRow As Long
    Dim rowSumCol As Long
    Dim facultyStartCol As Long
    Dim facultyEndCol As Long
    Dim r As Long, c As Long
    Dim targetCol As Long

    Set ws = ThisWorkbook.Worksheets("Schedule")
    lastRow = GetLastRow(ws, 1)
    rowSumCol = GetHeaderColumn(ws, "Row Sum")

    facultyStartCol = 2
    facultyEndCol = rowSumCol - 1
    targetCol = 0

    For c = facultyStartCol To facultyEndCol
        If NzText(ws.Cells(HEADER_ROW, c).value) = facultyName Then
            targetCol = c
            Exit For
        End If
    Next c

    If targetCol = 0 Then
        CountFacultyAssignments = 0
        Exit Function
    End If

    For r = FIRST_DATA_ROW To lastRow
        If Val(ws.Cells(r, targetCol).value) = 1 Then
            CountFacultyAssignments = CountFacultyAssignments + 1
        End If
    Next r
End Function

Private Function SumFacultyPreferenceScores(ByVal facultyName As String) As Long
    Dim wsSched As Worksheet
    Dim lastRow As Long
    Dim r As Long
    Dim sectionId As String
    Dim assignedFaculty As String
    Dim prefVal As Variant

    Set wsSched = ThisWorkbook.Worksheets("Schedule")
    lastRow = GetLastRow(wsSched, 1)

    For r = FIRST_DATA_ROW To lastRow
        sectionId = NzText(wsSched.Cells(r, 1).value)
        If sectionId <> "" Then
            assignedFaculty = GetAssignedFacultyBySection(sectionId)
            If assignedFaculty = facultyName Then
                prefVal = GetPreferenceScore(sectionId, facultyName)
                If IsNumeric(prefVal) Then
                    SumFacultyPreferenceScores = SumFacultyPreferenceScores + CLng(prefVal)
                End If
            End If
        End If
    Next r
End Function

Public Sub ClearScheduleAssignmentsOnly()
    Dim ws As Worksheet
    Dim lastRow As Long
    Dim rowSumCol As Long
    Dim facultyStartCol As Long
    Dim facultyEndCol As Long
    Dim r As Long

    Set ws = ThisWorkbook.Worksheets("Schedule")

    lastRow = GetLastRow(ws, 1)
    rowSumCol = GetHeaderColumn(ws, "Row Sum")

    facultyStartCol = 2
    facultyEndCol = rowSumCol - 1

    If lastRow < FIRST_DATA_ROW Then Exit Sub
    If facultyEndCol < facultyStartCol Then Exit Sub

    ws.Range(ws.Cells(FIRST_DATA_ROW, facultyStartCol), _
             ws.Cells(lastRow, facultyEndCol)).ClearContents

    For r = FIRST_DATA_ROW To lastRow
        If NzText(ws.Cells(r, 1).value) <> "" Then
            ws.Cells(r, rowSumCol).Formula = "=SUM(" & _
                ws.Cells(r, facultyStartCol).Address(False, False) & ":" & _
                ws.Cells(r, facultyEndCol).Address(False, False) & ")"
        Else
            ws.Cells(r, rowSumCol).ClearContents
        End If
    Next r

    AddMessage "INFO", "ClearScheduleAssignmentsOnly", "SCHEDULE_ASSIGNMENTS_CLEARED", _
        "Only solver-written assignment cells were cleared from Schedule."
End Sub

Public Sub WriteSimpleFakeSchedule()
    Dim ws As Worksheet
    Dim lastRow As Long
    Dim rowSumCol As Long
    Dim r As Long
    Dim sectionId As String

    Set ws = ThisWorkbook.Worksheets("Schedule")
    lastRow = GetLastRow(ws, 1)
    rowSumCol = GetHeaderColumn(ws, "Row Sum")

    Call ClearScheduleAssignmentsOnly

    For r = FIRST_DATA_ROW To lastRow
        sectionId = NzText(ws.Cells(r, 1).value)

        Select Case sectionId
            Case "CS101-A"
                ws.Cells(r, 2).value = 1
            Case "CS101-B"
                ws.Cells(r, 3).value = 1
            Case "CS202-A"
                ws.Cells(r, 4).value = 1
            Case "CS305-A"
                ws.Cells(r, 6).value = 1
            Case "CS410-A"
                ws.Cells(r, 7).value = 1
            Case "MATH210-A"
                ws.Cells(r, 5).value = 1
        End Select

        If sectionId <> "" Then
            ws.Cells(r, rowSumCol).Formula = "=SUM(" & _
                ws.Cells(r, 2).Address(False, False) & ":" & _
                ws.Cells(r, rowSumCol - 1).Address(False, False) & ")"
        End If
    Next r

    AddMessage "INFO", "WriteSimpleFakeSchedule", "FAKE_SCHEDULE_WRITTEN", _
        "Fake solver assignments written to Schedule."
End Sub

Public Sub ClearSummaryOutput()
    Dim ws As Worksheet

    Set ws = ThisWorkbook.Worksheets("Summary")

    ws.Range("A5:F10").ClearContents
    ws.Range("A14:F30").ClearContents
    ws.Range("A22:F100").ClearContents

    AddMessage "INFO", "ClearSummaryOutput", "SUMMARY_CLEARED", _
        "Summary result areas cleared."
End Sub

Public Sub RebuildSummaryFromSchedule()
    Dim wsSched As Worksheet
    Dim wsSummary As Worksheet
    Dim wsWorkload As Worksheet
    Dim lastSchedRow As Long
    Dim lastWorkRow As Long
    Dim outRow As Long
    Dim loadRow As Long
    Dim r As Long
    Dim cFaculty As Long, cMin As Long, cMax As Long
    Dim sectionId As String
    Dim facultyName As String
    Dim prefScore As Variant
    Dim assignedCount As Long
    Dim minRequired As Variant
    Dim maxAllowed As Variant
    Dim totalPref As Long

    Set wsSched = ThisWorkbook.Worksheets("Schedule")
    Set wsSummary = ThisWorkbook.Worksheets("Summary")
    Set wsWorkload = ThisWorkbook.Worksheets("Workload")

    lastSchedRow = GetLastRow(wsSched, 1)
    lastWorkRow = GetLastRow(wsWorkload, 1)

    cFaculty = GetHeaderColumn(wsWorkload, "Faculty Name")
    cMin = GetHeaderColumn(wsWorkload, "Min Sections")
    cMax = GetHeaderColumn(wsWorkload, "Max Sections")

    Call ClearSummaryOutput

    ' Section Assignments
    outRow = 5
    For r = FIRST_DATA_ROW To lastSchedRow
        sectionId = NzText(wsSched.Cells(r, 1).value)

        If sectionId <> "" Then
            facultyName = GetAssignedFacultyBySection(sectionId)
            prefScore = GetPreferenceScore(sectionId, facultyName)

            wsSummary.Cells(outRow, 1).value = sectionId
            wsSummary.Cells(outRow, 2).value = GetCourseTitleBySection(sectionId)
            wsSummary.Cells(outRow, 3).value = facultyName
            wsSummary.Cells(outRow, 4).value = GetDaysBySection(sectionId)
            wsSummary.Cells(outRow, 5).value = GetTimeBySection(sectionId)
            wsSummary.Cells(outRow, 6).value = prefScore

            outRow = outRow + 1
        End If
    Next r

    ' Faculty Load Summary
    loadRow = 14
    For r = FIRST_DATA_ROW To lastWorkRow
        facultyName = NzText(wsWorkload.Cells(r, cFaculty).value)

        If facultyName <> "" Then
            assignedCount = CountFacultyAssignments(facultyName)
            minRequired = wsWorkload.Cells(r, cMin).value
            maxAllowed = wsWorkload.Cells(r, cMax).value
            totalPref = SumFacultyPreferenceScores(facultyName)

            wsSummary.Cells(loadRow, 1).value = facultyName
            wsSummary.Cells(loadRow, 2).value = assignedCount
            wsSummary.Cells(loadRow, 3).value = minRequired
            wsSummary.Cells(loadRow, 4).value = maxAllowed

            If assignedCount < Val(minRequired) Or assignedCount > Val(maxAllowed) Then
                wsSummary.Cells(loadRow, 5).value = "VIOLATION"
            Else
                wsSummary.Cells(loadRow, 5).value = "OK"
            End If

            wsSummary.Cells(loadRow, 6).value = totalPref

            loadRow = loadRow + 1
        End If
    Next r

    AddMessage "INFO", "RebuildSummaryFromSchedule", "SUMMARY_REBUILT", _
        "Summary rebuilt from Schedule assignments."
End Sub

Public Sub CopyMessagesToSummaryLog()
    Dim wsMsg As Worksheet
    Dim wsSummary As Worksheet
    Dim lastRow As Long
    Dim srcRow As Long
    Dim outRow As Long

    If Not SheetExists("Messages") Then Exit Sub

    Set wsMsg = ThisWorkbook.Worksheets("Messages")
    Set wsSummary = ThisWorkbook.Worksheets("Summary")

    lastRow = GetLastRow(wsMsg, 1)
    outRow = 22

    wsSummary.Range("A22:F100").ClearContents

    For srcRow = 2 To lastRow
        wsSummary.Cells(outRow, 1).value = wsMsg.Cells(srcRow, 1).value
        wsSummary.Cells(outRow, 2).value = wsMsg.Cells(srcRow, 2).value
        wsSummary.Cells(outRow, 3).value = wsMsg.Cells(srcRow, 3).value
        wsSummary.Cells(outRow, 4).value = wsMsg.Cells(srcRow, 4).value
        wsSummary.Cells(outRow, 5).value = wsMsg.Cells(srcRow, 5).value
        wsSummary.Cells(outRow, 6).value = wsMsg.Cells(srcRow, 6).value
        outRow = outRow + 1
    Next srcRow
End Sub


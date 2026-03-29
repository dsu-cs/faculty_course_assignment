Attribute VB_Name = "modConflictPairs"
Option Explicit

Private Function NormalizeDaysToken(ByVal rawDays As String) As String
    Dim t As String

    t = UCase$(Trim$(rawDays))
    t = Replace(t, " ", "")
    t = Replace(t, "TTH", "TR")
    t = Replace(t, "TH", "R")

    NormalizeDaysToken = t
End Function

Private Function DaysOverlap(ByVal daysA As String, ByVal daysB As String) As Boolean
    Dim a As String, b As String
    Dim i As Long
    Dim ch As String

    a = NormalizeDaysToken(daysA)
    b = NormalizeDaysToken(daysB)

    For i = 1 To Len(a)
        ch = Mid$(a, i, 1)
        If InStr(1, b, ch, vbTextCompare) > 0 Then
            DaysOverlap = True
            Exit Function
        End If
    Next i

    DaysOverlap = False
End Function

Private Function TimeTextToMinutes(ByVal valueIn As Variant) As Long
    Dim txt As String
    Dim parts() As String

    If IsDate(valueIn) Then
        TimeTextToMinutes = Hour(CDate(valueIn)) * 60 + Minute(CDate(valueIn))
        Exit Function
    End If

    txt = Trim$(CStr(valueIn))
    If txt = "" Then
        TimeTextToMinutes = -1
        Exit Function
    End If

    parts = Split(txt, ":")
    If UBound(parts) <> 1 Then
        TimeTextToMinutes = -1
        Exit Function
    End If

    TimeTextToMinutes = CLng(parts(0)) * 60 + CLng(parts(1))
End Function

Private Function TimesOverlap(ByVal startA As Long, ByVal endA As Long, ByVal startB As Long, ByVal endB As Long) As Boolean
    If startA < 0 Or endA < 0 Or startB < 0 Or endB < 0 Then
        TimesOverlap = False
    Else
        TimesOverlap = (startA < endB) And (startB < endA)
    End If
End Function

Public Function BuildConflictPairsJson() As String
    Dim ws As Worksheet
    Dim lastRow As Long
    Dim r1 As Long, r2 As Long
    Dim cSectionID As Long, cDays As Long, cStart As Long, cEnd As Long
    Dim secA As String, secB As String
    Dim daysA As String, daysB As String
    Dim startA As Long, endA As Long, startB As Long, endB As Long
    Dim json As String

    Set ws = ThisWorkbook.Worksheets("Time Blocks")
    lastRow = GetLastRow(ws, 1)

    cSectionID = GetHeaderColumn(ws, "Section ID")
    cDays = GetHeaderColumn(ws, "Days")
    cStart = GetHeaderColumn(ws, "Start Time")
    cEnd = GetHeaderColumn(ws, "End Time")

    json = "["

    For r1 = FIRST_DATA_ROW To lastRow - 1
        secA = NzText(ws.Cells(r1, cSectionID).value)
        daysA = NzText(ws.Cells(r1, cDays).value)
        startA = TimeTextToMinutes(ws.Cells(r1, cStart).value)
        endA = TimeTextToMinutes(ws.Cells(r1, cEnd).value)

        If secA <> "" Then
            For r2 = r1 + 1 To lastRow
                secB = NzText(ws.Cells(r2, cSectionID).value)
                daysB = NzText(ws.Cells(r2, cDays).value)
                startB = TimeTextToMinutes(ws.Cells(r2, cStart).value)
                endB = TimeTextToMinutes(ws.Cells(r2, cEnd).value)

                If secB <> "" Then
                    If DaysOverlap(daysA, daysB) And TimesOverlap(startA, endA, startB, endB) Then
                        json = json & "{"
                        json = json & """sectionA"":" & JsonString(secA) & ","
                        json = json & """sectionB"":" & JsonString(secB) & ","
                        json = json & """daysA"":" & JsonString(daysA) & ","
                        json = json & """daysB"":" & JsonString(daysB) & ","
                        json = json & """startA"":" & JsonNumber(startA) & ","
                        json = json & """endA"":" & JsonNumber(endA) & ","
                        json = json & """startB"":" & JsonNumber(startB) & ","
                        json = json & """endB"":" & JsonNumber(endB)
                        json = json & "},"
                    End If
                End If
            Next r2
        End If
    Next r1

    If Right$(json, 1) = "," Then json = Left$(json, Len(json) - 1)
    json = json & "]"

    BuildConflictPairsJson = json
End Function

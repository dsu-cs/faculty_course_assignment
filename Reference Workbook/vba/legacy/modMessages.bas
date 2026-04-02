Attribute VB_Name = "modMessages"
Option Explicit

Private Function GetOrCreateMessagesSheet() As Worksheet
    Dim ws As Worksheet

    If SheetExists("Messages") Then
        Set GetOrCreateMessagesSheet = ThisWorkbook.Worksheets("Messages")
        Exit Function
    End If

    Set ws = ThisWorkbook.Worksheets.Add(After:=ThisWorkbook.Worksheets(ThisWorkbook.Worksheets.Count))
    ws.Name = "Messages"

    ws.Cells(1, 1).value = "Timestamp"
    ws.Cells(1, 2).value = "Severity"
    ws.Cells(1, 3).value = "Source"
    ws.Cells(1, 4).value = "Code"
    ws.Cells(1, 5).value = "Message"
    ws.Cells(1, 6).value = "Detail"

    Set GetOrCreateMessagesSheet = ws
End Function

Public Sub AddMessage(ByVal severity As String, ByVal sourceName As String, ByVal codeText As String, ByVal msg As String, Optional ByVal detail As String = "")
    Dim ws As Worksheet
    Dim nextRow As Long

    Set ws = GetOrCreateMessagesSheet()
    nextRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row + 1

    If nextRow < 2 Then nextRow = 2

    ws.Cells(nextRow, 1).value = Now
    ws.Cells(nextRow, 2).value = severity
    ws.Cells(nextRow, 3).value = sourceName
    ws.Cells(nextRow, 4).value = codeText
    ws.Cells(nextRow, 5).value = msg
    ws.Cells(nextRow, 6).value = detail
End Sub

Public Sub ClearMessages()
    Dim ws As Worksheet

    Set ws = GetOrCreateMessagesSheet()
    ws.Rows("2:" & ws.Rows.Count).ClearContents
End Sub

Public Sub ShowInfo(ByVal msg As String)
    MsgBox msg, vbInformation, "Faculty Assignment Tool"
End Sub

Public Sub ShowWarning(ByVal msg As String)
    MsgBox msg, vbExclamation, "Faculty Assignment Tool"
End Sub

Public Sub ShowErrorMessage(ByVal msg As String)
    MsgBox msg, vbCritical, "Faculty Assignment Tool"
End Sub

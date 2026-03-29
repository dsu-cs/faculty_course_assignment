Attribute VB_Name = "modUtils"
Option Explicit

Public Const HEADER_ROW As Long = 3
Public Const FIRST_DATA_ROW As Long = 4

Public Function SheetExists(ByVal sheetName As String) As Boolean
    Dim ws As Worksheet

    SheetExists = False
    For Each ws In ThisWorkbook.Worksheets
        If StrComp(ws.Name, sheetName, vbTextCompare) = 0 Then
            SheetExists = True
            Exit Function
        End If
    Next ws
End Function

Public Function GetLastRow(ByVal ws As Worksheet, ByVal colNum As Long) As Long
    GetLastRow = ws.Cells(ws.Rows.Count, colNum).End(xlUp).Row
End Function

Public Function GetLastCol(ByVal ws As Worksheet, ByVal rowNum As Long) As Long
    GetLastCol = ws.Cells(rowNum, ws.Columns.Count).End(xlToLeft).Column
End Function

Public Function NzText(ByVal valueIn As Variant) As String
    If IsError(valueIn) Then
        NzText = ""
    ElseIf IsNull(valueIn) Then
        NzText = ""
    ElseIf IsEmpty(valueIn) Then
        NzText = ""
    Else
        NzText = Trim$(CStr(valueIn))
    End If
End Function

Public Function EscapeJson(ByVal textValue As String) As String
    Dim result As String

    result = textValue
    result = Replace(result, "\", "\\")
    result = Replace(result, """", "\""")
    result = Replace(result, vbCrLf, "\n")
    result = Replace(result, vbCr, "\n")
    result = Replace(result, vbLf, "\n")

    EscapeJson = result
End Function

Public Function JsonString(ByVal valueIn As Variant) As String
    JsonString = """" & EscapeJson(NzText(valueIn)) & """"
End Function

Public Function JsonNumber(ByVal valueIn As Variant) As String
    If IsNumeric(valueIn) And NzText(valueIn) <> "" Then
        JsonNumber = CStr(valueIn)
    Else
        JsonNumber = "0"
    End If
End Function

Public Function BoolJson(ByVal valueIn As Variant) As String
    Dim txt As String
    txt = LCase$(NzText(valueIn))

    Select Case txt
        Case "true", "yes", "1"
            BoolJson = "true"
        Case Else
            BoolJson = "false"
    End Select
End Function

Public Function GetHeaderColumn(ByVal ws As Worksheet, ByVal headerName As String) As Long
    Dim lastCol As Long
    Dim colNum As Long

    lastCol = GetLastCol(ws, HEADER_ROW)

    For colNum = 1 To lastCol
        If StrComp(NzText(ws.Cells(HEADER_ROW, colNum).value), headerName, vbTextCompare) = 0 Then
            GetHeaderColumn = colNum
            Exit Function
        End If
    Next colNum

    Err.Raise vbObjectError + 2000, "GetHeaderColumn", _
        "Header not found on sheet '" & ws.Name & "': " & headerName
End Function


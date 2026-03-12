Attribute VB_Name = "modWorkbookChecks"
Option Explicit

Public Function ValidateRequiredSheets() As Boolean
    Dim requiredSheets As Variant
    Dim i As Long
    Dim missingList As String

    requiredSheets = Array("Sections", "Time Blocks", "Preferences", "Workload", "Schedule", "Summary")
    missingList = ""

    For i = LBound(requiredSheets) To UBound(requiredSheets)
        If Not SheetExists(CStr(requiredSheets(i))) Then
            missingList = missingList & vbCrLf & "- " & CStr(requiredSheets(i))
        End If
    Next i

    If missingList <> "" Then
        ShowErrorMessage "Missing required sheets:" & vbCrLf & missingList
        ValidateRequiredSheets = False
    Else
        ValidateRequiredSheets = True
    End If
End Function

Public Function ValidateSampleHeaders() As Boolean
    On Error GoTo ErrHandler

    Call GetHeaderColumn(ThisWorkbook.Worksheets("Sections"), "Section ID")
    Call GetHeaderColumn(ThisWorkbook.Worksheets("Sections"), "Course #")
    Call GetHeaderColumn(ThisWorkbook.Worksheets("Sections"), "Course Title")
    Call GetHeaderColumn(ThisWorkbook.Worksheets("Sections"), "Credits")
    Call GetHeaderColumn(ThisWorkbook.Worksheets("Sections"), "Max Seats")
    Call GetHeaderColumn(ThisWorkbook.Worksheets("Sections"), "Level")
    Call GetHeaderColumn(ThisWorkbook.Worksheets("Sections"), "Department")

    Call GetHeaderColumn(ThisWorkbook.Worksheets("Time Blocks"), "Section ID")
    Call GetHeaderColumn(ThisWorkbook.Worksheets("Time Blocks"), "Days")
    Call GetHeaderColumn(ThisWorkbook.Worksheets("Time Blocks"), "Start Time")
    Call GetHeaderColumn(ThisWorkbook.Worksheets("Time Blocks"), "End Time")
    Call GetHeaderColumn(ThisWorkbook.Worksheets("Time Blocks"), "Room")

    Call GetHeaderColumn(ThisWorkbook.Worksheets("Preferences"), "Section ID")

    Call GetHeaderColumn(ThisWorkbook.Worksheets("Workload"), "Faculty Name")
    Call GetHeaderColumn(ThisWorkbook.Worksheets("Workload"), "Min Sections")
    Call GetHeaderColumn(ThisWorkbook.Worksheets("Workload"), "Max Sections")
    Call GetHeaderColumn(ThisWorkbook.Worksheets("Workload"), "Type")
    Call GetHeaderColumn(ThisWorkbook.Worksheets("Workload"), "Notes")

    Call GetHeaderColumn(ThisWorkbook.Worksheets("Schedule"), "Section ID")
    Call GetHeaderColumn(ThisWorkbook.Worksheets("Schedule"), "Row Sum")

    ValidateSampleHeaders = True
    Exit Function

ErrHandler:
    ShowErrorMessage "Header validation failed: " & Err.Description
    ValidateSampleHeaders = False
End Function

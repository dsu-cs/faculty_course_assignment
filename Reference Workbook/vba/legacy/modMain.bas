Attribute VB_Name = "ModMain"
Option Explicit

Public Sub TestWorkbookSetup()
    If Not ValidateRequiredSheets() Then Exit Sub
    If Not ValidateSampleHeaders() Then Exit Sub

    AddMessage "INFO", "TestWorkbookSetup", "WORKBOOK_OK", _
        "Workbook structure validated successfully."

    ShowInfo "Workbook structure looks valid."
End Sub

Public Sub ResetTestOutputs()
    On Error GoTo ErrHandler

    ClearMessages
    ClearScheduleAssignmentsOnly
    ClearSummaryOutput
    CopyMessagesToSummaryLog

    ShowInfo "Test outputs cleared. Schedule assignments, Summary results, and Messages have been reset."
    Exit Sub

ErrHandler:
    ShowErrorMessage "Reset failed: " & Err.Description
End Sub


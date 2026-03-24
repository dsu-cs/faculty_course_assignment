Attribute VB_Name = "modSolverCommunication"
Option Explicit

Private Const DEFAULT_SOLVER_URL As String = "https://placeholder-url/api/solve"

Public Sub RunSolverButton()
    SubmitSolverPackage False
End Sub

Public Sub RunSolverDryRun()
    SubmitSolverPackage True
End Sub

Public Sub SubmitSolverPackage(Optional ByVal useFakeResponse As Boolean = False)
    Dim payload As String
    Dim responseText As String
    Dim solverUrl As String
    Dim appliedCount As Long

    On Error GoTo ErrHandler

    ClearMessages

    If Not ValidateRequiredSheets() Then Exit Sub
    If Not ValidateSampleHeaders() Then Exit Sub

    payload = BuildScenarioPayloadJson()
    AddMessage "INFO", "SubmitSolverPackage", "PAYLOAD_READY", _
        "Solver payload built successfully.", Left$(payload, 1000)

    If useFakeResponse Then
        responseText = BuildDemoSolverResponseJson()
        AddMessage "INFO", "SubmitSolverPackage", "FAKE_MODE", _
            "Using fake solver response for dry run demonstration."
    Else
        solverUrl = ResolveSolverUrl()
        AddMessage "INFO", "SubmitSolverPackage", "SUBMIT_START", _
            "Submitting payload to solver endpoint.", solverUrl
        responseText = HttpPostJson(solverUrl, payload)
    End If

    AddMessage "INFO", "SubmitSolverPackage", "SOLVER_RESPONSE", _
        "Solver response received.", Left$(responseText, 1000)

    appliedCount = ParseAndApplySolverResponse(responseText)

    RebuildSummaryFromSchedule
    CopyMessagesToSummaryLog

    AddMessage "INFO", "SubmitSolverPackage", "RUN_COMPLETE", _
        "Solver flow completed.", "Assignments applied=" & appliedCount

    ShowInfo "Solver flow completed. Assignments applied: " & appliedCount & "."
    Exit Sub

ErrHandler:
    AddMessage "ERROR", "SubmitSolverPackage", "RUN_FAILED", Err.Description
    CopyMessagesToSummaryLog
    ShowErrorMessage "Solver flow failed: " & Err.Description
End Sub

Public Function BuildDemoSolverResponseJson() As String
    BuildDemoSolverResponseJson = _
        "{""status"":""success""," & _
        """runId"":""RUN-DEMO-001""," & _
        """message"":""Fake solver response returned for workbook testing.""," & _
        """assignments"":[" & _
            "{""sectionId"":""CS101-A"",""facultyName"":""Dr. Smith"",""score"":3}," & _
            "{""sectionId"":""CS101-B"",""facultyName"":""Dr. Jones"",""score"":3}," & _
            "{""sectionId"":""CS202-A"",""facultyName"":""Dr. Lee"",""score"":3}," & _
            "{""sectionId"":""CS305-A"",""facultyName"":""Dr. Kim"",""score"":2}," & _
            "{""sectionId"":""CS410-A"",""facultyName"":""Dr. Nguyen"",""score"":2}" & _
        "]}"
End Function

Public Function ResolveSolverUrl() As String
    Dim configuredUrl As String

    configuredUrl = ReadSolverUrlFromSummary()
    If configuredUrl = "" Then
        configuredUrl = InputBox("Enter the solver submit URL:", "Solver URL", DEFAULT_SOLVER_URL)
    End If

    configuredUrl = Trim$(configuredUrl)
    If configuredUrl = "" Then
        Err.Raise vbObjectError + 3300, "ResolveSolverUrl", "Solver URL was not provided."
    End If

    ResolveSolverUrl = configuredUrl
End Function

Public Function ReadSolverUrlFromSummary() As String
    On Error GoTo SafeExit

    If SheetExists("Summary") Then
        ReadSolverUrlFromSummary = Trim$(CStr(ThisWorkbook.Worksheets("Summary").Range("H18").value))
    End If

SafeExit:
End Function


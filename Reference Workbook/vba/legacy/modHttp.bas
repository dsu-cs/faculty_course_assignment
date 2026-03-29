Attribute VB_Name = "modHttp"
Option Explicit

Public Function HttpPostJson(ByVal url As String, ByVal jsonBody As String) As String
    Dim http As Object

    On Error GoTo ErrHandler

    Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")

    http.Open "POST", url, False
    http.setRequestHeader "Content-Type", "application/json"
    http.send jsonBody

    If http.Status < 200 Or http.Status >= 300 Then
        AddMessage "ERROR", "HttpPostJson", "HTTP_" & http.Status, "HTTP POST failed.", http.responseText
        Err.Raise vbObjectError + 3100, "HttpPostJson", "HTTP POST failed with status " & http.Status
    End If

    AddMessage "INFO", "HttpPostJson", "HTTP_SUCCESS", "HTTP POST succeeded.", "Status " & http.Status
    HttpPostJson = http.responseText
    Exit Function

ErrHandler:
    AddMessage "ERROR", "HttpPostJson", "POST_FAILED", Err.Description
    Err.Raise Err.Number, Err.Source, Err.Description
End Function

Public Function GetFakeSolverResponseJson() As String
    Dim json As String

    json = "{"
    json = json & """status"":""success"","
    json = json & """runId"":""RUN-DEMO-001"","
    json = json & """message"":""Fake solver response returned for workbook testing."","
    json = json & """assignments"":["
    json = json & "{""sectionId"":""CS101-A"",""facultyName"":""Dr. Smith"",""score"":3},"
    json = json & "{""sectionId"":""CS101-B"",""facultyName"":""Dr. Jones"",""score"":3},"
    json = json & "{""sectionId"":""CS202-A"",""facultyName"":""Dr. Lee"",""score"":3}"
    json = json & "]"
    json = json & "}"

    GetFakeSolverResponseJson = json
End Function

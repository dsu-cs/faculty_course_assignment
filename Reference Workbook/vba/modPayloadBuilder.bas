Attribute VB_Name = "modPayloadBuilder"
Option Explicit

Public Function BuildScenarioPayloadJson() As String
    Dim json As String

    json = "{"
    json = json & """schemaVersion"":""0.3"","
    json = json & """generatedAt"":" & JsonString(Format$(Now, "yyyy-mm-dd\Thh:nn:ss")) & ","
    json = json & """sourceWorkbook"":" & JsonString(ThisWorkbook.Name) & ","
    json = json & """sections"":" & ReadSectionsJsonArray() & ","
    json = json & """faculty"":" & ReadFacultyJsonArrayFromPreferences() & ","
    json = json & """timeBlocks"":" & ReadTimeBlocksJsonArray() & ","
    json = json & """conflictPairs"":" & BuildConflictPairsJson() & ","
    json = json & """preferences"":" & ReadPreferencesJsonArray() & ","
    json = json & """workload"":" & ReadWorkloadJsonArray()
    json = json & "}"

    BuildScenarioPayloadJson = json
End Function

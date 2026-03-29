VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "clsSection"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
Option Explicit

Private pSectionId As String
Private pCourseNumber As String
Private pCourseTitle As String
Private pCredits As Long
Private pMaxSeats As Long
Private pLevel As String
Private pDepartment As String

Public Property Get SectionId() As String
    SectionId = pSectionId
End Property

Public Property Let SectionId(ByVal value As String)
    pSectionId = Trim$(value)
End Property

Public Property Get CourseNumber() As String
    CourseNumber = pCourseNumber
End Property

Public Property Let CourseNumber(ByVal value As String)
    pCourseNumber = Trim$(value)
End Property

Public Property Get CourseTitle() As String
    CourseTitle = pCourseTitle
End Property

Public Property Let CourseTitle(ByVal value As String)
    pCourseTitle = Trim$(value)
End Property

Public Property Get Credits() As Long
    Credits = pCredits
End Property

Public Property Let Credits(ByVal value As Long)
    pCredits = value
End Property

Public Property Get MaxSeats() As Long
    MaxSeats = pMaxSeats
End Property

Public Property Let MaxSeats(ByVal value As Long)
    pMaxSeats = value
End Property

Public Property Get Level() As String
    Level = pLevel
End Property

Public Property Let Level(ByVal value As String)
    pLevel = Trim$(value)
End Property

Public Property Get Department() As String
    Department = pDepartment
End Property

Public Property Let Department(ByVal value As String)
    pDepartment = Trim$(value)
End Property

Public Function ToJson() As String
    ToJson = "{" & _
        "\"sectionId\":" & JsonString(pSectionId) & "," & _
        "\"courseNumber\":" & JsonString(pCourseNumber) & "," & _
        "\"courseTitle\":" & JsonString(pCourseTitle) & "," & _
        "\"credits\":" & JsonNumber(pCredits) & "," & _
        "\"maxSeats\":" & JsonNumber(pMaxSeats) & "," & _
        "\"level\":" & JsonString(pLevel) & "," & _
        "\"department\":" & JsonString(pDepartment) & _
        "}"
End Function

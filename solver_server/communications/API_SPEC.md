# Communications Server API Specification

**Version:** 0.2.0  
**Author:** Muhammad Bhutta  
**Team:** Lindsey Crow (VBA), Tyler Hardy (Communications)  
**Last Updated:** March 21, 2026

---

## Base URL
```
http://solver-server:5000
```

**Note:** For local testing, use `http://localhost:5000`

---

## Authentication

**Current:** None required (internal network only)  
**Future:** May add API key header: `X-API-Key: <key>`

---

## Endpoints

### 1. GET /health

**Purpose:** Check if solver server is running and healthy

**Request:** None

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "solver-server",
  "solver_available": true
}
```

**Example (VBA):**
```vb
GET http://solver-server:5000/health
```

---

### 2. GET /

**Purpose:** Get server information and status

**Request:** None

**Response (200 OK):**
```json
{
  "service": "Faculty Course Assignment Solver Server",
  "version": "0.2.0",
  "author": "Muhammad Bhutta",
  "status": "running",
  "solver_available": true,
  "timestamp": "2026-03-21T22:32:14.246083"
}
```

---

### 3. POST /solve

**Purpose:** Submit course assignment data and get solver recommendations

**Request Headers:**
Content-Type: application/json
  "preferences_csv": "section,faculty,score\nCSC150,Alice,3\n...",
  "time_blocks_csv": "section,pattern,start_time\nCSC150,MWF,08:00\n...",
  "workload_csv": "faculty,min,max\nAlice,1,2\n..."
}
```

**Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| run_id | string | No | Unique identifier for this solve request (auto-generated if not provided) |
| preferences_csv | string | Yes | CSV data with faculty preferences (0-3 or X) |
| time_blocks_csv | string | Yes | CSV data with section meeting times |
| workload_csv | string | Yes | CSV data with faculty min/max teaching loads |

**Response (200 OK - Success):**
```json
{
  "status": "success",
  "run_id": "run_20260321_223214",
  "assignments": [
    {
      "section": "CSC150",
      "faculty": "Alice"
    },
    {
      "section": "CSC250",
      "faculty": "Bob"
    }
  ],
  "validation_passed": true,
  "violations": [],
  "warnings": [],
  "timestamp": "2026-03-21T22:32:14.246083"
}
```

**Response (200 OK - No Solution):**
```json
{
  "status": "error",
  "run_id": "run_20260321_223214",
  "message": "No valid assignment found",
  "details": "The solver could not find a solution that satisfies all constraints"
}
```

**Response (400 Bad Request):**
```json
{
  "status": "error",
  "message": "Missing required CSV data",
  "details": {
    "preferences_csv": "received",
    "time_blocks_csv": "missing",
    "workload_csv": "received"
  }
}
```

**Response (500 Internal Server Error):**
```json
{
  "status": "error",
  "message": "Internal server error",
  "details": "Error description here",
  "timestamp": "2026-03-21T22:32:14.246083"
}
```

---

## CSV Format Specifications

### preferences.csv
```csv
section,faculty,score
CSC150-A,Alice,3
CSC150-A,Bob,1
CSC250-A,Alice,2
CSC250-A,Bob,X
```

**Fields:**
- `section`: Section ID (string)
- `faculty`: Faculty name (string)
- `score`: Preference (0=neutral, 1=low, 2=medium, 3=high, X=cannot teach)

### time_blocks.csv
```csv
section,pattern,start_time
CSC150-A,MWF,08:00
CSC250-A,TTh,10:00
```

**Fields:**
- `section`: Section ID (string)
- `pattern`: Day pattern (MWF, TTh, or MW)
- `start_time`: Start time in HH:MM format (24-hour)

### workload.csv
```csv
faculty,min,max
Alice,1,2
Bob,1,3
```

**Fields:**
- `faculty`: Faculty name (string)
- `min`: Minimum sections to teach (integer)
- `max`: Maximum sections to teach (integer)

---

## Error Handling

All errors return appropriate HTTP status codes:

| Status Code | Meaning | Action |
|-------------|---------|--------|
| 200 | Success | Process results normally |
| 400 | Bad Request | Check JSON format and required fields |
| 500 | Server Error | Retry or contact administrator |

All error responses include:
- `status`: "error"
- `message`: Human-readable error message
- `details` (optional): Additional error information

---

## VBA Integration Example
```vb
' Example VBA code for calling the solver

Sub CallSolver()
    Dim http As Object
    Set http = CreateObject("MSXML2.XMLHTTP")
    
    ' Build JSON request
    Dim jsonRequest As String
    jsonRequest = "{" & _
        """run_id"": ""run_" & Format(Now, "yyyymmdd_hhnnss") & """," & _
        """preferences_csv"": """ & GetPreferencesCSV() & """," & _
        """time_blocks_csv"": """ & GetTimeBlocksCSV() & """," & _
        """workload_csv"": """ & GetWorkloadCSV() & """" & _
        "}"
    
    ' Send request
    http.Open "POST", "http://solver-server:5000/solve", False
    http.setRequestHeader "Content-Type", "application/json"
    http.send jsonRequest
    
    ' Handle response
    If http.Status = 200 Then
        Dim response As String
        response = http.responseText
        ' Parse JSON response and update workbook
        ProcessResults response
    Else
        MsgBox "Error: " & http.Status & " - " & http.responseText
    End If
End Sub
```

---

## Testing

Test the endpoints using curl:
```bash
# Health check
curl http://localhost:5000/health

# Server info
curl http://localhost:5000/

# Solve request
curl -X POST http://localhost:5000/solve \
  -H "Content-Type: application/json" \
  -d '{"preferences_csv":"...","time_blocks_csv":"...","workload_csv":"..."}'
```

---

## Contact

**Questions or Issues:**
- Muhammad Bhutta (Communications Server)
- Lindsey Crow (Excel VBA Integration)
- Tyler Hardy (Communications Team)

**GitHub Branch:** `communications-setup````json
{
  "run_id": "optional-unique-identifier",
```

**Request Body (JSON):**


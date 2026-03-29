# CSV to CSP Converter

**Manager:** Anto Shibu  
**Team:** Muhammad Bhutta, Sawyer DeWitt  
**Status:** Initial Setup

---

## Overview

Converts CSV data from Excel workbook into Google OR-Tools Constraint Satisfaction Problem format.

---

## Purpose

Takes structured CSV files (sections, faculty, preferences) and generates a solvable CSP that:
- Creates binary variables for faculty-section assignments
- Applies hard constraints (workload limits, qualifications)
- Applies soft constraints (preferences, balance)
- Returns optimal assignments

---

## Input Files

### sections.csv
```csv
SectionID,CourseNumber,Credits,Enrolled,Capacity,IsGraduate
12345,CSC150,3,15,25,FALSE
12346,CSC770,4,12,25,TRUE
```

### faculty.csv
```csv
FacultyID,Name,Baseline,IsTenureTrack
jared,Jared Sandy,30,TRUE
alice,Alice Smith,30,FALSE
```

### preferences.csv
```csv
FacultyID,SectionID,Preference
jared,12345,+2
alice,12345,X
```

---

## Output

Python CSP model ready to solve with OR-Tools.

---

## Module Structure
```
csv_converter/
├── __init__.py
├── parser.py          # CSV parsing and validation
├── models.py          # Data structure classes
├── generator.py       # CSP generation from data
├── converter.py       # Main orchestrator
├── tests/             # Unit tests
└── test_data/         # Sample CSV files for testing
```

---

## Current Status

- [x] Directory structure created
- [ ] Parser implementation
- [ ] Generator implementation
- [ ] Unit tests
- [ ] Integration with Communications server

---

## Dependencies

- Requires CSP Design specification (Gabe's team)
- Used by Communications server (Muhammad's team)
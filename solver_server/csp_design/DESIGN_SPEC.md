# Constraint Satisfaction Problem Design Specification

**Authors:** Gabe Delle (Manager), Muhammad Bhutta, Anto Shibu  
**Last Updated:** March 21, 2026  
**Status:** Draft

---

## Overview

This document defines how faculty-course assignment constraints are structured and processed by the solver for the DSU Faculty Workload & Course Scheduling Tool.

---

## Variables

### Binary Assignment Variables
Each potential faculty-course assignment is a Boolean variable:

**Format:** `faculty_[facultyID]_section_[sectionID]`  
**Domain:** {0, 1} where 1 = assigned, 0 = not assigned

**Example:**
- `faculty_jared_section_12345` = Is Jared assigned to section 12345?

**Optimization:** If faculty preference = 'X' (cannot teach), variable is NOT created.

---

## Constraint Types

### 1. Hard Constraints (MUST be satisfied)

#### H1: Workload Maximum
**Rule:** Faculty workload cannot exceed 125% of baseline

**Formula:**
```
SUM(credits for all assigned courses) <= baseline * 1.25
```

**Example:**
- Tenure track faculty baseline = 30 credits
- Maximum allowed = 37.5 credits

#### H2: Time Conflicts
**Rule:** Faculty cannot teach two sections at the same time

**Formula:**
```
If time_overlap(section_A, section_B):
    faculty_X_section_A + faculty_X_section_B <= 1
```

#### H3: Qualifications
**Rule:** Faculty cannot teach courses they're not qualified for

**Formula:**
```
If preference[faculty][course] == 'X':
    faculty_course_assignment = 0
```

#### H4: Section Coverage
**Rule:** Each section must have exactly one faculty assigned

**Formula:**
```
SUM(all faculty variables for section) == 1
```

---

### 2. Soft Constraints (PREFER to satisfy)

#### S1: Faculty Preferences
**Rule:** Maximize preference satisfaction

**Preference Mapping:**
- +3 → weight 30
- +2 → weight 20
- +1 → weight 10
- 0 → weight 0
- -1 → weight -10
- -2 → weight -20
- -3 → weight -30

#### S2: Minimize Overload
**Rule:** Prefer faculty to stay under baseline (100%)

**Penalty:** -5 points per credit over baseline

#### S3: Workload Balance
**Rule:** Distribute workload evenly among faculty

**Goal:** Minimize variance in faculty workloads

---

## Credit Calculation Rules

### Undergraduate Courses
- Base credits: 3
- If enrolled >= 10: Full 3 credits
- If enrolled < 10: `(enrolled * 1.33 / 10) * 3`

### Graduate Courses
- Base credits: 4
- Same enrollment rules as undergraduate

### Cross-Listed Courses
- If one section >= 10 students: other section < 10 gets +1 bonus credit

### Dissertation
- 0.5 credits per student

---

## Input Data Format

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
jared,12346,+3
alice,12345,X
```

---

## Solver Output Format

### Success Response
```json
{
  "status": "feasible",
  "objective_value": 245.5,
  "assignments": [
    {"faculty": "jared", "section": "12345", "course": "CSC 770"}
  ],
  "violations": [],
  "warnings": [
    {
      "type": "overload",
      "faculty": "jared",
      "message": "2 credits over baseline"
    }
  ]
}
```

### Infeasible Response
```json
{
  "status": "infeasible",
  "violations": [
    {
      "type": "H1",
      "faculty": "jared",
      "message": "Cannot assign - exceeds 125% maximum"
    }
  ]
}
```

---

## Implementation Checklist

### Phase 1 (MVP):
- [ ] H1: Workload maximum constraint
- [ ] H3: Qualification constraint (X rating)
- [ ] H4: Section coverage constraint
- [ ] S1: Faculty preferences objective

### Phase 2 (Future):
- [ ] H2: Time conflict constraint
- [ ] S2: Minimize overload penalty
- [ ] S3: Workload balance
- [ ] Graduate course multiplier
- [ ] Cross-listing rules
- [ ] Dissertation credits

---

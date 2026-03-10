## Data Flow

```
Excel Workbook
│
│  [Time Blocks tab] ──► build_conflict_pairs() ──────────────┐
│  [Preferences tab] ──► load_preferences()     ──► SchedulingData
│  [Workload tab]    ──► load_workload()         ──────────────┘
│                                                              │
│                                                      build_model()
│                                                              │
│                                                       run_solver()
│                                                              │
│  [Schedule tab]    ◄── write_schedule() ◄── assignment dict ┘
```

## Workbook Tab Reference

| Tab              | Sent to OR? | Notes                                  |
|------------------|-------------|----------------------------------------|
| Sections         | No          | Course catalogue, not used by solver   |
| Time Blocks      | Via code    | Converted to conflict pairs in Python  |
| Preferences      | Yes         | -3 to +3 scores, used as objective     |
| Workload         | Yes         | Min/max sections per faculty           |
| Schedule         | Output      | 0/1 matrix written by solver           |
| Summary          | No          | Readable view of Schedule tab          |

---

## Constraint Summary

| ID  | Type       | Description                                              |
|-----|------------|----------------------------------------------------------|
| C1  | Coverage   | Every section assigned to exactly 1 faculty              |
| C2  | Validity   | Assigned faculty must exist in the faculty list          |
| C3  | Workload   | Each faculty teaches between min and max sections        |
| C4  | Conflict   | No faculty teaches two time-overlapping sections         |
| Obj | Objective  | Maximise sum of pref[s][f] × x[s][f] over all assignments|

---


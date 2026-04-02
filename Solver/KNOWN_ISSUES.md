# Known Issues & Design Notes

Living document tracking open bugs, deferred features, and design decisions
for the Faculty Scheduling Solver. Update this file when issues are discovered,
work begins, or items are resolved.

**Format:**
- Each entry has a unique ID, status, date logged, and description
- Tag the area of code affected so the right person picks it up
- Move resolved items to the Resolved section with a closing note

**Status values:** `Open` · `In Progress` · `Resolved` · `Deferred`

**Area tags:** `data_loader` · `build_csp` · `validator` · `output` · `csv_format` · `design`

---

## Open Issues

---

### KI-001 | Dual credit sections treated as independent
**Status:** Open
**Date logged:** 2026-03-13
**Area:** `data_loader` · `build_csp`

400-level and 500-level sections co-taught in the same room at the same time
(e.g. CSC 461 and CSC 561, CSC 447 and CSC 547) are currently treated as two
independent sections. The solver may assign them to different faculty, which is
invalid, or correctly assign them to the same faculty but flag a false time
conflict violation since they share a time block.

**Proposed fix:**
Add a `linked_pairs` field to `SchedulingData` and detect pairs automatically
in `load_all()` by grouping sections that share the same faculty, day pattern,
and start time where one course number is exactly 100 higher than the other.

In `build_csp()`, add:
```python
# Linked sections must always be assigned to the same faculty
for crn1, crn2 in data.linked_pairs:
    for f in faculty:
        model.add(x[crn1, f] == x[crn2, f])
```

Also add a C6 check to `validate()` to verify linked pairs were not split.

---

### KI-002 | Workload formula — partial implementation, pending policy confirmation
**Status:** In Progress
**Date logged:** 2026-03-13
**Area:** `data_loader` · `build_csp` · `csv_format`

Dynamic workload calculation is now implemented in `load_all()`. When `workload_if_full` and `workload_per_student` columns are present in `sections.csv`, the formula is:
```python
if current_seats >= max_seats > 0:
    units = workload_if_full
else:
    units = round(workload_per_student × current_seats)
units = max(units, 1)
```

If only `workload_if_full` is present, that value is used directly. If neither column is present, sections fall back to `DEFAULT_COURSE_WORKLOAD = 4`.

**Remaining work:** The full DSU policy rules have not yet been confirmed with the client:
- Small section threshold (< 10 students, 100–600 level): `enrolled × 0.10 × credit_hours`
- Grad 700+ multiplier: `credit_hours × 1.33`
- Cross-listed 400/500 bonus: `+1 unit`

The formula is isolated in one loop in `load_all()` and is a single block change once the client confirms.

---

### KI-003 | Room assignment not modelled
**Status:** Open
**Date logged:** 2026-03-13
**Area:** `build_csp` · `data_loader` · `csv_format`

The `room` column in `time_blocks.csv` is currently read but completely ignored
by the solver. No room constraints exist in the model.

**Planned approach (Option 2 — separate variable):**
Add a second decision variable `y[section, room] ∈ {0, 1}` alongside the
existing `x[section, faculty]`. This keeps faculty and room scheduling
decoupled and avoids a 3D variable.

New constraints needed:
```python
# Each section assigned to exactly one room
for s in sections:
    model.add_exactly_one(y[s, r] for r in rooms)

# No two time-conflicting sections can share a room
for s1, s2 in conflict_pairs:
    for r in rooms:
        model.add(y[s1, r] + y[s2, r] <= 1)
```

New input needed: a `rooms.csv` with room ID, building, capacity, and type
(lecture hall / lab / seminar).

New output needed: a `room_assignment.csv` (0/1 matrix, same format as
`schedule.csv`) and a room column in the Summary output.

**Dependency:** KI-004 (online sections) must be resolved first so that
online sections are correctly excluded from room assignment.

---

### KI-004 | Cross-listed internet twin detection and assignment copy
**Status:** Resolved
**Date logged:** 2026-03-13
**Resolved:** 2026-03-29
**Area:** `data_loader` · `output`

Internet sections sharing the same `Sub + Num + Desc` as a regular in-person section are now detected in `load_all()` and filtered from the OR solver. After solving, `write_schedule_csv()` copies the regular section's faculty assignment to the twin. Twins share identical preference scores in `preferences.csv` (cached by `(sub, num, desc)` key during generation).

In the latest run: 168 twins detected and filtered, assignments copied correctly, validation passed.

---

### KI-005 | Co-taught sections (shared faculty) not handled
**Status:** Open
**Date logged:** 2026-03-13
**Area:** `data_loader`

Some sections in the registrar data list two faculty separated by `/`
(e.g. `Peter C Britton/Erik John Pederson`). These are currently skipped
entirely during faculty extraction because the slash is used as a filter.

This means co-taught sections have no assigned faculty in the preferences
matrix and will likely receive a low-preference assignment or cause issues
if those faculty members are expected to split the workload.

**Proposed fix:**
Split the faculty string on `/`, register both names, and model the section
as requiring both faculty (or optionally either, depending on department
policy). This may require a new constraint type: `add_at_least_one` for
sections that can be covered by either of two specific faculty.

---

### KI-006 | No capacity constraint on room size vs section enrollment
**Status:** Deferred
**Date logged:** 2026-03-13
**Area:** `build_csp`

When room assignment is added (KI-003), the model will need to ensure that a
section's enrollment does not exceed the room's capacity. The `Seats` column
in the registrar data contains enrollment in `enrolled/capacity` format
(e.g. `21/25`) which would need to be parsed.

**Dependency:** Blocked by KI-003.

---

### KI-008 | No room type constraint (lab vs lecture hall)
**Status:** Deferred
**Date logged:** 2026-03-13
**Area:** `build_csp` · `csv_format`

Lab sections (e.g. BIOL 101L, CHEM 326L) require a laboratory room, not a
standard lecture hall. When room assignment is added, the model will need a
room type constraint:

```python
# A lab section can only be assigned to a lab room
for s in lab_sections:
    for r in non_lab_rooms:
        model.add(y[s, r] == 0)
```

This requires a `room_type` column in `rooms.csv` and a `section_type` field
derivable from the course number suffix (e.g. `L` in `BIOL 101L`).

**Dependency:** Blocked by KI-003.

---

### KI-009 | Single-day sections bucketed and excluded from OR
**Status:** Resolved
**Date logged:** 2026-03-13
**Resolved:** 2026-03-29
**Area:** `data_loader`

Single-day sections (M, Tu, W, Th, F) are now detected in `_is_single_day()` and bucketed into `single_day` in `load_all()`. They are excluded from OR and from conflict pair generation, but are preserved in `all_sections_ordered` and written to `schedule.csv` with a blank faculty assignment so the output row count matches `sections.csv` exactly.

In the latest run: 31 single-day sections correctly bucketed and excluded.

---

### KI-010 | schedule.csv is silently overwritten on each run
**Status:** Open
**Date logged:** 2026-03-13
**Area:** `output`

`write_schedule_csv()` overwrites any existing `schedule.csv` without warning.
There is no history of previous runs.

**Proposed fix (optional):** Add a `--timestamp` flag that appends a datetime
to the output filename, e.g. `schedule_20260313_143022.csv`. Keep default
behaviour (overwrite) unchanged so existing integrations are not broken.

---

### KI-011 | No early feasibility check before running the solver
**Status:** Open
**Date logged:** 2026-03-13
**Area:** `data_loader`

`load_all()` does not verify that the problem is likely feasible before handing
data to the solver. The solver may spend time searching before returning
`INFEASIBLE` for problems that could be caught immediately, such as:

- Total `max_sections` across all faculty is less than the number of sections
- A section has `x` for every faculty member (no valid assignment possible)
- A section appears in `preferences.csv` but not in `time_blocks.csv`

**Proposed fix:** Add a `preflight_check(data: SchedulingData)` function in
`data_loader` that raises descriptive errors for these cases before the model
is built.

---

## Resolved Issues

### KI-004 | Cross-listed internet twin detection and assignment copy
[see above]

### KI-009 | Single-day sections bucketed and excluded from OR
[see above]

---

## Deferred — Future Work

Items that are intentionally out of scope for the current version but should
be revisited.

| ID | Item | Reason deferred |
|---|---|---|
| KI-002 | Weighted workload (credit hours × enrollment) | Needs department agreement on formula |
| KI-007 | Room capacity vs enrollment constraint | Blocked by KI-003 (room assignment) |
| KI-008 | Room type constraint (lab vs lecture) | Blocked by KI-003 (room assignment) |

---

## Design Decisions — On Record

Decisions made deliberately that future contributors should understand before
changing.

**Why `x` instead of negative scores for exclusions?**
The original design used `-3 to +3` scores. Negative scores were soft
discouragement — the solver could still assign a faculty member with a `-3`
score if no better option existed. This was changed to `0–3 + x` so that
hard exclusions (unqualified faculty, conflict of interest) are truly
impossible rather than just unlikely. See `load_preferences()` for
implementation.

**Why are conflict pairs a flat list and not a matrix?**
The conflict pair list `[(s1, s2), ...]` is simpler to iterate over in
`build_csp()` than a 2D matrix and avoids the risk of the matrix getting
out of sync with the time block data. The list is always derived fresh from
`time_blocks.csv` on each run.

**Why is end time not stored in `time_blocks.csv`?**
End times are fully deterministic given start time and day pattern (MWF = 50
min, TTh/MW = 75 min). Storing them would create a second source of truth
that could drift out of sync. They are always computed in `_derive_end_time()`.

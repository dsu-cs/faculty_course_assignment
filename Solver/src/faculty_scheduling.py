"""
faculty_scheduling.py
=====================
Faculty scheduling solver using Google OR-Tools CP-SAT.

Reads three CSV files as input:
    preferences.csv  — section x faculty preference scores x or (0 to +3)
    time_blocks.csv  — section day pattern + start time (registrar data)
    workload.csv     — faculty min/max teaching load

Solves a Constraint Satisfaction Problem (CSP) to find the best
faculty-to-section assignment that satisfies all constraints.

Outputs:
    schedule.csv     — section x faculty assignment matrix (0/1)
    prints a human-readable summary to the terminal

Usage:
    python faculty_scheduling.py
    python faculty_scheduling.py --preferences p.csv --time_blocks t.csv --workload w.csv

CSV formats are described in each loader function below.
"""

from __future__ import annotations

import csv
import sys
import argparse
from dataclasses import dataclass, field
from datetime import time, datetime, timedelta
from itertools import combinations
from typing import NamedTuple

from ortools.sat.python import cp_model


# ══════════════════════════════════════════════════════════════════════
#  SECTION 1 — CONSTANTS & DATA STRUCTURES
#  These are shared across all parts of the pipeline.
# ══════════════════════════════════════════════════════════════════════

# Duration rules — fixed by institution, derived from day pattern.
# End time is never stored in the CSV; it is always computed from these.
DURATION_MINUTES: dict[str, int] = {
    "MWF": 50,   # Mon / Wed / Fri  → 50-minute sessions
    "TTh": 75,   # Tue / Thu        → 75-minute sessions
    "MW":  75,   # Mon / Wed        → 75-minute sessions
}

# Which individual days each pattern covers.
# Used for the day-overlap check when computing conflict pairs.
PATTERN_DAYS: dict[str, frozenset[str]] = {
    "MWF": frozenset({"M", "W", "F"}),
    "TTh": frozenset({"T", "H"}),
    "MW":  frozenset({"M", "W"}),
}

# Solver time limit — increase for larger problems
SOLVER_TIME_LIMIT_SECONDS = 60.0


class TimeBlock(NamedTuple):
    """
    Represents the meeting schedule of one section.
    End time is computed from pattern + start, never read from file.
    Room is a placeholder — not used in the current model.
    """
    section_id: str
    pattern: str             # "MWF" | "TTh" | "MW"
    days: frozenset[str]     # individual day characters
    start: time
    end: time                # derived, not stored in CSV
    room: str = ""           # placeholder for future room assignment


@dataclass
class SchedulingData:
    """
    All inputs the CSP model needs, in clean Python types.
    Produced by load_all() and consumed by build_csp().
    """
    sections: list[str]
    faculty: list[str]

    # preferences[section][faculty] = integer score from -3 to +3
    # +3 = strongly prefer, -3 = strongly avoid, 0 = neutral
    preferences: dict[str, dict[str, int]]

    # Pairs of sections that overlap in time — no faculty can teach both
    conflict_pairs: list[tuple[str, str]]

    # workload[faculty] = (min_sections, max_sections)
    workload: dict[str, tuple[int, int]]
    exclusions:     set[tuple[str, str]]   


@dataclass
class BuiltModel:
    """
    The fully described (but not yet solved) CP-SAT model.
    Produced by build_csp() and consumed by run_solver().
    """
    model: cp_model.CpModel

    # x[section, faculty] is a BoolVar — 1 if assigned, 0 if not
    # This is the core decision variable of the entire CSP
    x: dict[tuple[str, str], cp_model.IntVar]

    # Carried through so the solver can loop over them when reading results
    sections: list[str]
    faculty: list[str]


@dataclass
class ValidationReport:
    """Collects errors and warnings from constraint validation."""
    passed: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def fail(self, msg: str) -> None:
        self.passed = False
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def print_report(self) -> None:
        status = "✓ ALL CHECKS PASSED" if self.passed else "✗ VALIDATION FAILED"
        print(f"\n{'─' * 50}")
        print(f"  Validation: {status}")
        print(f"{'─' * 50}")
        for e in self.errors:
            print(f"  [ERROR]  {e}")
        for w in self.warnings:
            print(f"  [WARN]   {w}")
        if not self.errors and not self.warnings:
            print("  (no issues)")


# ══════════════════════════════════════════════════════════════════════
#  SECTION 2 — CSV LOADERS 
#
#  Reads the three input CSVs and converts them into SchedulingData.
#  No OR-Tools types are used here
#
#  CSV formats:
#
#  preferences.csv
#      section_id, Faculty A, Faculty B, Faculty C, ...
#      CS101-A,    3,         1,          0,         ...
#      (first column = section ID, remaining = one score per faculty)
#
#  time_blocks.csv
#      section_id, pattern, start_time, room
#      CS101-A,    MWF,     08:00,      (blank — future use)
#      (room column optional for MVP; end time is derived from pattern)
#
#  workload.csv
#      faculty, min_sections, max_sections
#      Dr. Smith, 1, 2
# ══════════════════════════════════════════════════════════════════════

def _normalise_pattern(raw: str) -> str:
    """
    Convert scraped day pattern strings to the canonical keys used in
    DURATION_MINUTES. Handles case variations (tth, TTH, MWf, etc.).
    """
    mapping = {
        "mwf": "MWF", "MWF": "MWF",
        "tth": "TTh", "TTH": "TTh", "TTh": "TTh",
        "mw":  "MW",  "MW":  "MW",
    }
    cleaned = raw.strip()
    result  = mapping.get(cleaned) or mapping.get(cleaned.upper())
    if result is None:
        raise ValueError(
            f"Unrecognised day pattern '{raw}'. "
            f"Supported patterns: {list(DURATION_MINUTES)}"
        )
    return result


def _derive_end_time(start: time, pattern: str) -> time:
    """
    Compute the end time of a section from its start time and day pattern.
    This replaces storing end time in the CSV — it is always deterministic.

    MWF  08:00  →  08:50  (+ 50 min)
    TTh  09:30  →  10:45  (+ 75 min)
    MW   13:00  →  14:15  (+ 75 min)
    """
    minutes = DURATION_MINUTES[pattern]
    dt = datetime.combine(datetime.today(), start) + timedelta(minutes=minutes)
    return dt.time()


def _times_overlap(a_start: time, a_end: time,
                   b_start: time, b_end: time) -> bool:
    """
    Return True if time interval [a_start, a_end) overlaps [b_start, b_end).

    Back-to-back sections sharing only a boundary are NOT considered
    conflicting — a section ending at 09:00 does not conflict with one
    starting at 09:00.
    """
    return a_start < b_end and b_start < a_end


def _sections_conflict(a: TimeBlock, b: TimeBlock) -> bool:
    """
    Two sections conflict when BOTH conditions are true:
      1. They share at least one meeting day
      2. Their time intervals overlap

    Either condition alone is not enough — different-day sections never
    conflict regardless of time, and same-day back-to-back sessions don't.
    """
    days_overlap = bool(a.days & b.days)
    if not days_overlap:
        return False
    return _times_overlap(a.start, a.end, b.start, b.end)


def load_preferences(path: str) -> tuple[list[str], list[str], dict[str, dict[str, int]], set[tuple[str, str]]]:
    """
    Read preferences.csv.

    Expected format (first row = header):
        section_id, Faculty A, Faculty B, Faculty C, ...
        CS101-A,    3,         1,          x,         ...

    Score values:
        0-3  — preference score (0 = neutral, 3 = strongly prefer)
        x    — hard exclusion, this faculty CANNOT be assigned to this section

    Returns:
        sections    — ordered list of section IDs
        faculty     — ordered list of faculty names (from header)
        preferences — preferences[section][faculty] = int score (0–3)
        exclusions  — set of (section, faculty) pairs that are hard excluded
    """
    sections:   list[str] = []
    faculty:    list[str] = []
    preferences: dict[str, dict[str, int]] = {}
    exclusions:  set[tuple[str, str]] = set()   # (section, faculty) pairs marked x

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)

        # Faculty names start at column index 1 (index 0 is "section_id")
        faculty = [name.strip() for name in header[1:]]

        for row in reader:
            if not row or not row[0].strip():
                continue  # skip blank rows

            section_id = row[0].strip()
            sections.append(section_id)
            preferences[section_id] = {}

            for i, fac in enumerate(faculty):
                raw = row[i + 1].strip() if (i + 1 < len(row) and row[i + 1].strip()) else "0"

                if raw.lower() == "x":
                    # Hard exclusion — faculty cannot teach this section
                    # Store as 0 in preferences (neutral) and record in exclusions
                    preferences[section_id][fac] = 0
                    exclusions.add((section_id, fac))
                else:
                    preferences[section_id][fac] = int(raw)

    return sections, faculty, preferences, exclusions


def load_time_blocks(path: str) -> dict[str, TimeBlock]:
    """
    Read time_blocks.csv.

    Expected format (first row = header):
        section_id, pattern, start_time, room
        CS101-A,    MWF,     08:00,      (room left blank for now)

    End time is NOT in the CSV — it is derived from the day pattern.
    Room column is read but not used in the MVP (placeholder).

    Returns:
        time_blocks — time_blocks[section_id] = TimeBlock
    """
    time_blocks: dict[str, TimeBlock] = {}

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            section_id = row["section_id"].strip()
            pattern    = _normalise_pattern(row["pattern"])

            # Parse start time from "HH:MM" string
            h, m   = map(int, row["start_time"].strip().split(":"))
            start  = time(h, m)

            # Derive end time from pattern — never stored in the file
            end = _derive_end_time(start, pattern)

            # Room is read but not used yet — stored for future extension
            room = row.get("room", "").strip()

            time_blocks[section_id] = TimeBlock(
                section_id=section_id,
                pattern=pattern,
                days=PATTERN_DAYS[pattern],
                start=start,
                end=end,
                room=room,   # placeholder — ignored by the CSP model
            )

    return time_blocks


def build_conflict_pairs(time_blocks: dict[str, TimeBlock]) -> list[tuple[str, str]]:
    """
    Compare every pair of sections and return those that conflict in time.

    This is the only function that contains time-overlap logic.
    Everything downstream (the CSP model) only sees a plain list of
    forbidden pairs — it has no knowledge of times or day patterns.

    Example results:
        MWF 08:00-08:50  vs  MWF 08:30-09:20  → CONFLICT  (same days, overlap)
        MWF 08:00-08:50  vs  TTh 08:00-09:15  → no conflict (no shared day)
        MWF 08:00-08:50  vs  MWF 09:00-09:50  → no conflict (back-to-back)
        MW  13:00-14:15  vs  MWF 13:00-13:50  → CONFLICT  (share M and W)
    """
    conflict_pairs: list[tuple[str, str]] = []
    section_list = list(time_blocks.keys())

    # combinations() gives every unique pair without repetition — (A,B) but not (B,A)
    for s1, s2 in combinations(section_list, 2):
        if _sections_conflict(time_blocks[s1], time_blocks[s2]):
            conflict_pairs.append((s1, s2))

    return conflict_pairs


def load_workload(path: str) -> dict[str, tuple[int, int]]:
    """
    Read workload.csv.

    Expected format (first row = header):
        faculty, min_sections, max_sections
        Dr. Smith, 1, 2
        Dr. Nguyen, 0, 1

    Returns:
        workload — workload[faculty_name] = (min_sections, max_sections)
    """
    workload: dict[str, tuple[int, int]] = {}

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            faculty = row["faculty"].strip()
            mn      = int(row["min_sections"].strip())
            mx      = int(row["max_sections"].strip())
            workload[faculty] = (mn, mx)

    return workload


def load_all(preferences_path, time_blocks_path, workload_path) -> SchedulingData:
    
    # load_preferences now returns 4 values instead of 3
    sections, faculty, preferences, exclusions = load_preferences(preferences_path)
    time_blocks    = load_time_blocks(time_blocks_path)
    conflict_pairs = build_conflict_pairs(time_blocks)
    workload       = load_workload(workload_path)

    print(f"[Loader] {len(sections)} sections | "
          f"{len(faculty)} faculty | "
          f"{len(conflict_pairs)} conflict pair(s) | "
          f"{len(exclusions)} exclusion(s)")

    return SchedulingData(
        sections=sections,
        faculty=faculty,
        preferences=preferences,
        conflict_pairs=conflict_pairs,
        workload=workload,
        exclusions=exclusions,
    )

# ══════════════════════════════════════════════════════════════════════
#  SECTION 3 — CSP MODEL BUILDER
#
#  Takes a SchedulingData object and populates a CP-SAT model with:
#    - Decision variables  x[section, faculty] ∈ {0, 1}
#    - Coverage constraint  — each section gets exactly one faculty
#    - Workload constraints — each faculty stays within load bounds
#    - Conflict constraints — no faculty double-booked in time
#    - Objective            — maximise total preference score
#
#  Nothing in this section reads from files or writes to files.
#  All inputs are plain Python types from SchedulingData.
# ══════════════════════════════════════════════════════════════════════

def build_csp(model: cp_model.CpModel, data: SchedulingData) -> BuiltModel:
    """
    Describe the faculty scheduling problem as a CSP inside `model`.

    This function only DESCRIBES the problem — it does not solve it.
    All model.add_*() and model.maximize() calls just register rules.
    The solver doesn't run until run_solver() is called.

    Parameters
    ----------
    model : cp_model.CpModel
        An empty CpModel to populate. Created by the caller so that
        the caller controls the model lifecycle.
    data : SchedulingData
        Loaded by load_all(). Contains sections, faculty, preferences,
        conflict_pairs, and workload.

    Returns
    -------
    BuiltModel
        The same model (now populated), plus the variable dict x and
        the section/faculty name lists needed by the solver.
    """
    sections = data.sections
    faculty  = data.faculty

    # ── Step 1: Create decision variables ─────────────────────────────
    #
    # x[s, f] is a boolean variable — 1 if faculty f teaches section s,
    # 0 otherwise. These are the only things the solver actually decides.
    #
    # The string key (s, f) is Python-side bookkeeping — OR-Tools
    # internally tracks each variable by an integer index, not by name.
    #
    # Total variables = len(sections) × len(faculty)
    # With 5 sections and 6 faculty → 30 boolean variables
    x: dict[tuple[str, str], cp_model.IntVar] = {}
    for s in sections:
        for f in faculty:
            x[s, f] = model.new_bool_var(f"x[{s},{f}]")

    # This is a hard constraint — unlike a negative preference score which
    # the solver can still choose if no better option exists, an exclusion
    # can never be overridden by the objective.
    for s, f in data.exclusions:
        model.add(x[s, f] == 0)

    # ── Step 2: Coverage constraint ───────────────────────────────────
    #
    # Every section must be assigned to EXACTLY ONE faculty member.
    # This enforces that every row in the output matrix sums to 1.
    #
    # Formally:  Σ_f  x[s, f]  =  1   for all sections s
    #
    # add_exactly_one() is more efficient than add(sum == 1) because
    # CP-SAT has a specialised propagator for this constraint type.
    for s in sections:
        model.add_exactly_one(x[s, f] for f in faculty)

    # ── Step 3: Workload constraints ──────────────────────────────────
    #
    # Each faculty member must teach at least min and at most max sections.
    # This operates on the column of the matrix — summing across all sections
    # for one faculty member.
    #
    # Formally:  min_f  ≤  Σ_s  x[s, f]  ≤  max_f   for all faculty f
    for f in faculty:
        min_load, max_load = data.workload[f]

        # Sum of all assignments in this faculty member's column
        total_assigned = sum(x[s, f] for s in sections)

        model.add(total_assigned >= min_load)
        model.add(total_assigned <= max_load)

    # ── Step 4: Time conflict constraints ─────────────────────────────
    #
    # For every pair of sections that overlap in time, no single faculty
    # member can be assigned to both. This prevents double-booking.
    #
    # Formally:  x[s1, f] + x[s2, f]  ≤  1
    #            for all (s1, s2) in conflict_pairs, for all faculty f
    #
    # The conflict_pairs list was computed entirely in Section 2 —
    # the model has no knowledge of times or day patterns.
    for s1, s2 in data.conflict_pairs:
        for f in faculty:
            model.add(x[s1, f] + x[s2, f] <= 1)

    # ── Step 5: Objective — maximise preference score ─────────────────
    #
    # Each assignment x[s, f] = 1 contributes preferences[s][f] to the
    # total score. The solver finds the assignment that maximises this sum.
    #
    # Formally:  max  Σ_{s,f}  preferences[s][f] · x[s, f]
    #
    # Because coverage forces exactly one x[s,f]=1 per section, only
    # len(sections) terms will be nonzero in the final solution.
    #
    # OR-Tools requires integer coefficients — preference scores are
    # already integers (-3 to +3) so no scaling is needed.
    objective_terms = [
        data.preferences[s][f] * x[s, f]
        for s in sections
        for f in faculty
        if data.preferences[s][f] != 0   # skip zero-score terms (no-op)
    ]
    model.maximize(sum(objective_terms))

    # Print a constraint count summary for debugging
    n_vars     = len(x)
    n_coverage = len(sections)
    n_workload = len(faculty) * 2
    n_conflict = len(data.conflict_pairs) * len(faculty)
    print(f"[CSP] {n_vars} variables | "
          f"{n_coverage} coverage | "
          f"{n_workload} workload | "
          f"{n_conflict} conflict constraints")

    return BuiltModel(model=model, x=x, sections=sections, faculty=faculty)


# ══════════════════════════════════════════════════════════════════════
#  SECTION 4 — SOLVER, VALIDATOR & OUTPUT  (formerly Person 3)
#
#  Runs the solver, validates the result, prints a summary,
#  and writes the output CSV.
#
#  Also contains standalone validation tests that can be run
#  independently to verify the pipeline is working correctly.
# ══════════════════════════════════════════════════════════════════════

def run_solver(built: BuiltModel,
               time_limit: float = SOLVER_TIME_LIMIT_SECONDS
               ) -> dict[str, str] | None:
    """
    Run the CP-SAT solver on the built model and extract the assignment.

    This is the only place where actual computation happens — everything
    before this was just describing the problem.

    Parameters
    ----------
    built      : BuiltModel from build_csp()
    time_limit : max wall-clock seconds before the solver gives up

    Returns
    -------
    assignment : dict[section_id → faculty_name]  if a solution was found
    None       : if the problem is INFEASIBLE or the solver TIMED OUT
    """
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.log_search_progress = False  # set True for verbose output

    print(f"\n[Solver] Running (time limit: {time_limit}s) ...")
    status = solver.solve(built.model)

    status_name = solver.status_name(status)
    print(f"[Solver] Status    : {status_name}")
    print(f"[Solver] Wall time : {solver.wall_time:.3f}s")

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        obj = solver.objective_value
        optimality = "optimal" if status == cp_model.OPTIMAL else "feasible (not proven optimal)"
        print(f"[Solver] Objective : {obj:.0f}  ({optimality})")

        # Extract which faculty was assigned to each section.
        # For each section, exactly one x[s, f] will be 1 (guaranteed by
        # the coverage constraint) — find it and record the faculty name.
        assignment: dict[str, str] = {}
        for s in built.sections:
            for f in built.faculty:
                if solver.value(built.x[s, f]) == 1:
                    assignment[s] = f
                    break  # move to next section once the 1 is found

        return assignment

    # Handle failure cases with descriptive messages
    if status == cp_model.INFEASIBLE:
        print("[Solver] ✗ INFEASIBLE — no valid assignment exists.")
        print("         Check: are workload bounds achievable given the number of sections?")
        print("         Check: are conflict constraints leaving any section unassignable?")
    elif status == cp_model.UNKNOWN:
        print(f"[Solver] ✗ TIMED OUT — no solution found within {time_limit}s.")
        print("         Try increasing SOLVER_TIME_LIMIT_SECONDS.")
    else:
        print(f"[Solver] Unexpected status: {status_name}")

    return None


def validate(assignment: dict[str, str], data: SchedulingData) -> ValidationReport:
    """
    Check that the solver's output satisfies all constraints.

    This is a sanity check — if the model is built correctly, the solver
    output should always pass. But running this catches bugs in the model
    or in the result-extraction code.

    Constraint checks:
        C1 — Coverage    : every section has exactly one assignment
        C2 — Valid names : all assigned faculty exist in the faculty list
        C3 — Workload    : each faculty's load is within [min, max]
        C4 — Conflicts   : no faculty assigned to two time-conflicting sections

    Warnings (valid but worth flagging):
        W1 — Negative preference score in the final assignment
        W2 — Faculty with zero sections assigned (if min_load was 0)
    """
    report = ValidationReport()

    # C1 — Every section must appear in the assignment
    for s in data.sections:
        if s not in assignment or assignment[s] is None:
            report.fail(f"C1 Coverage: section '{s}' was not assigned.")

    # C2 — Every assigned faculty must be in the known faculty list
    for s, f in assignment.items():
        if f not in data.faculty:
            report.fail(f"C2 Unknown faculty: '{f}' (assigned to '{s}') "
                        f"is not in the faculty list.")

    # C3 — Each faculty member's load must be within their workload bounds
    load: dict[str, int] = {f: 0 for f in data.faculty}
    for f in assignment.values():
        if f in load:
            load[f] += 1

    for f in data.faculty:
        mn, mx = data.workload[f]
        actual = load[f]
        if actual < mn:
            report.fail(f"C3 Workload: '{f}' assigned {actual} section(s), "
                        f"minimum is {mn}.")
        if actual > mx:
            report.fail(f"C3 Workload: '{f}' assigned {actual} section(s), "
                        f"maximum is {mx}.")

    # C4 — No faculty member can teach two sections that overlap in time
    for s1, s2 in data.conflict_pairs:
        f1 = assignment.get(s1)
        f2 = assignment.get(s2)
        if f1 and f2 and f1 == f2:
            report.fail(f"C4 Time Conflict: '{f1}' assigned to both "
                        f"'{s1}' and '{s2}', which overlap in time.")

    # C5 — No excluded (section, faculty) pair should appear in the assignment
    for s, f in data.exclusions:
        if assignment.get(s) == f:
            report.fail(f"C5 Exclusion violated: '{f}' was assigned to '{s}' "
                        f"despite being marked as excluded.")

    # W1 — Flag negative preference assignments (valid but suboptimal)
    for s, f in assignment.items():
        score = data.preferences.get(s, {}).get(f, 0)
        if score < 0:
            report.warn(f"W1 Negative preference: '{f}' has score {score:+d} "
                        f"for section '{s}'.")

    return report


def print_summary(assignment: dict[str, str], data: SchedulingData) -> None:
    """Print a formatted human-readable schedule to the terminal."""

    print(f"\n{'═' * 62}")
    print("  SCHEDULE SUMMARY")
    print(f"{'═' * 62}")

    # Section assignment table
    print(f"  {'Section':<14} {'Assigned Faculty':<20} {'Pref Score':>10}")
    print(f"  {'─' * 14} {'─' * 20} {'─' * 10}")

    total_score = 0
    for s in data.sections:
        f     = assignment.get(s, "UNASSIGNED")
        score = data.preferences.get(s, {}).get(f, 0) if f != "UNASSIGNED" else 0
        total_score += score
        flag  = "  ◄ negative" if score < 0 else ""
        print(f"  {s:<14} {f:<20} {score:>+10}{flag}")

    print(f"  {'─' * 44}")
    print(f"  {'Total preference score':.<34} {total_score:>+10}")

    # Faculty workload table
    print(f"\n  {'Faculty':<20} {'Assigned':>9}  {'Min':>4}  {'Max':>4}  Status")
    print(f"  {'─' * 20} {'─' * 9}  {'─' * 4}  {'─' * 4}  {'─' * 12}")

    load: dict[str, int] = {f: 0 for f in data.faculty}
    for f in assignment.values():
        if f in load:
            load[f] += 1

    for f in data.faculty:
        mn, mx = data.workload[f]
        n      = load[f]
        status = "✓ OK" if mn <= n <= mx else "✗ VIOLATION"
        print(f"  {f:<20} {n:>9}  {mn:>4}  {mx:>4}  {status}")

    print(f"{'═' * 62}\n")


def write_schedule_csv(assignment: dict[str, str],
                       sections: list[str],
                       faculty: list[str],
                       output_path: str) -> None:
    """
    Write the solver output to a CSV file in the same 0/1 matrix format
    used by the Schedule tab in the Excel workbook.

    Output format:
        section_id, Faculty A, Faculty B, Faculty C, ...
        CS101-A,    1,         0,          0,         ...
        CS101-B,    0,         1,          0,         ...
    """
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Header row — section_id followed by each faculty name
        writer.writerow(["section_id"] + faculty)

        # Data rows — 1 for the assigned faculty, 0 for all others
        for s in sections:
            assigned_faculty = assignment.get(s)
            row = [s] + [1 if fac == assigned_faculty else 0 for fac in faculty]
            writer.writerow(row)

    print(f"[Output] Schedule written → {output_path}")


# ══════════════════════════════════════════════════════════════════════
#  SECTION 5 — STANDALONE TESTS
#
#  These tests verify each part of the pipeline independently.
#  Run them directly:  python faculty_scheduling.py --test
#
#  Tests do not require real CSV files — they use inline sample data.
# ══════════════════════════════════════════════════════════════════════

def _make_sample_data() -> SchedulingData:
    """
    Build a small SchedulingData object from hardcoded values.
    Used by tests so they don't depend on external CSV files.

    Any negative preference score is treated as a hard exclusion —
    the score is set to 0 and the (section, faculty) pair is added
    to exclusions so the solver cannot assign them.
    """
    sections = ["CS101-A", "CS101-B", "CS202-A", "CS305-A", "CS410-A"]
    faculty  = ["Dr. Smith", "Dr. Jones", "Dr. Lee", "Dr. Patel", "Dr. Kim", "Dr. Nguyen"]

    raw_preferences = {
        "CS101-A": {"Dr. Smith": 3,  "Dr. Jones": 1,  "Dr. Lee": 0,
                    "Dr. Patel": -1, "Dr. Kim": 2,    "Dr. Nguyen": 1},
        "CS101-B": {"Dr. Smith": 2,  "Dr. Jones": 3,  "Dr. Lee": 1,
                    "Dr. Patel": 0,  "Dr. Kim": -1,   "Dr. Nguyen": 2},
        "CS202-A": {"Dr. Smith": 0,  "Dr. Jones": 2,  "Dr. Lee": 3,
                    "Dr. Patel": 1,  "Dr. Kim": -2,   "Dr. Nguyen": 0},
        "CS305-A": {"Dr. Smith": 1,  "Dr. Jones": -1, "Dr. Lee": 1,
                    "Dr. Patel": 2,  "Dr. Kim": 3,    "Dr. Nguyen": -1},
        "CS410-A": {"Dr. Smith": 2,  "Dr. Jones": 1,  "Dr. Lee": -1,
                    "Dr. Patel": 0,  "Dr. Kim": 3,    "Dr. Nguyen": 2},
    }

    # Convert negative scores to hard exclusions.
    # Any score below 0 → set to 0 in preferences and add to exclusions.
    # This mirrors what load_preferences() does when it reads 'x' from CSV.
    preferences: dict[str, dict[str, int]] = {}
    exclusions:  set[tuple[str, str]] = set()

    for s, scores in raw_preferences.items():
        preferences[s] = {}
        for f, score in scores.items():
            if score < 0:
                preferences[s][f] = 0        # neutralise the score
                exclusions.add((s, f))        # hard ban instead
            else:
                preferences[s][f] = score

    time_blocks = {
        "CS101-A": TimeBlock("CS101-A", "MWF", PATTERN_DAYS["MWF"],
                             time(8,  0), time(8,  50)),
        "CS101-B": TimeBlock("CS101-B", "TTh", PATTERN_DAYS["TTh"],
                             time(9, 30), time(10, 45)),
        "CS202-A": TimeBlock("CS202-A", "MWF", PATTERN_DAYS["MWF"],
                             time(10, 0), time(10, 50)),
        "CS305-A": TimeBlock("CS305-A", "MW",  PATTERN_DAYS["MW"],
                             time(10, 0), time(11, 15)),
        "CS410-A": TimeBlock("CS410-A", "TTh", PATTERN_DAYS["TTh"],
                             time(14, 30), time(15, 45)),
    }

    conflict_pairs = build_conflict_pairs(time_blocks)

    workload = {
        "Dr. Smith":  (1, 2),
        "Dr. Jones":  (1, 2),
        "Dr. Lee":    (1, 2),
        "Dr. Patel":  (1, 2),
        "Dr. Kim":    (1, 2),
        "Dr. Nguyen": (0, 1),
    }

    return SchedulingData(sections, faculty, preferences, conflict_pairs, workload, exclusions=exclusions)


def test_conflict_detection() -> None:
    """
    T1 — Verify that _sections_conflict() correctly identifies overlapping sections.
    """
    print("\n[Test T1] Conflict detection")

    # Should conflict — both MWF, times overlap (10:00–10:50 vs 10:00–11:15)
    a = TimeBlock("A", "MWF", PATTERN_DAYS["MWF"], time(10, 0), time(10, 50))
    b = TimeBlock("B", "MW",  PATTERN_DAYS["MW"],  time(10, 0), time(11, 15))
    assert _sections_conflict(a, b), "FAIL: MWF 10:00 vs MW 10:00 should conflict"
    print("  ✓ MWF 10:00–10:50  vs  MW 10:00–11:15  → conflict detected")

    # Should NOT conflict — different days entirely
    c = TimeBlock("C", "TTh", PATTERN_DAYS["TTh"], time(10, 0), time(11, 15))
    assert not _sections_conflict(a, c), "FAIL: MWF vs TTh should not conflict"
    print("  ✓ MWF 10:00–10:50  vs  TTh 10:00–11:15 → no conflict (different days)")

    # Should NOT conflict — back-to-back on same days
    d = TimeBlock("D", "MWF", PATTERN_DAYS["MWF"], time(10, 50), time(11, 40))
    assert not _sections_conflict(a, d), "FAIL: back-to-back sections should not conflict"
    print("  ✓ MWF 10:00–10:50  vs  MWF 10:50–11:40 → no conflict (back-to-back)")

    print("  T1 PASSED\n")


def test_end_time_derivation() -> None:
    """
    T2 — Verify that end times are correctly derived from day patterns.
    """
    print("[Test T2] End time derivation")

    cases = [
        ("MWF", time(8,  0),  time(8,  50)),   # 8:00 + 50min
        ("TTh", time(9, 30),  time(10, 45)),    # 9:30 + 75min
        ("MW",  time(13, 0),  time(14, 15)),    # 13:00 + 75min
    ]

    for pattern, start, expected_end in cases:
        derived = _derive_end_time(start, pattern)
        assert derived == expected_end, (
            f"FAIL: {pattern} {start} → expected {expected_end}, got {derived}"
        )
        print(f"  ✓ {pattern} {start.strftime('%H:%M')} → {derived.strftime('%H:%M')}")

    print("  T2 PASSED\n")


def test_full_pipeline() -> None:
    """
    T3 — Run the complete pipeline on sample data and verify the result.

    Checks:
      - Solver finds a solution
      - All constraints pass validation
      - No section is left unassigned
      - No faculty exceeds their workload
      - No faculty is double-booked on conflicting sections
    """
    print("[Test T3] Full pipeline on sample data")

    data = _make_sample_data()
    print(f"  Sections      : {data.sections}")
    print(f"  Faculty       : {data.faculty}")
    print(f"  Conflict pairs: {data.conflict_pairs}")

    # Build model
    model = cp_model.CpModel()
    built = build_csp(model, data)

    # Solve
    assignment = run_solver(built, time_limit=30.0)
    assert assignment is not None, "FAIL: solver returned no solution"
    print(f"  Assignment    : {assignment}")

    # Validate
    report = validate(assignment, data)
    report.print_report()
    assert report.passed, f"FAIL: validation errors: {report.errors}"

    print("  T3 PASSED\n")


def test_infeasible_detection() -> None:
    """
    T4 — Verify that the solver correctly identifies an infeasible problem.

    Makes it infeasible by setting all faculty max_load to 0
    while still requiring every section to be covered.
    """
    print("[Test T4] Infeasibility detection")

    data = _make_sample_data()

    # Override workload so no faculty can teach anything
    data.workload = {f: (0, 0) for f in data.faculty}

    model = cp_model.CpModel()
    built = build_csp(model, data)
    result = run_solver(built, time_limit=10.0)

    assert result is None, "FAIL: expected None for infeasible problem"
    print("  ✓ Solver correctly returned None for infeasible input")
    print("  T4 PASSED\n")


def test_exclusion_constraint() -> None:
    print("[Test T5] Exclusion constraint")

    data = _make_sample_data()

    # CS202-A / Dr. Kim is already excluded from sample data (was -2)
    # Verify the solver respects it
    assert ("CS202-A", "Dr. Kim") in data.exclusions, \
        "FAIL: expected CS202-A/Dr. Kim to be in exclusions"

    model = cp_model.CpModel()
    built = build_csp(model, data)
    assignment = run_solver(built, time_limit=30.0)

    assert assignment is not None, "FAIL: solver returned no solution"
    assert assignment.get("CS202-A") != "Dr. Kim", \
        "FAIL: Dr. Kim was assigned to CS202-A despite exclusion"

    print(f"  ✓ CS202-A assigned to {assignment['CS202-A']} (not Dr. Kim)")
    print("  T5 PASSED\n")


def run_all_tests() -> None:
    """Run all standalone tests."""
    print("=" * 50)
    print("  RUNNING ALL TESTS")
    print("=" * 50)
    test_end_time_derivation()
    test_conflict_detection()
    test_full_pipeline()
    test_infeasible_detection()
    test_exclusion_constraint()
    print("=" * 50)
    print("  ALL TESTS PASSED")
    print("=" * 50)


# ══════════════════════════════════════════════════════════════════════
#  SECTION 6 — ENTRY POINT
#  Parses arguments and runs either the full pipeline or the test suite.
# ══════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(description="Faculty scheduling solver")
    parser.add_argument("--preferences",  default="preferences.csv")
    parser.add_argument("--time_blocks",  default="time_blocks.csv")
    parser.add_argument("--workload",     default="workload.csv")
    parser.add_argument("--output",       default="schedule.csv")
    parser.add_argument("--test",         action="store_true",
                        help="Run standalone tests instead of the full pipeline")
    args = parser.parse_args()

    if args.test:
        run_all_tests()
        return

    # Step 1: Load all CSVs into SchedulingData ──────────────
    data = load_all(args.preferences, args.time_blocks, args.workload)

    # Step 2: Build the CSP model (unsolved) ──────────────────
    model = cp_model.CpModel()
    built = build_csp(model, data)

    # Step 3: Solve ───────────────────────────────────────────
    assignment = run_solver(built, time_limit=SOLVER_TIME_LIMIT_SECONDS)

    if assignment is None:
        print("No solution found. Exiting.")
        sys.exit(1)

    # Step 4: Validate the result ─────────────────────────────
    report = validate(assignment, data)
    report.print_report()

    if not report.passed:
        print("Validation failed — schedule NOT written.")
        sys.exit(1)

    # Step 5: Print human-readable summary ────────────────────
    print_summary(assignment, data)

    # Step 6: Write output CSV ────────────────────────────────
    write_schedule_csv(assignment, data.sections, data.faculty, args.output)


if __name__ == "__main__":
    main()

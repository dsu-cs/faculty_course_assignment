"""
faculty_scheduling.py
=====================
Faculty scheduling solver using Google OR-Tools CP-SAT.

Reads three CSV files as input:
    sections.csv    — course sections with enrollment data
    time.csv        — time block data per section
    preferences.csv — faculty preference scores (0-3 or x)
    workload.csv    — optional, per-faculty research units (defaults to 0)
    
Solves a Constraint Satisfaction Problem (CSP) to find the best
faculty-to-section assignment that satisfies all constraints.

Outputs:
    schedule.csv     — section x faculty assignment matrix (0/1)
    prints a human-readable summary to the terminal

Usage:
    python faculty_scheduling.py
    python faculty_scheduling.py --sections s.csv --time t.csv --preferences p.csv
    python faculty_scheduling.py --workload w.csv  (optional)
    python faculty_scheduling.py --test

CSV formats are described in each loader function below.
"""

from __future__ import annotations

import csv
import sys
import argparse
from dataclasses import dataclass, field
from datetime import time, datetime, timedelta
from itertools import combinations

from ortools.sat.python import cp_model


# ══════════════════════════════════════════════════════════════════════
#  SECTION 1 — CONSTANTS & DATA STRUCTURES
#  These are shared across all parts of the pipeline.
# ══════════════════════════════════════════════════════════════════════
# Default workbook path
DEFAULT_SECTIONS_PATH    = "sections.csv"
DEFAULT_TIME_PATH        = "time_blocks.csv"
DEFAULT_PREFERENCES_PATH = "preferences.csv"
DEFAULT_WORKLOAD_PATH    = "workload.csv"

# ── Workload configuration ────────────────────────────────────────────
FACULTY_MAX_WORKLOAD    = 30   # soft cap — total units per faculty per semester
OVERLOAD_PENALTY        = 10   # preference points lost per unit over cap
DEFAULT_COURSE_WORKLOAD =  4   # fallback units per section if current_workload missing

# Solver time limit — increase for larger problems
SOLVER_TIME_LIMIT_SECONDS = 60.0

# Maps any known column name variation → canonical field name.
# Headers are normalised (lowercased, spaces → underscores) before lookup.
# To support a new column name variation, add it on the LEFT side only.
# To add a new workload column, update the placeholder entries at the bottom.
HEADER_ALIASES: dict[str, str] = {
    # CRN
    "crn":              "crn",
    "course_ref":       "crn",
    "course_ref_num":   "crn",

    # Sections tab
    "sub":              "sub",
    "subject":          "sub",
    "num":              "num",
    "number":           "num",
    "course_num":       "num",
    "seq":              "seq",
    "section":          "seq",
    "crd":              "crd",
    "credits":          "crd",
    "credit":           "crd",
    "desc":             "desc",
    "description":      "desc",
    "course_name":      "desc",
    "title":            "desc",
    "seats":            "seats",
    "current_seats":    "current_seats",
    "enrolled":         "current_seats",
    "current":          "current_seats",
    "max_seats":        "max_seats",
    "capacity":         "max_seats",
    "max":              "max_seats",
    "waitlist":         "waitlist",
    "wait":             "waitlist",
    "faculty":          "faculty",
    "instructor":       "faculty",
    "professor":        "faculty",

    # Time tab
    "days":             "days",
    "day":              "days",
    "day_pattern":      "days",
    "pattern":          "days",
    "start_time":       "start_time",
    "start":            "start_time",
    "begin":            "start_time",
    "end_time":         "end_time",
    "end":              "end_time",
    "room":             "room",
    "location":         "room",
    "building":         "room",

    # ── Workload placeholders ─────────────────────────────────────────
    # Update the LEFT side when real column names are confirmed.
    # Do NOT change the RIGHT side — those match Section field names.
    "current_workload":     "current_workload",      # total workload units for section
    "workload_per_student": "workload_per_student",  # workload per enrolled student
    "research_workload":    "research_workload",     # unique/research section workload

    #per faculty workload stuff
    "research_units":   "research_units",
    "release_units":    "research_units",
    "research":         "research_units",
}

def _resolve_header(raw: str | None) -> str | None:
    """
    Normalise a raw header cell value and resolve it to a canonical
    field name via HEADER_ALIASES.

    Normalisation: strip whitespace, lowercase, replace spaces/hyphens
    with underscores. Returns None if the header is unrecognised —
    that column is silently skipped.
    """
    if raw is None:
        return None
    normalised = (
        raw.strip()
           .lower()
           .replace(" ", "_")
           .replace("-", "_")
    )
    return HEADER_ALIASES.get(normalised)


def _parse_days(days_str: str | None) -> frozenset[str] | None:
    """
    Convert a days string from the workbook into a frozenset of
    individual day characters for conflict detection.

    Handles any combination of day tokens:
        M  = Monday
        Tu = Tuesday
        W  = Wednesday
        Th = Thursday
        F  = Friday

    Examples:
        "MWF"   → frozenset({"M", "W", "F"})
        "TuTh"  → frozenset({"T", "H"})    (T=Tue, H=Thu to avoid collision)
        "MTuWF" → frozenset({"M", "T", "W", "F"})
        "W"     → frozenset({"W"})
        None    → None  (internet section)
    """
    if not days_str or not days_str.strip():
        return None

    days = set()
    s = days_str.strip()
    i = 0
    while i < len(s):
        if s[i:i+2] == "Tu":
            days.add("T")   # T = Tuesday
            i += 2
        elif s[i:i+2] == "Th":
            days.add("H")   # H = Thursday (avoids collision with T=Tuesday)
            i += 2
        elif s[i] == "T":
            # Bare T — treat as Tuesday (e.g. "TTh" → T + Th is handled above,
            # but "T" alone or "TT" edge cases land here as Tuesday)
            days.add("T")
            i += 1
        elif s[i] in ("M", "W", "F"):
            days.add(s[i])
            i += 1
        else:
            i += 1  # skip unrecognised characters

    return frozenset(days) if days else None


def _is_single_day(days: frozenset[str]) -> bool:
    """Return True if the section meets on exactly one day."""
    return len(days) == 1


def _parse_time(raw) -> time | None:
    """
    Parse a time value from a workbook cell.
    Accepts datetime.time objects (from Excel) or 'HH:MM' strings.
    Returns None if the value is missing or unparseable.
    """
    if raw is None:
        return None
    if isinstance(raw, time):
        return raw
    try:
        h, m = map(int, str(raw).strip().split(":"))
        return time(h, m)
    except (ValueError, AttributeError):
        return None

def _parse_seats(raw) -> tuple[int, int]:
    """
    Parse combined seats field — '18/25' → (18, 25).
    Falls back to (0, 0) if missing or unparseable.
    """
    if not raw:
        return 0, 0
    s = str(raw).strip()
    if "/" in s:
        parts = s.split("/", 1)
        try:
            cur = int(parts[0].strip())
            mx = int(parts[1].strip())
            # Sanity check — seat counts should be reasonable
            # A date like 12/11/2000 would give mx=2000 which is clearly wrong and sometimes happens due to bad excel formatting
            if cur > 999 or mx > 999:
                return 0, 0
            return cur, mx
        except ValueError:
            return 0, 0
    # Single number — treat as current seats, max unknown
    try:
        return int(s), 0
    except ValueError:
        return 0, 0

def _times_overlap(a_start: time, a_end: time,
                   b_start: time, b_end: time) -> bool:
    """
    Return True if time interval [a_start, a_end) overlaps [b_start, b_end).

    Back-to-back sections sharing only a boundary are NOT considered
    conflicting — a section ending at 09:00 does not conflict with one
    starting at 09:00.
    """
    return a_start < b_end and b_start < a_end


def _sections_conflict(a: "Section", b: "Section") -> bool:
    """
    Two sections conflict when BOTH conditions are true:
      1. They share at least one meeting day
      2. Their time intervals overlap

    Either condition alone is not enough — different-day sections never
    conflict regardless of time, and same-day back-to-back sessions don't.
    """
    if a.days is None or b.days is None:
        return False
    if not (a.days & b.days):
        return False
    if a.start is None or a.end is None or b.start is None or b.end is None:
        return False
    return _times_overlap(a.start, a.end, b.start, b.end)

@dataclass
class Section:
    """
    A single course section combining data from both the Sections tab
    and the Time tab, joined on CRN.

    Time fields (days, start, end, room) are None for internet sections.
    Bucket is determined after joining:
        days is None              → internet
        days has exactly one day  → single_day
        days has multiple days    → regular
    """
    # From Sections tab
    crn:           str
    sub:           str
    num:           str
    seq:           str
    crd:           str
    desc:          str
    current_seats: int
    max_seats:     int
    waitlist:      int
    faculty:       str 

    # From Time tab — None for internet sections
    days:  frozenset[str] | None = None
    start: time | None           = None
    end:   time | None           = None
    room:  str | None            = None

    # Workload placeholders ─────────────────────────────────────────
    # Update HEADER_ALIASES when real column names are confirmed.
    current_workload:     float | None = None  # total workload units for section
    workload_per_student: float | None = None  # workload per enrolled student
    research_workload:    float | None = None  # unique/research section workload



@dataclass
class SchedulingData:
    """
    All inputs the CSP model needs in clean Python types.
    Produced by load_all() and consumed by build_csp().

    Three section buckets — each contains full Section objects so the
    teammate has sub, num, desc, faculty for twin/dual-credit detection:

        regular    → MWF/TTh/MW/MTWF/etc. — sent to OR, conflict pairs built
        single_day → M/Tu/W/Th/F          — NOT sent to OR
        internet   → no days/time          — sent to OR, filter twins/dual credit/internet crosslisted?
    """
    regular:    list[Section]
    single_day: list[Section]
    internet:   list[Section]
    sections_to_solve: list[str] #THIS IS WHATS SENT TO THE OR SOLVER. SHOULD HAVE FILTERED DUAL CREDIT AND INTERNET SECTIONS
    faculty:          list[str]
    preferences:      dict[str, dict[str, int]]  # [crn][faculty] = score (0-3)
    exclusions:       set[tuple[str, str]]        # (crn, faculty) hard bans
    conflict_pairs:   list[tuple[str, str]]       # regular sections only
    workload:         dict[str, tuple[int, int]]  # [faculty] = (min_units, max_units)
    section_workload: dict[str, int]              # [crn] = workload units from current_workload


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
#  Reads sections.csv, time.csv, and preferences.csv delivered by the
#  Communications Server. Joins sections + time on CRN, then buckets.
#  No OR-Tools types used here — only plain Python.
#
#  CSV formats (header row required, column order does not matter):
#
#  sections.csv:
#      CRN, Sub, Num, Seq, Crd, Desc, Current Seats, Max Seats, Waitlist, Faculty
#
#  time.csv:
#      CRN, Sub, Days, Start Time, End Time, Room
#      (online sections have blank Days, Start Time, End Time, Room)
#
#  preferences.csv:
#      CRN, Faculty A, Faculty B, ...  (wide format — one column per faculty)
#      scores: 0-3 or x
# ══════════════════════════════════════════════════════════════════════

def _read_csv(path: str) -> list[dict]:
    records = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)

        header_row = next(reader, None)
        if header_row is None:
            return []

        # Skip title row if present — first cell is a label not a field name
        if _resolve_header(header_row[0]) is None:
            header_row = next(reader, None)
        if header_row is None:
            return []

        headers = [_resolve_header(cell) for cell in header_row]

        for row in reader:
            data = dict(zip(headers, row))
            crn = data.get("crn", "").strip()
            if not crn:
                continue
            data["crn"] = crn
            records.append(data)

    return records

def load_sections_csv(path: str) -> dict[str, dict]:
    """
    Read sections.csv.

    Returns a dict keyed by CRN. Time fields are not present here —
    they come from time.csv and are joined in load_all().
    """
    records = _read_csv(path)
    sections_by_crn = {rec["crn"]: rec for rec in records}
    print(f"[Loader] sections.csv: {len(sections_by_crn)} rows")
    return sections_by_crn

def load_time_csv(path: str) -> dict[str, dict]:
    """
    Read time.csv.

    Returns a dict keyed by CRN. Sections with no Days value are
    internet sections — they are still included here with blank fields.
    """
    records = _read_csv(path)
    time_by_crn = {rec["crn"]: rec for rec in records}
    print(f"[Loader] time.csv: {len(time_by_crn)} rows")
    return time_by_crn


def load_preferences_csv(path: str) -> tuple[list[str], list[str], dict[str, dict[str, int]], set[tuple[str, str]]]:
    """
    Read preferences.csv.

    Expected format (first row = header):
        section_id, Faculty A, Faculty B, Faculty C, ...
        CS101-A,    3,         1,          x,         ...

    Score values:
        0-3  — preference score (0 = neutral, 3 = strongly prefer)
        x    — hard exclusion, this faculty CANNOT be assigned to this section

    Returns:
        faculty     — ordered list of faculty names (from header)
        preferences — preferences[section][faculty] = int score (0–3)
        exclusions  — set of (section, faculty) pairs that are hard excluded
    """
    preferences: dict[str, dict[str, int]] = {}
    exclusions:  set[tuple[str, str]] = set()
    faculty:     list[str] = []

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)

        # Header row — col 0 = CRN identifier, col 1+ = faculty names
        header_row = next(reader, None)
        if header_row is None:
            return [], {}, set()


        # Skip title row if present — first cell is a label not a field name
        if _resolve_header(header_row[0]) is None and header_row[0].strip():
            header_row = next(reader, None)
        if header_row is None:
            return [], {}, set()

        faculty = [
            h.strip() for h in header_row[1:]
            if h and h.strip()
        ]

        for row in reader:
            if not row or not row[0].strip():
                continue

            crn = row[0].strip()
            preferences[crn] = {}

            for i, fac in enumerate(faculty):
                raw = row[i + 1].strip() if (i + 1) < len(row) else ""

                if not raw:
                    preferences[crn][fac] = 0
                elif raw.lower() == "x":
                    preferences[crn][fac] = 0
                    exclusions.add((crn, fac))
                else:
                    try:
                        preferences[crn][fac] = int(raw)
                    except ValueError:
                        preferences[crn][fac] = 0

    print(f"[Loader] preferences.csv: {len(preferences)} CRNs | "
          f"{len(faculty)} faculty | {len(exclusions)} exclusion(s)")
    return faculty, preferences, exclusions

def load_workload_csv(path: str) -> dict[str, int]:
    """
    Read workload.csv — optional per-faculty research unit assignments.

    Expected format:
        Faculty, Research Units/Buyout?
        Wendy Simmermon, 10
        Jeffrey E Elbert, 0

    Returns:
        dict[faculty_name → research_units_already_assigned]

    Faculty not in this file default to 0 research units,
    meaning their full FACULTY_MAX_WORKLOAD(30) cap is available.
    """
    research_units: dict[str, int] = {}

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)

        header_row = next(reader, None)
        if header_row is None:
            return {}

        # Skip title row if present
        if _resolve_header(header_row[0]) is None and header_row[0].strip():
            header_row = next(reader, None)
        if header_row is None:
            return {}

        for row in reader:
            if not row or not row[0].strip():
                continue
            faculty = row[0].strip()
            try:
                units = int(row[1].strip()) if len(row) > 1 else 0
            except ValueError:
                units = 0
            research_units[faculty] = units

    print(f"[Loader] workload.csv: {len(research_units)} faculty with research units")
    return research_units

def _build_section(sec_data: dict, time_data: dict | None) -> Section:
    """
    Combine a Sections tab row and its matching Time tab row (if any)
    into a single Section object.

    If time_data is None or has no Days value, the section is internet.
    """
    def safe_int(val, default: int = 0) -> int:
        try:
            return int(val) if val is not None else default
        except (ValueError, TypeError):
            return default

    # Parse seats — try combined "x/y" format first, fall back to separate columns
    _cur, _max = _parse_seats(sec_data.get("seats"))
    current_seats = _cur or safe_int(sec_data.get("current_seats"))
    max_seats     = _max or safe_int(sec_data.get("max_seats"))

    # Parse time fields — None if internet
    days_raw  = time_data.get("days")  if time_data else None
    days      = _parse_days(days_raw)
    start     = _parse_time(time_data.get("start_time")) if time_data else None
    end       = _parse_time(time_data.get("end_time"))   if time_data else None
    room      = str(time_data.get("room") or "").strip() or None if time_data else None

    return Section(
        crn           = sec_data.get("crn", ""),
        sub           = str(sec_data.get("sub") or "").strip(),
        num           = str(sec_data.get("num") or "").strip(),
        seq           = str(sec_data.get("seq") or "").strip(),
        crd           = str(sec_data.get("crd") or "").strip(),
        desc          = str(sec_data.get("desc") or "").strip(),
        current_seats = current_seats,
        max_seats     = max_seats,
        waitlist      = safe_int(sec_data.get("waitlist")),
        faculty       = str(sec_data.get("faculty") or "").strip(),
        days          = days,
        start         = start,
        end           = end,
        room          = room,
        # Workload fields — read from CSV if present, None if column not yet added
        # current_workload is active now; per_student and research pending workload.py
        current_workload     = safe_int(sec_data.get("current_workload")) or None,
        workload_per_student = safe_int(sec_data.get("workload_per_student")) or None,
        research_workload    = safe_int(sec_data.get("research_workload")) or None,
    )

def build_conflict_pairs(regular: list[Section]) -> list[tuple[str, str]]:
    """
    Compare every pair of regular sections and return those that conflict.

    Only regular sections are checked — single_day and internet sections
    are never in conflict pairs.

    Two sections conflict when:
      1. They share at least one meeting day
      2. Their time intervals overlap (back-to-back is NOT a conflict)
    """
    pairs: list[tuple[str, str]] = []

    for a, b in combinations(regular, 2):
        if _sections_conflict(a, b):
            pairs.append((a.crn, b.crn))

    return pairs

def load_all(
    #sections_path:    str = DEFAULT_SECTIONS_PATH,

    sections_path:    str | None = DEFAULT_SECTIONS_PATH, #  MAKING IT OPTIONAL FOR CD
    time_path:        str = DEFAULT_TIME_PATH,
    preferences_path: str = DEFAULT_PREFERENCES_PATH,
    workload_path:    str | None = DEFAULT_WORKLOAD_PATH,
) -> SchedulingData:
    """
    Master loader — reads all three CSVs and returns a SchedulingData
    object ready for build_csp().

    Steps:
      1. Read sections.csv  → dict keyed by CRN
      2. Read time.csv      → dict keyed by CRN
      3. Join on CRN        → Section objects
      4. Bucket sections    → regular / single_day / internet
      5. Read preferences.csv → faculty list, scores, exclusions
      6. Build conflict pairs from regular sections only
    """
    # ── Step 1 & 2: Read CSVs ────────────────────────────────────────
    time_by_crn     = load_time_csv(time_path)

    try:
        sections_by_crn = load_sections_csv(sections_path)
    except (FileNotFoundError, TypeError):
        print("[Loader] sections.csv not found — deriving from time_blocks.csv")
        sections_by_crn = {
                crn: {
                    "crn":     crn,
                    "sub":     data.get("sub", ""),
                    "num":     "", "seq": "", "crd": "",
                    "desc":    "", "seats": "", "waitlist": "0",
                    "faculty": "",
                }
                for crn, data in time_by_crn.items()
            }
        
    # ── Step 3 & 4: Join and bucket ───────────────────────────────────
    regular:    list[Section] = []
    single_day: list[Section] = []
    internet:   list[Section] = []

    for crn, sec_data in sections_by_crn.items():
        time_data = time_by_crn.get(crn)
        section   = _build_section(sec_data, time_data)

        if section.days is None:
            # No days value → internet section
            internet.append(section)
        elif _is_single_day(section.days):
            # Exactly one day → single_day bucket
            single_day.append(section)
        else:
            # Multiple days → regular bucket
            regular.append(section)

    # ── Step 5: Read Preferences ──────────────────────────────────────
    faculty, preferences, exclusions = load_preferences_csv(preferences_path)

    # ── Step 6: Conflict pairs — regular only ─────────────────────────
    conflict_pairs = build_conflict_pairs(regular)

    # ── Section workload units ───────────────────────────────────────
    # Read current_workload from each section. Defaults to DEFAULT_COURSE_WORKLOAD if missing.
    # so the constraint is always unit-based, never section-count based.
    all_sections = regular + single_day + internet
    section_workload: dict[str, int] = {}
    for sec in all_sections:
        try:
            units = int(sec.current_workload) if sec.current_workload is not None else DEFAULT_COURSE_WORKLOAD
        except (ValueError, TypeError):
            units = DEFAULT_COURSE_WORKLOAD
        section_workload[sec.crn] = units

    # ── Faculty workload bounds ───────────────────────────────────────
    # min=0 (no hard minimum), max=FACULTY_MAX_WORKLOAD units (soft cap)
    # If workload.csv not provided or faculty not listed, full cap is used.
    try:
        research_units = load_workload_csv(workload_path)
    except (FileNotFoundError, TypeError):
        research_units = {}
    workload = {f: (0, max(0,FACULTY_MAX_WORKLOAD - research_units.get(f,0))) for f in faculty}

    print(f"[Loader] regular={len(regular)} | "
          f"single_day={len(single_day)} | "
          f"internet={len(internet)} | "
          f"conflict_pairs={len(conflict_pairs)} | "
          f"workload units per section={set(section_workload.values())}")

    # filter linked internet twins and dual credit here before this list is built
    # Only what's in this list gets sent to OR
    sections_to_solve = ([s.crn for s in regular] + [s.crn for s in internet])

    return SchedulingData(
        regular          = regular,
        single_day       = single_day,
        internet         = internet,
        sections_to_solve= sections_to_solve, #This is what OR sees
        faculty          = faculty,
        preferences      = preferences,
        exclusions       = exclusions,
        conflict_pairs   = conflict_pairs,
        workload         = workload,
        section_workload = section_workload,
    )
    


def build_csp(model: cp_model.CpModel, data: SchedulingData) -> BuiltModel:
    """
    Describe the faculty scheduling CSP inside `model`.

    Sections sent to OR: regular + internet (single_day excluded).
    Conflict constraints: regular sections only.
    Workload: soft cap of FACULTY_MAX_WORKLOAD from workload.py.
    """
    # CRNs sent to the solver - regular + internet that is not filtered out
    sections = data.sections_to_solve
    faculty  = data.faculty

    # x[crn, faculty] = 1 if that faculty is assigned to that section
    x: dict[tuple[str, str], cp_model.IntVar] = {}
    for s in sections:
        for f in faculty:
            x[s, f] = model.new_bool_var(f"x[{s},{f}]")

    # Hard ban — x[s, f] = 0 for all (s, f) marked x in Preferences
    for s, f in data.exclusions:
        if s in sections:   # only apply to sections OR is solving for
            model.add(x[s, f] == 0)

    # Every section must be assigned to exactly one faculty member
    for s in sections:
        model.add_exactly_one(x[s, f] for f in faculty)

    # Workload is measured in units (from section_workload)
    # Each assigned section contributes its current_workload units
    # to the faculty member's total. The cap (FACULTY_MAX_WORKLOAD) is
    # a soft limit — slack allows overload but the objective penalises it.
    slack_vars = {}
    max_possible_units = sum(data.section_workload.get(s, 1) for s in sections)


    for f in faculty:
        mn, mx = data.workload[f]

        # Total workload units for this faculty member
        total_units = sum(
            data.section_workload.get(s, 1) * x[s, f]
            for s in sections
        )

        # Hard minimum units (usually 0)
        if mn > 0:
            model.add(total_units >= mn)

        # Soft maximum — slack absorbs overload, penalised in objective
        slack = model.new_int_var(0, max_possible_units, f"slack_{f}")
        model.add(total_units <= mx + slack)
        slack_vars[f] = slack

    # No faculty can be assigned to two regular sections that overlap.
    # Internet sections have no time so they never appear in conflict_pairs.
    for s1, s2 in data.conflict_pairs:
        for f in faculty:
            model.add(x[s1, f] + x[s2, f] <= 1)

    preference_terms = [
        data.preferences.get(s, {}).get(f, 0) * x[s, f]
        for s in sections
        for f in faculty
        if data.preferences.get(s, {}).get(f, 0) != 0
    ]

    overload_penalty_terms = [
        OVERLOAD_PENALTY * slack_vars[f]
        for f in faculty
    ]

    model.maximize(sum(preference_terms) - sum(overload_penalty_terms))

    # Summary
    n_vars     = len(x)
    n_coverage = len(sections)
    n_conflict = len(data.conflict_pairs) * len(faculty)
    print(f"[CSP] {n_vars} variables | "
          f"{n_coverage} coverage | "
          f"{n_conflict} conflict constraints | "
          f"soft workload cap={FACULTY_MAX_WORKLOAD}")

    return BuiltModel(model=model, x=x, sections=sections, faculty=faculty)

# ══════════════════════════════════════════════════════════════════════
#  SECTION 4 — SOLVER, VALIDATOR & OUTPUT
# ══════════════════════════════════════════════════════════════════════

def run_solver(built: BuiltModel,
               time_limit: float = SOLVER_TIME_LIMIT_SECONDS
               ) -> dict[str, str] | None:
    """
    Run the CP-SAT solver on the built model and extract the assignment.

    This is the only place where actual computation happens — everything
    before this was just describing the problem.

    Returns:
        dict[crn → faculty_name]  if a solution was found
        None                      if INFEASIBLE or TIMED OUT
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
        C5 — Exclusions  : no x-marked pair was assigned

    Warnings (valid but worth flagging):
        W1 — Negative preference score in the final assignment
    """
    report = ValidationReport()

    or_sections = data.sections_to_solve

    # C1 — Every section must appear in the assignment
    for crn in or_sections:
        if crn not in assignment or assignment[crn] is None:
            report.fail(f"C1 Coverage: section '{crn}' was not assigned.")

    # C2 — Every assigned faculty must be in the known faculty list
    for crn, f in assignment.items():
        if f not in data.faculty:
            report.fail(f"C2 Unknown faculty: '{f}' assigned to '{crn}'.")

    # C3 — Each faculty member's load must be within their workload bounds
    load_units: dict[str, int] = {f: 0 for f in data.faculty}
    for crn, f in assignment.items():
        if f in load_units:
            load_units[f] += data.section_workload.get(crn, 1)

    for f in data.faculty:
        mn, mx = data.workload[f]
        actual = load_units[f]
        if actual < mn:
            report.fail(f"C3 Workload: '{f}' assigned {actual} units, "
                        f"minimum is {mn} units.")
        if actual > mx:
            report.warn(f"W2 Workload: '{f}' assigned {actual} units, "
                        f"soft cap is {mx} units (overload penalty applied).")

    # C4 — No faculty member can teach two sections that overlap in time
    for s1, s2 in data.conflict_pairs:
        f1 = assignment.get(s1)
        f2 = assignment.get(s2)
        if f1 and f2 and f1 == f2:
            report.fail(f"C4 Time Conflict: '{f1}' assigned to both "
                        f"'{s1}' and '{s2}', which overlap in time.")

    # C5 — No excluded (section, faculty) pair should appear in the assignment
    for crn, f in data.exclusions:
        if assignment.get(crn) == f:
            report.fail(f"C5 Exclusion violated: '{f}' was assigned to '{crn}' "
                        f"despite being marked as excluded.")

    # W1 — Flag negative preference assignments (valid but suboptimal)
    for crn, f in assignment.items():
        score = data.preferences.get(crn, {}).get(f, 0)
        if score <= 0:
            report.warn(f"W1 Negative preference: '{f}' has score {score:+d} "
                        f"for section '{crn}'.")

    return report


def print_summary(assignment: dict[str, str], data: SchedulingData) -> None:
    """Print a formatted human-readable schedule to the terminal."""

    print(f"\n{'═' * 62}")
    print("  SCHEDULE SUMMARY")
    print(f"{'═' * 62}")

    # Section assignment table
    print(f"  {'CRN':<10} {'Assigned Faculty':<25} {'Score':>6}")
    print(f"  {'─' * 10} {'─' * 25} {'─' * 6}")

    total_score = 0
    or_sections = data.sections_to_solve

    for crn in or_sections:
        f     = assignment.get(crn, "UNASSIGNED")
        score = data.preferences.get(crn, {}).get(f, 0) if f != "UNASSIGNED" else 0
        total_score += score
        print(f"  {crn:<10} {f:<25} {score:>+6}")

    print(f"  {'─' * 41}")
    print(f"  {'Total preference score':.<35} {total_score:>+6}")

    print(f"\n  {'Faculty':<25} {'Units':>6}  {'Sections':>9}  {'Cap':>4}  {'Research':>9}  Status")
    print(f"  {'─'*25} {'─'*6}  {'─'*9}  {'─'*4}  {'─'*9}  {'─'*12}")

    unit_load: dict[str, int] = {f: 0 for f in data.faculty}
    sect_load: dict[str, int] = {f: 0 for f in data.faculty}
    for crn, f in assignment.items():
        if f in unit_load:
            unit_load[f] += data.section_workload.get(crn, 1)
            sect_load[f] += 1

    for f in data.faculty:
        _, mx = data.workload[f]
        units = unit_load[f]
        sects = sect_load[f]
        research = FACULTY_MAX_WORKLOAD - mx   # research = cap reduction
        status = "✓ OK" if units <= mx else f"⚠ +{units - mx} over cap"
        print(f"  {f:<25} {units:>6}  {sects:>9}  {mx:>4}  {research:>9}  {status}")

    print(f"\n  Single-day sections (not scheduled): {len(data.single_day)}")
    print(f"{'═' * 62}\n")

def write_schedule_csv(assignment: dict[str, str],
                       data: SchedulingData,
                       output_path: str) -> None:
    """
    Write the solver output to a CSV file.

    Output format (0/1 matrix):
        crn, Faculty A, Faculty B, ...
        70346, 1, 0, ...
    """
    faculty  = data.faculty
    sections = data.sections_to_solve

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["crn"] + faculty)
        for crn in sections:
            assigned = assignment.get(crn)
            row = [crn] + [1 if fac == assigned else 0 for fac in faculty]
            writer.writerow(row)

    print(f"[Output] Schedule written → {output_path}")


# ══════════════════════════════════════════════════════════════════════
#  SECTION 5 — STANDALONE TESTS
#
#
#  Tests that verify pure logic functions without requiring CSV files.
#  Run with: python faculty_scheduling.py --test
#
#  T1 — Day pattern parsing
#  T2 — Conflict detection
# ══════════════════════════════════════════════════════════════════════

def test_day_parsing() -> None:
    """T1 — Verify _parse_days() handles all day pattern variations."""
    print("\n[Test T1] Day pattern parsing")

    cases = [
        ("MWF",   frozenset({"M", "W", "F"})),
        ("TTh",   frozenset({"T", "H"})),
        ("TuTh",  frozenset({"T", "H"})),
        ("MW",    frozenset({"M", "W"})),
        ("MTuWF", frozenset({"M", "T", "W", "F"})),
        ("W",     frozenset({"W"})),
        ("Tu",    frozenset({"T"})),
        ("Th",    frozenset({"H"})),
        (None,    None),
    ]

    for raw, expected in cases:
        result = _parse_days(raw)
        assert result == expected, f"FAIL: '{raw}' → {result}, expected {expected}"
        print(f"  ✓ '{raw}' → {result}")

    print("  T1 PASSED\n")


def test_conflict_detection() -> None:
    """T2 — Verify conflict detection using provided end times."""
    print("[Test T2] Conflict detection")

    def sec(crn, days_str, start_t, end_t):
        return Section(
            crn=crn, sub="X", num="100", seq="D01", crd="3",
            desc="Test", current_seats=0, max_seats=0, waitlist=0,
            faculty="", days=_parse_days(days_str),
            start=start_t, end=end_t,
        )

    a = sec("A", "MWF",   time(10, 0),  time(10, 50))
    b = sec("B", "MW",    time(10, 0),  time(11, 15))
    c = sec("C", "TTh",   time(10, 0),  time(11, 15))
    d = sec("D", "MWF",   time(10, 50), time(11, 40))
    e = sec("E", "MTuWF", time(8, 0),   time(8, 50))
    f = sec("F", "MWF",   time(8, 0),   time(8, 50))

    assert _sections_conflict(a, b),     "FAIL: MWF/MW same time should conflict"
    assert not _sections_conflict(a, c), "FAIL: MWF vs TTh should not conflict"
    assert not _sections_conflict(a, d), "FAIL: back-to-back should not conflict"
    assert _sections_conflict(e, f),     "FAIL: MTuWF vs MWF share M,W,F should conflict"

    print("  ✓ MWF 10:00–10:50  vs  MW 10:00–11:15  → conflict")
    print("  ✓ MWF 10:00–10:50  vs  TTh 10:00–11:15 → no conflict")
    print("  ✓ MWF 10:00–10:50  vs  MWF 10:50–11:40 → no conflict (back-to-back)")
    print("  ✓ MTuWF 8:00–8:50  vs  MWF 8:00–8:50   → conflict (share M,W,F)")
    print("  T2 PASSED\n")


def run_all_tests() -> None:
    print("=" * 50)
    print("  RUNNING ALL TESTS")
    print("=" * 50)
    test_day_parsing()
    test_conflict_detection()
    print("=" * 50)
    print("  ALL TESTS PASSED")
    print("=" * 50)


# ══════════════════════════════════════════════════════════════════════
#  SECTION 6 — ENTRY POINT
#  Parses arguments and runs either the full pipeline or the test suite.
# ══════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(description="Faculty scheduling solver")
    
    parser.add_argument("--sections", default=DEFAULT_SECTIONS_PATH,
                        help="Path to sections.csv (optional — derived from time_blocks.csv if not found)")
    parser.add_argument("--time",        default=DEFAULT_TIME_PATH,
                        help="Path to time.csv")
    parser.add_argument("--preferences", default=DEFAULT_PREFERENCES_PATH,
                        help="Path to preferences.csv")
    parser.add_argument("--workload", default=DEFAULT_WORKLOAD_PATH,
                        help="Optional path to workload.csv (faculty research units)")
    parser.add_argument("--output",   default="schedule.csv",
                        help="Output path for the schedule CSV")
    parser.add_argument("--test",     action="store_true",
                        help="Run T1/T2 logic tests (no CSV files required)")
    args = parser.parse_args()

    if args.test:
        run_all_tests()
        return

    # Step 1 — Load CSVs
    data = load_all(args.sections, args.time, args.preferences, args.workload)

    # Step 2 — Build model
    model = cp_model.CpModel()
    built = build_csp(model, data)

    # Step 3 — Solve
    assignment = run_solver(built, time_limit=SOLVER_TIME_LIMIT_SECONDS)

    if assignment is None:
        print("No solution found. Exiting.")
        sys.exit(1)

    # Step 4 — Validate
    report = validate(assignment, data)
    report.print_report()

    if not report.passed:
        print("Validation failed — schedule NOT written.")
        sys.exit(1)

    # Step 5 — Summary
    print_summary(assignment, data)

    # Step 6 — Write output
    write_schedule_csv(assignment, data, args.output)


if __name__ == "__main__":
    main()
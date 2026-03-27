"""
Workload configuration and calculation for the faculty scheduling solver.

This module owns all workload-related constants and logic so that changes
to the workload formula do not require touching faculty_scheduling.py.

Current state: simple section-count based workload with a soft cap of 30
units per faculty member. Formula-based calculation (credits x enrollment
x level multiplier)

Import in faculty_scheduling.py:
    from workload import FACULTY_MAX_WORKLOAD
"""

from __future__ import annotations

# ── Workload cap ──────────────────────────────────────────────────────
# Maximum workload units a faculty member can be assigned per semester.
# This is a SOFT constraint — the solver penalises exceeding it but will
# do so if no feasible solution exists within the cap.
FACULTY_MAX_WORKLOAD: int = 30

# ── Penalty for exceeding the soft cap ───────────────────────────────
# Each unit over FACULTY_MAX_WORKLOAD costs this many preference points.
# Raise this value to make the solver try harder to stay within the cap.
OVERLOAD_PENALTY: int = 10
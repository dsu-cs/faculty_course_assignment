from ortools.sat.python import cp_model
import sys
sys.path.append("Solver")

from faculty_scheduling import load_all, build_csp, run_solver, validate, write_schedule_csv, print_summary

# Step 1 — load the CSVs
data = load_all(
    preferences_path="data/preferences.csv",
    time_blocks_path="data/time_blocks.csv",
    workload_path="data/workload.csv",
)

# Step 2 — build the model
model = cp_model.CpModel()
built = build_csp(model, data)

# Step 3 — solve
assignment = run_solver(built)

# Step 4 — handle the result
if assignment is None:
    print("No solution found.")
else:
    write_schedule_csv(assignment, data.sections, data.faculty, "output/schedule.csv")

# For validation
if assignment is not None:
    report = validate(assignment, data)
    report.print_report()

    if report.passed:
        print_summary(assignment, data)
        write_schedule_csv(assignment, data.sections, data.faculty, "output/schedule.csv")
    else:
        print("Validation failed — schedule not written.")

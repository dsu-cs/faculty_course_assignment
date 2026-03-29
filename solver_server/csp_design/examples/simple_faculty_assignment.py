"""
Simple Faculty Assignment CSP Example
Author: Muhammad Bhutta
Purpose: Demonstrate constraint satisfaction for faculty-course assignments

This is a simplified example to show how the solver works before
implementing the full system.
"""

from ortools.sat.python import cp_model


def simple_faculty_assignment():
    """
    Simple example: Assign 3 faculty to 5 courses
    
    Faculty:
    - Alice (baseline: 9 credits, max: 12)
    - Bob (baseline: 9 credits, max: 12)
    - Charlie (baseline: 9 credits, max: 12)
    
    Courses:
    - CSC 150 (3 credits)
    - CSC 250 (3 credits)
    - CSC 350 (3 credits)
    - CSC 450 (3 credits)
    - CSC 770 (4 credits, graduate)
    """
    
    print("=" * 60)
    print("Simple Faculty-Course Assignment Example")
    print("=" * 60)
    
    # Create the model
    model = cp_model.CpModel()
    
    # Data
    faculty = ['Alice', 'Bob', 'Charlie']
    courses = ['CSC150', 'CSC250', 'CSC350', 'CSC450', 'CSC770']
    credits = {
        'CSC150': 3,
        'CSC250': 3,
        'CSC350': 3,
        'CSC450': 3,
        'CSC770': 4
    }
    
    # Faculty preferences (-3 to +3)
    preferences = {
        ('Alice', 'CSC150'): 3,   # Alice loves intro courses
        ('Alice', 'CSC250'): 2,
        ('Alice', 'CSC350'): 0,
        ('Alice', 'CSC450'): -2,
        ('Alice', 'CSC770'): -3,  # Alice avoids grad courses
        
        ('Bob', 'CSC150'): -1,
        ('Bob', 'CSC250'): 1,
        ('Bob', 'CSC350'): 2,
        ('Bob', 'CSC450'): 3,     # Bob loves upper-level
        ('Bob', 'CSC770'): 0,
        
        ('Charlie', 'CSC150'): -2,
        ('Charlie', 'CSC250'): 0,
        ('Charlie', 'CSC350'): 1,
        ('Charlie', 'CSC450'): 2,
        ('Charlie', 'CSC770'): 3,  # Charlie loves grad courses
    }
    
    # Qualifications (X = cannot teach)
    # Alice cannot teach CSC 770 (not qualified for grad courses)
    cannot_teach = [('Alice', 'CSC770')]
    
    # STEP 1: Create variables
    # One binary variable for each (faculty, course) pair
    assignments = {}
    for f in faculty:
        for c in courses:
            if (f, c) not in cannot_teach:
                var_name = f'{f}_{c}'
                assignments[(f, c)] = model.NewBoolVar(var_name)
            else:
                # Don't create variable if cannot teach
                assignments[(f, c)] = None
    
    print(f"\nCreated {sum(1 for v in assignments.values() if v is not None)} variables")
    
    # STEP 2: HARD CONSTRAINT - Each course must have exactly one instructor
    for c in courses:
        course_vars = [assignments[(f, c)] for f in faculty if assignments[(f, c)] is not None]
        model.Add(sum(course_vars) == 1)
    
    print("Added H4: Section coverage constraints (each course has 1 instructor)")
    
    # STEP 3: HARD CONSTRAINT - Faculty workload cannot exceed maximum (12 credits)
    max_workload = 12
    for f in faculty:
        faculty_vars = []
        for c in courses:
            if assignments[(f, c)] is not None:
                faculty_vars.append(assignments[(f, c)] * credits[c])
        
        if faculty_vars:
            model.Add(sum(faculty_vars) <= max_workload)
    
    print("Added H1: Workload maximum constraints (≤12 credits per faculty)")
    
    # STEP 4: SOFT CONSTRAINT - Maximize preference satisfaction
    # Convert preferences to objective weights
    objective_terms = []
    for (f, c), pref in preferences.items():
        if assignments[(f, c)] is not None:
            weight = pref * 10  # Scale: +3 becomes 30, -3 becomes -30
            objective_terms.append(assignments[(f, c)] * weight)
    
    model.Maximize(sum(objective_terms))
    print("Added S1: Preference maximization objective")
    
    # STEP 5: Solve
    print("\n" + "=" * 60)
    print("Solving...")
    print("=" * 60)
    
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    
    # STEP 6: Display results
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print(f"\nStatus: {'OPTIMAL' if status == cp_model.OPTIMAL else 'FEASIBLE'}")
        print(f"Objective value (preference score): {solver.ObjectiveValue()}")
        print("\nAssignments:")
        print("-" * 60)
        
        # Show assignments by faculty
        for f in faculty:
            print(f"\n{f}:")
            total_credits = 0
            total_pref = 0
            
            for c in courses:
                if assignments[(f, c)] is not None and solver.Value(assignments[(f, c)]):
                    course_credits = credits[c]
                    course_pref = preferences[(f, c)]
                    total_credits += course_credits
                    total_pref += course_pref
                    
                    pref_str = f"{course_pref:+d}" if course_pref != 0 else " 0"
                    print(f"  - {c} ({course_credits} credits, preference: {pref_str})")
            
            print(f"  Total: {total_credits} credits, preference sum: {total_pref:+d}")
        
        print("\n" + "=" * 60)
        print("Solution found successfully!")
        print("=" * 60)
        
    else:
        print("\nNo solution found!")
        print("This might mean constraints are too restrictive.")
    
    return status


if __name__ == '__main__':
    simple_faculty_assignment()
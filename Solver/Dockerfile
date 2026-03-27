FROM python:3.13-slim
 
# Metadata
LABEL description="Faculty Scheduling Solver — Google OR-Tools CP-SAT"
 
WORKDIR /app
 
# Install ortools (and openpyxl, as noted in Solver/README.md)
RUN pip install --no-cache-dir ortools openpyxl
 
# Copy solver source
COPY src/faculty_scheduling.py .

# Required CSVs
COPY preferences.csv time_blocks.csv ./

# Optional CSVs — silently skipped if not present
COPY sections.cs[v] workload.cs[v] ./
 
# Output directory — mount a host path here to retrieve schedule.csv
RUN mkdir -p /app/output
 
# Run the solver by default; pass --test to run the test suite instead.
# Input paths and output path are overridable via CLI args:
#   --preferences, --time_blocks, --workload, --output
ENTRYPOINT ["python", "faculty_scheduling.py"]
CMD ["--output", "/app/output/schedule.csv"]

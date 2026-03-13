# Faculty Course Assignment tool

A constraint satisfaction solver tool to help deans and chairs assign faculty to courses based on faculty preferences.

To build & run this tool, use the [Docker guide](docs/docker.md).

## Components
 
| Component | Description |
|---|---|
| [Solver](Solver/README.md) | CP-SAT constraint solver — assigns faculty to sections based on preferences, workload limits, and time conflicts |
 
## Quick Start
 
See the [Docker guide](docs/docker.md) for full setup instructions.
 
### Run the solver
 
```bash
# Build and run the solver against the bundled sample CSVs
docker compose run --rm solver
 
# Output lands in ./solver-output/schedule.csv
```
 
```bash
# Run the solver test suite (no CSV files needed)
docker compose run --rm solver --test
```
 
### Run the full stack (webserver + database)
 
```bash
cp .env.example .env
docker compose up -d postgres
```
 
## CI
 
GitHub Actions workflows live in `.github/workflows/`.
 
| Workflow | Triggers on | What it does |
|---|---|---|
| `solver-ci.yml` | Changes to `Solver/` | Builds the solver image, runs the test suite, runs a full solve against sample CSVs, uploads `schedule.csv` as a build artifact |

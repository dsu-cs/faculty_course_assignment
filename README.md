# Faculty Course Assignment tool

A constraint satisfaction solver tool to help deans and chairs assign faculty to courses based on faculty preferences.

To build & run this tool, use the [Docker guide](docs/docker.md).

## Components
 
| Component | Description |
|---|---|
| [Solver](Solver/README.md) | CP-SAT constraint solver — assigns faculty to sections based on preferences, workload limits, and time conflicts |
| [Web Server](webserver/README.md) | Faculty interface for submitting course preferences. Assembler of workbook through BIM scraping for the deans. |
 
## Quick Start
 
See the [Docker guide](docs/docker.md) for full setup instructions.
 
 
### Run the full stack (webserver + database)
 
```bash
cp .env.example .env
docker compose up -d postgres
```

### Run just the webserver component
cd into webserver folder
```bash
cp .env.example .env
docker compose -f docker-compose.local.yml up --build
```
 
## CI
 
GitHub Actions workflows live in `.github/workflows/`.
 
| Workflow | Triggers on | What it does |
|---|---|---|
| `solver-ci.yml` | Changes to `Solver/` | Builds the solver image, runs the test suite, runs a full solve against sample CSVs, uploads `schedule.csv` as a build artifact |

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


### Run the servers (webserver, postgres DB)

```bash
cp .env.example .env  # change envs accordingly
sudo docker compose build
sudo docker compose up
# sudo docker compose down  # shut down all the containers
```

Refer to the [official Docker documentation](https://docs.docker.com/compose/) for seeing logs, bringing up individual containers, etc.

## CI
GitHub Actions workflows live in `.github/workflows/`.

| Workflow | Triggers on | What it does |
|---|---|---|
| `solver-ci.yml` | Changes to `Solver/` | Builds the solver image, runs the test suite, runs a full solve against sample CSVs, uploads `schedule.csv` as a build artifact || `lint.yml` | `push`, `pull_request` | Validates YAML syntax/format across the repository |
| `compose-builds.yml` | `push`, `pull_request` | Builds and runs Docker Compose services, checks container health |
| `cd.yml` | `push` to `main`, manual dispatch | Deploys app to remote VM via SSH and Docker Compose |
| `solver-ci.yml` | Changes to `Solver/` | Builds the solver image, runs the test suite, runs a full solve against sample CSVs, uploads `schedule.csv` as a build artifact |


## Current Status 

**Communications Feature:**  Complete - Integration testing phase
- Flask server deployed and running (138.247.13.5:5000)
- CSV converter updated to match PR #24 format
- Solver integration complete (file-based workflow)
- Awaiting code reviews and end-to-end testing

**CSV Format:**  Standardized via PR #24
- sections.csv, time_blocks.csv, preferences.csv (required)
- workload.csv (optional)

**VBA Integration:**  In Progress
- Awaiting VBA code push from Lindsey Crow
- Windows 11 VM available for off-campus testing 

**Active PRs:**
- #11: CSV Converter (in review)
- Flask Integration: Server-solver integration (in review)


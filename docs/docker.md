# Docker Structure
We are using Docker Compose for the project, and our services currently include:
- [`postgres`](#postgres)

## Postgres
Our backend database for the web server.
- Uses an internal `backend` docker network for communication

# Build & Run the Project
- Install the official [Docker Compose](https://docs.docker.com/compose/install/)
- Navigate to the project's root directory (`faculty_course_assignment`)
- Create a `.env` file based on `.env.example`
- Spin up the Compose project with `docker compose up -d`
- Bring the project down with `docker compose down`

For a quick guide on usage, including seeing logs, running containers, and understanding `docker-compose.yml`, read the [docs](https://docs.docker.com/compose/intro/compose-application-model/)
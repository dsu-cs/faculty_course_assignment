# Docker Structure
We are using Docker Compose for the project, and our services currently include:
- [`django`](#django)
- [`postgres`](#postgres)

## Django
Our frontend for the web server.
- Uses a CookieCutter template application
- Custom Bootstrap CSS overrides for the styling from [DSU Brand Manual](https://dsu.edu/marketing/_files/DSU-Brand-Manual_web.pdf)

## Postgres
Our backend database for the web server.
- Uses an internal `backend` docker network for communication

# Build & Run the Project
- Install the official [Docker Compose](https://docs.docker.com/compose/install/)
- Navigate to the project's root directory (`faculty_course_assignment`)
- Create a root `.env` file based on `.env.example` (root compose variables)
- Create webserver env files from examples:
  - `webserver/.envs/.local/.django` from `webserver/.envs/.local/.django.example`
  - `webserver/.envs/.local/.postgres` from `webserver/.envs/.local/.postgres.example`
- Spin up the Compose project with `docker compose up -d`
- Bring the project down with `docker compose down`

For a quick guide on usage, including seeing logs, running containers, and understanding `docker-compose.yml`, read the [docs](https://docs.docker.com/compose/intro/compose-application-model/)

## Mailtrap for Local Magic-Link Emails
- Use Mailtrap SMTP for local development so real inboxes are never used.
- Add these values to `webserver/.envs/.local/.django`:
  - `DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`
  - `EMAIL_HOST=sandbox.smtp.mailtrap.io`
  - `EMAIL_PORT=2525`
  - `EMAIL_HOST_USER=<mailtrap-username>`
  - `EMAIL_HOST_PASSWORD=<mailtrap-password>`
  - `EMAIL_USE_TLS=true`
- Configure magic-link behavior:
  - `MAGIC_LINK_JWT_SECRET=<random-secret>`
  - `MAGIC_LINK_TTL_MINUTES=30`
  - `MAGIC_LINK_ALLOWED_DOMAIN=dsu.edu`
- Start the stack with `docker compose up -d`, request a login link in the app, and open the Mailtrap inbox to click the magic link.

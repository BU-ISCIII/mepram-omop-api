# MePRAM API

Read-only Django/DRF API for aggregated MePRAM dashboard data generated from OMOP data.

This MVP intentionally exposes dashboard aggregates, not the full operational/genomic MePRAM domain. It covers cohort summaries, OMOP domains, concepts, facts and measurements. Isolate-level workflows such as ST, carbapenemases, genomic alerts or Microreact need another source of data.

## Installation

### Docker Test Installation

This is the recommended entry point for local development, smoke tests and frontend integration work.

The local test stack starts two services:

- `mepram_api`: Django API running inside a container
- `mepram_db`: MySQL database running inside a container

The database is stored in a Docker volume, so the stack can be stopped and started without losing data unless the volume is explicitly removed.

#### Prerequisites

Before starting, make sure the machine has:

- `git`
- Docker Engine
- Docker Compose plugin (`docker compose`)

Check the tooling:

```bash
git --version
docker --version
docker compose version
```

#### 1. Clone The Repository

```bash
git clone https://github.com/Aberdur/mepram-api.git
cd mepram-api
git checkout develop
```

#### 2. Configure The Local Stack

```bash
cp .env.example .env
```

Relevant local settings:

```text
MEPRAM_DB_NAME=mepram_api
MEPRAM_DB_USER=mepram
MEPRAM_DB_PASSWORD=mepram_password
MEPRAM_DB_PORT_HOST=6608
MEPRAM_API_PORT=8100
MEPRAM_CORS_ALLOWED_ORIGINS=http://127.0.0.1:3000,http://localhost:3000
```

#### 3. Build And Start

Run the container installer from the repository root:

```bash
bash container_install.sh --test --git_revision current
```

Optionally, if this is the first time installing the images, you should provide a path to the SQL database:

```bash
bash container_install.sh --test --git_revision current --dashboard_sql path/to/dashboard.sql
```

This command will:

* build the application image
* start `app` and `db`
* install the Django project inside the container
* run database migrations
* load the dashboard tables into the DB

The test compose runs Django migrations on startup. The dashboard tables are Django-managed models, aligned with the PathoCore API approach: schema changes are represented in `core/models.py` and tracked through migrations.

The dashboard dump can also be uploaded later, by running the following commands

```bash
docker compose -f docker-compose.test.yml exec mepram_api mkdir -p /data
docker compose -f docker-compose.test.yml cp /path/to/dashboard.sql mepram_api:/data/dashboard.sql
```

Then load the current dashboard dump into the migrated MySQL schema:

```bash
docker compose -f docker-compose.test.yml exec mepram_api \
  python manage.py import_dashboard_sql /data/dashboard.sql --truncate
```

#### 4. Check The Stack

```bash
docker compose -f docker-compose.test.yml ps
curl http://127.0.0.1:8100/v1/health
```

Useful URLs:

- API health: `http://127.0.0.1:8100/v1/health`
- OpenAPI: `http://127.0.0.1:8100/openapi/`
- Swagger: `http://127.0.0.1:8100/swagger/`

#### 5. Useful Commands

Follow API logs:

```bash
docker compose -f docker-compose.test.yml logs -f mepram_api
```

Open a shell in the API container:

```bash
docker compose -f docker-compose.test.yml exec mepram_api bash
```

Open a MySQL shell:

```bash
docker compose -f docker-compose.test.yml exec mepram_db \
  mysql -umepram -pmepram_password mepram_api
```

Run Django checks:

```bash
docker compose -f docker-compose.test.yml run --rm --no-deps \
  mepram_api python manage.py check
```

Stop the containers but keep the database volume:

```bash
docker compose -f docker-compose.test.yml down
```

Stop the containers and remove the database volume:

```bash
docker compose -f docker-compose.test.yml down -v
```

## Main Endpoints

- `GET /v1/health`
- `GET /v1/metadata`
- `GET /v1/capabilities`
- `GET /v1/cohort/summary`
- `GET /v1/domains`
- `GET /v1/domains/{domain_id}/concepts`
- `GET /v1/concepts`
- `GET /v1/concepts/{concept_id}`
- `GET /v1/concepts/{concept_id}/detail`
- `GET /v1/facts/concepts`
- `GET /v1/measurements/numeric`
- `GET /v1/measurements/categorical`

Aggregate endpoints support common filters such as `q`, `event_type`, `limit`, `offset` and `stratification=none|age|sex|age_sex` where applicable.

## Reloading Dashboard Data

To reload the dump into the existing database:

```bash
docker compose -f docker-compose.test.yml exec mepram_api \
  python manage.py import_dashboard_sql /data/dashboard.sql --truncate
```

To recreate the local database from scratch:

```bash
docker compose -f docker-compose.test.yml down -v
docker compose -f docker-compose.test.yml up -d --build
```

Use `down -v` only when you want to discard the local test database completely.

## PathoCore Web Integration

For local frontend integration, configure `pathocore-web` with:

```text
VITE_USE_CASE_DATA_MODE=mepram-api
VITE_MEPRAM_API_BASE_URL=http://127.0.0.1:8100/v1
```

The MePRAM API CORS allowlist is controlled with:

```text
MEPRAM_CORS_ALLOWED_ORIGINS=http://127.0.0.1:3000,http://localhost:3000
```

## Current Scope

Covered by `dashboard.sql`:

- clinical cohort summaries
- OMOP domains and concepts
- concept aggregates
- numeric and categorical measurements
- age, sex and age+sex stratifications

Not covered by `dashboard.sql`:

- isolate-level explorer
- ST and clonality
- carbapenemases or AMR gene calls
- genomic alerts
- Microreact exports
- real territorial/center operational coverage

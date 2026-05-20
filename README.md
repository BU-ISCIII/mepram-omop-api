# MePRAM API

Read-only Django/DRF API for the aggregated PostgreSQL `dashboard` schema generated from OMOP data.

This MVP intentionally exposes dashboard aggregates, not the full operational/genomic MePRAM domain. It covers cohort summaries, OMOP domains, concepts, facts and measurements. Isolate-level workflows such as ST, carbapenemases, genomic alerts or Microreact need another source of data.

## Installation

### Docker Test Installation

This is the recommended entry point for local development, smoke tests and frontend integration work.

The local test stack starts two services:

- `mepram_api`: Django API running inside a container
- `mepram_db`: PostgreSQL database running inside a container

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

Place `dashboard.sql` two directories above this repository, or set `MEPRAM_DASHBOARD_SQL_PATH` in `.env`.

```bash
cp .env.example .env
```

Relevant local settings:

```text
MEPRAM_DASHBOARD_SQL_PATH=../../dashboard.sql
MEPRAM_DB_NAME=mepram_dashboard
MEPRAM_DB_USER=mepram
MEPRAM_DB_PASSWORD=mepram_password
MEPRAM_API_PORT=8100
MEPRAM_CORS_ALLOWED_ORIGINS=http://127.0.0.1:3000,http://localhost:3000
```

#### 3. Build And Start

```bash
docker compose -f docker-compose.test.yml up -d --build
```

The test compose imports `dashboard.sql` into PostgreSQL on first database volume creation.

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

Open a PostgreSQL shell:

```bash
docker compose -f docker-compose.test.yml exec mepram_db \
  psql -U mepram -d mepram_dashboard
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

PostgreSQL imports `dashboard.sql` only when the database volume is first created. To reload the dump from scratch:

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

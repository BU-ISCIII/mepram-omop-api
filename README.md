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

## API Reference

All endpoints are read-only and are exposed under `/v1`. The API serves Django-managed dashboard tables imported from `dashboard.sql`; it does not query OMOP source tables directly.

Common query parameters:

- `q`: case-insensitive text search over concept names where supported.
- `limit`: maximum rows to return. Default `100`, maximum `1000`.
- `offset`: first row to return. Default `0`.
- `event_type`: filters aggregate tables by event type, for example `current` if present in the loaded dump.
- `stratification`: aggregate shape for fact and measurement endpoints. Accepted values are `none`, `age`, `sex`, `age_sex`.

### `GET /v1/health`

Operational health endpoint. It verifies database connectivity and checks every Django-managed dashboard table.

Response fields:

- `status`: `UP` when all dashboard tables exist, `DEGRADED` when the database is reachable but one or more tables are missing, `DOWN` when the database cannot be queried.
- `schema`: configured dashboard schema/database name.
- `tables`: one item per dashboard table with `table`, `exists` and `row_count`.
- `checked_at`: ISO timestamp of the check.

Use this endpoint after migrations and imports to confirm that the API is backed by the expected tables and row counts.

### `GET /v1/metadata`

Returns global metadata used by clients to build filters and navigation.

Response fields:

- `schema`: configured dashboard schema/database name.
- `domains`: list of OMOP domains with `domain_id`, `medical_concepts` and `participants`.
- `event_types`: distinct event types available in concept aggregates.
- `age_groups`: distinct cohort age groups.
- `genders`: distinct cohort gender labels.
- `vocabularies`: distinct OMOP vocabularies present in the concept catalogue.
- `total_patients`: number of patients in `dim_patient`.
- `capabilities`: feature flags returned by `/v1/capabilities`.

### `GET /v1/capabilities`

Returns boolean feature flags describing the current API scope. It explicitly marks clinical aggregates, age/sex stratifications and numeric/categorical measurements as supported, and isolate explorer/genomic alerts as unsupported.

### `GET /v1/cohort/summary`

Returns cohort-level patient distributions from `dim_patient`.

Response fields:

- `total_patients`: total patients in the dashboard cohort.
- `by_age`: rows with `age_group` and `patients`.
- `by_sex`: rows with `gender` and `patients`.
- `by_age_sex`: rows with `age_group`, `gender` and `patients`.

This endpoint is intended for high-level cohort cards and demographic charts.

### `GET /v1/domains`

Lists OMOP domains available in the dashboard.

Query parameters:

- `q` optional. When omitted, values come from `fact_domain`. When provided, the API searches matching concept names and recomputes domain-level distinct concept and patient counts from `events_long`.

Response rows:

- `domain_id`: OMOP domain label, for example `Condition` or `Measurement`.
- `medical_concepts`: number of distinct concepts in that domain.
- `participants`: number of distinct patients represented in that domain.

### `GET /v1/domains/{domain_id}/concepts`

Lists concepts for one OMOP domain and reports how many patients have evidence for each concept.

Path parameters:

- `domain_id`: OMOP domain to inspect.

Query parameters:

- `q` optional concept-name search.
- `limit`, `offset` for pagination.

Response fields:

- `domain_id`: requested domain.
- `total_participants`: distinct patients with at least one matching event in the requested domain.
- `data`: concept rows with `concept_id`, `concept_name`, `vocabulary_id`, `concept_code`, `participants` and `pct`.

`pct` is the concept participant count over the whole dashboard cohort, not over only the selected domain.

### `GET /v1/concepts`

Searches the imported OMOP concept catalogue without returning aggregate counts.

Query parameters:

- `q` optional concept-name search.
- `domain_id` optional exact OMOP domain filter.
- `vocabulary_id` optional exact vocabulary filter.
- `limit`, `offset` for pagination.

Response rows:

- `concept_id`: OMOP concept identifier.
- `concept_name`: display name.
- `domain_id`: OMOP domain.
- `vocabulary_id`: source vocabulary.
- `concept_code`: source concept code.

### `GET /v1/concepts/{concept_id}`

Returns catalogue metadata for one concept. It returns `404` with `{"error": "Concept not found"}` when the concept is not loaded.

Use `/v1/concepts/{concept_id}/detail` when aggregate counts, stratifications or measurement summaries are needed.

### `GET /v1/concepts/{concept_id}/detail`

Returns a dashboard detail view for one concept.

Query parameters:

- `event_type` optional. When provided, all aggregate sections are filtered to that event type.

Response fields:

- `concept`: concept metadata.
- `summary`: overall rows with `event_type`, `record_count`, `record_pct_overall`, `patient_count` and `patient_pct`.
- `by_age`: rows with `event_type`, `age_group`, `patient_count`, `patient_pct_group` and `patient_pct_concept`.
- `by_sex`: rows with `event_type`, `gender`, `patient_count`, `patient_pct_group` and `patient_pct_concept`.
- `by_age_sex`: rows with `event_type`, `age_group`, `gender`, `patient_count`, `patient_pct_group` and `patient_pct_concept`.
- `measurements.numeric`: numeric measurement summaries for the same concept.
- `measurements.categorical`: categorical measurement summaries for the same concept.

Percentage semantics:

- `record_pct_overall`: record percentage over all records in the dashboard aggregate.
- `patient_pct`: patient percentage for the concept over the cohort.
- `patient_pct_group`: patient percentage within the age/sex stratum.
- `patient_pct_concept`: patient percentage of the concept distributed across strata.

### `GET /v1/facts/concepts`

Lists precomputed concept-level aggregates. This is the main endpoint for ranked clinical concept charts.

Query parameters:

- `q` optional concept-name search.
- `domain_id` optional exact domain filter.
- `event_type` optional exact event type filter.
- `stratification`: `none`, `age`, `sex`, `age_sex`.
- `limit`, `offset` for pagination.

Base response columns for every stratification:

- `concept_id`, `concept_name`, `domain_id`, `vocabulary_id`, `concept_code`, `event_type`.

Additional columns by stratification:

- `none`: `record_count`, `record_pct_overall`, `patient_count`, `patient_pct`.
- `age`: `age_group`, `patient_count`, `patient_pct_group`, `patient_pct_concept`.
- `sex`: `gender`, `patient_count`, `patient_pct_group`, `patient_pct_concept`.
- `age_sex`: `age_group`, `gender`, `patient_count`, `patient_pct_group`, `patient_pct_concept`.

### `GET /v1/measurements/numeric`

Lists numeric measurement aggregates, including descriptive statistics.

Query parameters:

- `q` optional concept-name search.
- `concept_id` optional exact concept filter.
- `event_type` optional exact event type filter.
- `stratification`: `none`, `age`, `sex`, `age_sex`.
- `limit`, `offset` for pagination.

Base response columns:

- `concept_id`, `concept_name`, `vocabulary_id`, `concept_code`, `event_type`, `unit_concept_id`, `unit_name`, `n_records`, `n_patients`, `mean_value`, `sd_value`, `min_value`, `q1_value`, `median_value`, `q3_value`, `max_value`.

When stratified, rows also include `age_group`, `gender` or both, depending on `stratification`.

### `GET /v1/measurements/categorical`

Lists categorical measurement aggregates, where each row represents a concept value/category.

Query parameters:

- `q` optional concept-name search.
- `concept_id` optional exact concept filter.
- `event_type` optional exact event type filter.
- `stratification`: `none`, `age`, `sex`, `age_sex`.
- `limit`, `offset` for pagination.

Base response columns:

- `concept_id`, `concept_name`, `vocabulary_id`, `concept_code`, `event_type`, `value_as_concept_id`, `value_concept_name`, `record_count`, `patient_count`.

Additional columns by stratification:

- `none`: `patient_pct`.
- `age`: `age_group`, `patient_pct_group`, `patient_pct_concept`.
- `sex`: `gender`, `patient_pct_group`, `patient_pct_concept`.
- `age_sex`: `age_group`, `gender`, `patient_pct_group`, `patient_pct_concept`.

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

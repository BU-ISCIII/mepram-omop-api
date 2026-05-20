# MePRAM API

Read-only Django/DRF API for the aggregated PostgreSQL `dashboard` schema generated from OMOP data.

This MVP intentionally exposes dashboard aggregates, not the full operational/genomic MePRAM domain. It covers cohort summaries, OMOP domains, concepts, facts and measurements. Isolate-level workflows such as ST, carbapenemases, genomic alerts or Microreact need another source of data.

## Local Test Stack

Place `dashboard.sql` next to this repository, or set `MEPRAM_DASHBOARD_SQL_PATH` in `.env`.

```bash
cp .env.example .env
docker compose -f docker-compose.test.yml up -d --build
```

The test compose imports `dashboard.sql` into PostgreSQL on first database volume creation.

URLs:

- API health: `http://127.0.0.1:8100/v1/health`
- OpenAPI: `http://127.0.0.1:8100/openapi/`
- Swagger: `http://127.0.0.1:8100/swagger/`

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

If you need to reload `dashboard.sql` from scratch:

```bash
docker compose -f docker-compose.test.yml down -v
docker compose -f docker-compose.test.yml up -d --build
```

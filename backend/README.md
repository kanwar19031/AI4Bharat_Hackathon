# KiranaStudio Backend

Initial FastAPI scaffold aligned with `PROTOTYPE_PLAN.md`.

## Structure

```
backend/
  app/
    main.py
    config/
    routes/
    services/
    repo/
    pipeline/
    models/
```

## Run

```bash
cd backend
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Current State

- API scaffold with `upload`, `jobs`, and `catalogs` endpoints.
- Background pipeline wiring with placeholder steps.
- DynamoDB-backed repositories (optional) with in-memory fallback.
- Placeholder S3/Bedrock behavior for local endpoint flow testing.

## DynamoDB setup (optional)

- Create tables from `backend/infra/dynamodb_jobs_table.json` and `backend/infra/dynamodb_catalogs_table.json`.
- Enable by setting `USE_AWS_DB=true` in `backend/.env` (or set AWS keys + leave `AUTO_USE_AWS_DB=true`).

Example (AWS CLI):

```bash
aws dynamodb create-table --cli-input-json file://backend/infra/dynamodb_jobs_table.json
aws dynamodb create-table --cli-input-json file://backend/infra/dynamodb_catalogs_table.json
```

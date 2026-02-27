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
- In-memory repository for jobs/catalogs as a temporary stand-in for DynamoDB.
- Placeholder S3/Bedrock behavior for local endpoint flow testing.


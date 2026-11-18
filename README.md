# Offer Ranker System

A small ML service that scores how likely a customer is to accept an upsell offer: a FastAPI + scikit-learn API, packaged in Docker, with Terraform and GitHub Actions for Google Cloud Run.

```
client ──POST /predict──▶ FastAPI (api/app) ──▶ models/offer_model.joblib (scikit-learn)
                              ├─ GET /health   GET /metrics
                              └─ container ──▶ Cloud Run (via Terraform / workflows, optional)
```

Not local: the Cloud Run deployment, Artifact Registry and Terraform need your own GCP project and secrets. Running and testing the API needs none of them. API details: [api/README.md](api/README.md).

## Prerequisites

- Python 3.11 or 3.12 (tests run on 3.12; scikit-learn 1.4.2 does not install on 3.14)
- Docker (only for the container path)
- Port 8080 free for `make run-local` (override with `PORT`)
- Not needed locally: a GCP account, Terraform, gcloud

## Run it

1. `cd api && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
2. `make run-local` (serves on `http://localhost:8080`)
3. `curl http://localhost:8080/health`
4. `curl -X POST http://localhost:8080/predict -H 'Content-Type: application/json' -d '{"age":30,"tenure_months":12,"monthly_spend":123.4,"num_support_tickets":1}'`

Container path: `docker build -t offer-ranker-api ./api`, then `docker run --rm -p 8080:8080 offer-ranker-api`.

If port 8080 is taken: `PORT=8090 make run-local`, or map a different host port with Docker (`-p 127.0.0.1::8080` picks a free one; `docker port <name>` shows which). Check what answers on the port: another service on 8080 will return its own 404, not this API's JSON.

## What it does

| Action | Result |
| --- | --- |
| `GET /health` | `200 {"status":"ok","model_loaded":true}`; `500` if the model failed to load |
| `POST /predict` with the four fields | `200` with `upsell_probability`, `upsell_label` (true at probability >= 0.5) and a `request_id` |
| `POST /predict` with a bad value (e.g. `age` -1, wrong type, extra field) | `422`, rejected by the strict schema in [api/app/schemas.py](api/app/schemas.py) |
| `GET /metrics` | In-process counters: total requests, prediction requests, average latency, last prediction time |

## Interface

| Method | Path | Auth |
| --- | --- | --- |
| GET | `/health` | none |
| GET | `/metrics` | none |
| POST | `/predict` | none |

## Tests

`cd api && pytest -q`: 10 tests (API, model loader, request validation), no external services. Note: running them rewrites the tracked `api/models/offer_model.joblib`; `git restore` it afterwards. On pull requests CI ([.github/workflows/pr-checks.yml](.github/workflows/pr-checks.yml)) runs the tests, a Docker build and a gitleaks scan on free runners. The cloud workflows (ci, cd, cd_dispatch, ci-cd, destroy) need GCP secrets and are not run on PRs. [api/scripts/smoke_test.sh](api/scripts/smoke_test.sh) checks `/health` and `/predict` against any running URL.

## Layout

| Path | Role |
| --- | --- |
| [api/app/](api/app/) | FastAPI service: [main.py](api/app/main.py), [schemas.py](api/app/schemas.py), [model_loader.py](api/app/model_loader.py) |
| [api/tests/](api/tests/) | pytest suite |
| [api/scripts/](api/scripts/) | [train_model.py](api/scripts/train_model.py), [smoke_test.sh](api/scripts/smoke_test.sh) |
| [api/infrastructure/](api/infrastructure/) | Terraform for the Cloud Run service |
| [api/orchestrate.py](api/orchestrate.py), [api/Makefile](api/Makefile) | Train / run / test / docker / terraform helpers |
| [dq/](dq/dq_cli.py) | YAML-driven data-quality CLI ([rules](dq/dq_rules.yaml)) |
| [training/](training/customer_upsell_propensity.ipynb) | Training notebook |
| [planned-features/](planned-features/ORDER_OF_OPERATIONS.md) | Design notes for future work; none of it is implemented |
| [.github/workflows/](.github/workflows/) | PR checks plus the manual/dev cloud pipelines |

## Design notes

- Strict request schema (`StrictInt`/`StrictFloat`, `extra=forbid`) instead of coercion: a string "30" is rejected rather than silently converted.
- A trained model file is committed (1.4 KB) so the container starts without a training step; the alternative, training at image build, would make builds slower and non-reproducible.
- The deploy workflows are separate from PR checks on purpose: PRs must never need cloud credentials.

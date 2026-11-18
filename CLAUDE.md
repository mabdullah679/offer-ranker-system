# offer-ranker-system

FastAPI + scikit-learn upsell-propensity service (`api/`), with Terraform and GCP workflows, a YAML data-quality CLI (`dq/`) and a training notebook. Global rules: `~/.claude/CLAUDE.md`. Repo facts only below.

## Commands (verified 2026-11-18, Python 3.12)
- `cd api && pip install -r requirements.txt && pytest -q` : 10 tests, all pass. Run from `api/` (model path is relative).
- `make train` (in `api/`) rewrites the tracked `api/models/offer_model.joblib`; running tests also modifies it. `git restore` it unless you mean to change the model.
- Local container: `docker build ./api`, run with `-p 127.0.0.1::8080`, then `api/scripts/smoke_test.sh http://localhost:<port>`.
- scikit-learn 1.4.2 has no wheel for Python 3.14: use 3.11/3.12.

## Layout
`api/app/` service (`/health`, `/metrics`, `/predict`), `api/tests/`, `api/infrastructure/` Terraform, `dq/` data-quality CLI, `training/` notebook, `planned-features/` design notes (not implemented), `.github/workflows/`.

## Do not touch / watch for
- `ci.yml`, `cd.yml`, `cd_dispatch.yml`, `ci-cd.yml`, `destroy.yml` are cloud pipelines (GCP, Terraform apply/destroy). Never run or edit them without the owner. `pr-checks.yml` is the free PR gate.
- Never commit `*.tfstate`, `terraform.tfvars` values, or service-account JSON (gitignored; `terraform.tfvars` is still tracked, owner decision pending).
- No cloud provisioning from agent sessions. Branch + PR only.

# Planned Features – Order of Operations

This order is optimized for skill-building on top of a small but complete MLOps foundation.

## 0) Baseline

- Make sure you can:
  - Run training locally (`make train`) and see `models/offer_model.joblib`.
  - Run the API locally (`make run-local`) and hit `/health` and `/predict`.
  - Understand the existing CI/CD + Terraform at a high level.

## 1) Observability & Quality (02)

- Implement first: it improves everything else and is valuable even for a tiny project.
- Focus on:
  - Structured JSON logging (no PII, no full payloads).
  - Basic metrics (latency, error rate, request count) via Cloud Run / Cloud Monitoring.
  - Input validation and clean 4xx/5xx handling.
- Outcome: you can see how the model behaves in “production” and debug issues.

## 2) Model Registry & Promotion (01)

- Next, make model versions explicit and deploy by version.
- Focus on:
  - A simple GCS-backed registry layout for model artifacts + metadata.
  - CI writing model metadata and emitting a `MODEL_VERSION`.
  - CD deploying a specific `MODEL_VERSION` and `/info` exposing it.
- Outcome: you control which model is live and can reason about history.

## 3) Release Safety & Rollback (03) – Minimal

- Add just enough safety for deploys; keep scope small.
- Focus on:
  - Always keeping the previous image tag.
  - A simple rollback path triggered on smoke-test failure.
  - (Optional) a tiny canary step using Cloud Run traffic split for learning.
- Outcome: you practice safer releases without overbuilding for this small project.

## 4) Automation & Scheduled Retrain (04)

- Treat this as “pipeline thinking” more than heavy infra.
- Focus on:
  - A repeatable `train_and_eval` entrypoint that runs locally or on GitHub runners.
  - Comparing new metrics to the current production model.
  - Writing updated artifacts/metadata into the registry (reusing step 2).
- Outcome: you think in terms of automated promotion criteria, not manual “best guess” deploys.

## 5) LMS Integration & RAG (05) – Experimental

- Do this last, only if you want LLM/RAG skills.
- Keep scope intentionally small:
  - A single additional “LLM-style” endpoint that uses a tiny local/hosted model.
  - A minimal retrieval layer with just a small in-memory or tiny persisted index.
  - At most ~50 test queries; no production traffic.
- Outcome: you get exposure to multi-model routing and RAG concepts without over-investing infra.

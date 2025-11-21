# Observability & Quality Guardrails

## Goal
Monitor API health, performance, and model output quality with actionable alerts.

## Scope (MVP)
- Metrics: request rate, error rate, latency (P50/P95/P99) via Cloud Monitoring; basic dashboards + alerting policies.
- Logs: structured JSON logs with request_id, model_version, latency, status, and input validation results.
- Payload validation: schema/range/type checks on inference payloads; reject/flag bad inputs.
- Output monitoring: log prediction distributions; compute simple drift/PSI on a schedule and alert on spikes.

## Steps
1) Add structured logging middleware (FastAPI) emitting JSON fields: `request_id`, `path`, `status`, `latency_ms`, `model_version`, `payload_valid`.
2) Add payload validation (`pydantic` schema + custom range checks); return 400 on invalid; log rejects.
3) Expose metrics to Cloud Monitoring (or push via OpenTelemetry/structured logs → log-based metrics). Create dashboards for latency/error.
4) Add alerting policies: high error rate, high P99 latency.
5) Add a scheduled job (Cloud Scheduler + Cloud Run job) to fetch recent predictions (from logs or a lightweight store), compute distribution shift (e.g., PSI) vs. training baseline, and emit alerts/metrics.

## Stretch
- Per-tenant/route metrics; SLO burn-rate alerts.
- Record payload fingerprints and outlier scores (whylogs).
- Trace context propagation for end-to-end latency.

## Dependencies
- Cloud Monitoring/Logging enabled; service account with logging/monitoring write.
- Baseline distribution stored from training (serialize stats with the model).

## Acceptance Criteria
- Dashboards show request/error/latency; alerts fire on configured thresholds.
- Invalid payloads are rejected with 400 and logged.
- Drift job runs on schedule and surfaces a metric/alert when deviation exceeds threshold.

## Risks/Notes
- Keep payload logging privacy-safe; avoid storing PII/raw payloads beyond what’s necessary for validation/drift.
- Alert only on actionable thresholds to avoid noise.

# LMS Integration & RAG

## Goal
Serve multiple small models (ads, ideation, etc.) with per-tenant context via lightweight RAG, configurable per connector/admin.

## Scope (MVP)
- API supports `model_id`/`model_version` parameter to pick a registered model; default to production version.
- Simple context store per tenant/admin: vector index + metadata (FAISS on disk or Firestore/SQLite + GCS snapshots).
- Optional web search enrichment if a tenant provides an API key.
- RAG flow: retrieve top-K context, build prompt, call the selected model, return response with source metadata.

## Steps
1) Extend API routes to accept `model_id`/`model_version`; resolve from registry; load the right artifact.
2) Add a lightweight retrieval module:
   - Ingest: accept text/docs, embed (small open-source model), store vectors + metadata.
   - Query: per-tenant top-K retrieval; source filtering.
3) Add optional web search connector gated by tenant-provided key; merge results into context.
4) Add an inference path for LLM-style responses (for ads/ideation): build prompt with retrieved context; return answer + sources.
5) Document admin flows: add connector, upload context, set default model per tenant.

## Stretch
- Multi-tenant isolation with separate indexes/buckets.
- Caching of retrieval results; rate limiting per tenant.
- Evaluation harness for RAG quality (e.g., retrieval recall/precision on a small labeled set).

## Dependencies
- Registry in place for model/version resolution.
- Context store (FAISS + GCS persistence or Firestore) and an embedding model/container.
- Optional search API key per tenant.

## Cost & Free Tier Considerations
- Treat LMS integration and RAG as conceptual and experimental only, with at most a small number of manual test queries (on the order of tens of requests).
- Prefer local or GitHub-hosted embedding and retrieval components; if GCP persistence is used, keep the vector index tiny so storage and compute stay negligible.
- If external LLM or search APIs are involved, rely on their free tiers and clearly scope usage to a handful of test runs, not continuous production traffic.
- Avoid always-on RAG services; spin up any supporting infrastructure only when testing, and tear it down or keep it local to prevent background charges.

## Acceptance Criteria
- API can route requests to different models by id/version.
- RAG path returns answers with source metadata; honors per-tenant context.
- Admin can add context and (optionally) a search key without code changes.

## Risks/Notes
- Keep PII and tenant data isolated; do not leak context across tenants.
- Control costs: small embedding models, minimal indexing, cache results.

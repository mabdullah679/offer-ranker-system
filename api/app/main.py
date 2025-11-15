"""FastAPI application for the upsell prediction service."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from app.config import settings
from app.logging_config import (
    LoggingMiddleware,
    get_metrics_snapshot,
    record_prediction_request,
    setup_logging,
)
from app.model_loader import ModelLoadError, load_default_model
from app.schemas import UpsellRequest, UpsellResponse

logger = logging.getLogger("offer_ranker")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    app.state.model = None  # type: ignore[attr-defined]
    app.state.model_loaded = False  # type: ignore[attr-defined]
    try:
        model = load_default_model()
    except ModelLoadError as exc:  # pragma: no cover - ensures visibility on startup failure
        logger.error("Failed to load model on startup: %s", exc)
    else:
        app.state.model = model  # type: ignore[attr-defined]
        app.state.model_loaded = True  # type: ignore[attr-defined]
        logger.info("Model loaded successfully from %s", settings.model_path)
    yield


app = FastAPI(title="Offer Ranker API", version="1.0.0", lifespan=lifespan)
app.add_middleware(LoggingMiddleware)


@app.get("/health")
async def health() -> JSONResponse:
    if not getattr(app.state, "model_loaded", False):
        raise HTTPException(status_code=500, detail="Model not loaded")
    return JSONResponse({"status": "ok", "model_loaded": True})


@app.get("/metrics")
async def metrics() -> dict[str, Any]:
    return get_metrics_snapshot()


@app.post("/predict", response_model=UpsellResponse)
async def predict(payload: UpsellRequest) -> UpsellResponse:
    if not getattr(app.state, "model_loaded", False) or app.state.model is None:  # type: ignore[attr-defined]
        raise HTTPException(status_code=500, detail="Model not available")

    model = app.state.model  # type: ignore[attr-defined]

    features = [[
        payload.age,
        payload.tenure_months,
        payload.monthly_spend,
        payload.num_support_tickets,
    ]]

    try:
        probabilities = model.predict_proba(features)
    except Exception as exc:  # pragma: no cover - should not happen but return clean error
        logger.exception("Prediction failed: %s", exc)
        raise HTTPException(status_code=500, detail="Prediction failed") from exc

    probability = float(probabilities[0][1])
    label = bool(probability >= 0.5)
    request_id = str(uuid4())

    record_prediction_request()

    return UpsellResponse(
        upsell_probability=probability,
        upsell_label=label,
        request_id=request_id,
    )

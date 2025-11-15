"""Logging configuration and middleware for structured logs and metrics."""
from __future__ import annotations

import logging
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

LOGGER_NAME = "offer_ranker"


def setup_logging(level: int = logging.INFO) -> None:
    if logging.getLogger(LOGGER_NAME).handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.propagate = False


@dataclass
class MetricsTracker:
    total_requests: int = 0
    prediction_requests: int = 0
    last_prediction_timestamp: Optional[str] = None
    total_latency_ms: float = 0.0
    request_count: int = 0
    _logger: logging.Logger = field(default_factory=lambda: logging.getLogger(LOGGER_NAME))

    def record_request(self, latency_ms: float) -> None:
        self.total_requests += 1
        self.request_count += 1
        self.total_latency_ms += latency_ms
        self._logger.debug("Recorded request latency_ms=%s", latency_ms)

    def record_prediction(self) -> None:
        self.prediction_requests += 1
        self.last_prediction_timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def snapshot(self) -> Dict[str, Any]:
        avg_latency = self.total_latency_ms / self.request_count if self.request_count else 0.0
        return {
            "total_requests": self.total_requests,
            "prediction_requests": self.prediction_requests,
            "last_prediction_timestamp": self.last_prediction_timestamp,
            "avg_latency_ms": round(avg_latency, 3),
        }


metrics_tracker = MetricsTracker()


class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:  # type: ignore[override]
        super().__init__(app)
        self.logger = logging.getLogger(LOGGER_NAME)

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception as exc:
            latency_ms = (time.perf_counter() - start) * 1000
            metrics_tracker.record_request(latency_ms)
            self.logger.exception(
                "path=%s method=%s status=500 latency_ms=%.2f request_id=%s error=%s",
                request.url.path,
                request.method,
                latency_ms,
                request_id,
                exc,
            )
            raise

        latency_ms = (time.perf_counter() - start) * 1000
        metrics_tracker.record_request(latency_ms)

        response.headers["x-request-id"] = request_id
        log_message = (
            "path=%s method=%s status=%s latency_ms=%.2f request_id=%s"
            % (request.url.path, request.method, response.status_code, latency_ms, request_id)
        )
        self.logger.info(log_message)
        return response


def record_prediction_request() -> None:
    metrics_tracker.record_prediction()


def get_metrics_snapshot() -> Dict[str, Any]:
    return metrics_tracker.snapshot()

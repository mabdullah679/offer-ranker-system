"""Model loading utilities."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib

from app.config import settings


class ModelLoadError(RuntimeError):
    """Raised when the model artifact cannot be loaded."""


def load_model(model_path: str | Path) -> Any:
    path = Path(model_path)
    if not path.exists():
        raise ModelLoadError(f"Model artifact missing at {path}")

    try:
        return joblib.load(path)
    except Exception as exc:  # pragma: no cover - defensive
        msg = f"Failed to load model artifact at {path}: {exc}"
        raise ModelLoadError(msg) from exc


def load_default_model() -> Any:
    return load_model(settings.model_path)

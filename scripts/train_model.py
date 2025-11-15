"""Training script for the upsell logistic regression model."""
from __future__ import annotations

import logging
import os
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

LOGGER = logging.getLogger("train_model")


MODEL_PATH = Path("models/offer_model.joblib")
RANDOM_SEED = 42


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def generate_synthetic_data(num_samples: int = 500) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(RANDOM_SEED)

    ages = rng.integers(18, 80, size=num_samples)
    tenure = rng.integers(0, 120, size=num_samples)
    monthly_spend = rng.uniform(20.0, 500.0, size=num_samples)
    support_tickets = rng.integers(0, 10, size=num_samples)

    logits = (
        0.02 * ages
        + 0.03 * tenure
        + 0.05 * monthly_spend
        - 0.1 * support_tickets
        - 20
    )
    probs = 1 / (1 + np.exp(-logits))
    target = rng.binomial(1, probs)

    features = np.column_stack((ages, tenure, monthly_spend, support_tickets))
    return features, target


def build_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "classifier",
                LogisticRegression(max_iter=500, solver="lbfgs", random_state=RANDOM_SEED),
            ),
        ]
    )


def train_and_save(model_path: Path = MODEL_PATH) -> Path:
    LOGGER.info("Starting training pipeline")
    X, y = generate_synthetic_data()
    LOGGER.info("Generated synthetic dataset with shape %s and target distribution %.2f%% positives", X.shape, 100 * y.mean())

    pipeline = build_pipeline()
    pipeline.fit(X, y)
    LOGGER.info("Model fitted successfully")

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_path)
    LOGGER.info("Model artifact saved to %s", model_path)
    return model_path


if __name__ == "__main__":
    configure_logging()
    try:
        artifact_path = train_and_save()
        LOGGER.info("Training completed. Artifact at %s", artifact_path.resolve())
    except Exception as exc:  # pragma: no cover - logged and re-raised for visibility
        LOGGER.exception("Training failed: %s", exc)
        raise

from pathlib import Path

import pytest

from app.model_loader import ModelLoadError, load_model
from scripts.train_model import train_and_save


def test_load_model_success(tmp_path):
    artifact_path = tmp_path / "offer_model.joblib"
    train_and_save(artifact_path)
    model = load_model(artifact_path)
    assert hasattr(model, "predict_proba")


def test_load_model_missing(tmp_path):
    missing_path = tmp_path / "missing.joblib"
    with pytest.raises(ModelLoadError):
        load_model(missing_path)

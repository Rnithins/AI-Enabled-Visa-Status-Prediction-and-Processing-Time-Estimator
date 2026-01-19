import os

from app import MODEL_DIR
from visapredict.inference_adapter import load_model_and_metadata


def test_model_loads():
    model, metadata = load_model_and_metadata(MODEL_DIR)
    assert model is not None
    assert metadata["feature_order"]
    assert os.path.exists(os.path.join(MODEL_DIR, "visa_model.pkl"))

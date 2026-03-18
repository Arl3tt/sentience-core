from core.tools import extract_motor_imagery_features, classify_motor_imagery, MotorImageryNet
import numpy as np


def test_extract_features_shape(sample_multichannel):
    feats = extract_motor_imagery_features(sample_multichannel, fs=250.0)
    assert isinstance(feats, dict)
    assert any(k.startswith("f") for k in feats.keys())


def test_classify_motor_imagery_heuristic(sample_multichannel):
    res = classify_motor_imagery(sample_multichannel, fs=250.0, model=None)
    assert isinstance(res, dict)
    assert "predicted_class" in res
    assert "class_probabilities" in res


def test_training_api_runs():
    # ensure MotorImageryNet API exists but skip heavy training
    m = MotorImageryNet()
    assert hasattr(m, "num_channels")
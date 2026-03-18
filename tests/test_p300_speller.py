"""Test P300 Speller module."""
import numpy as np

from core.tools import P300Speller, extract_p300_features, classify_p300_response, create_speller_interface


def test_extract_features_epoch(sample_epoch):
    sp = P300Speller()
    feats = sp.extract_p300_features(sample_epoch, fs=250.0)
    assert "peak_amp" in feats and "peak_time_s" in feats

def test_detect_and_classify(sample_epoch):
    sp = create_speller_interface()
    detected, score = sp.detect_p300(sample_epoch, fs=250.0, threshold=0.0)
    assert isinstance(detected, bool)
    assert isinstance(score, float)

    # classification with small score arrays
    rows = np.array([0.1, 0.5, 0.2])
    cols = np.array([0.05, 0.02, 0.9])
    r, c, conf = classify_p300_response(rows, cols)
    assert isinstance(r, int) and isinstance(c, int)
    assert isinstance(conf, float)

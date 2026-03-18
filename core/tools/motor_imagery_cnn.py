"""
Motor imagery feature extraction and a lightweight classifier wrapper.

This module provides feature extraction (bandpower + simple time-domain stats)
and a classifier wrapper that will use scikit-learn if available; otherwise it
returns deterministic heuristics so the module is usable in CI and profiling.
"""
import numpy as np
from typing import Dict, Any, Optional

try:
    from sklearn.svm import SVC
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False


class MotorImageryNet:
    def __init__(self, num_channels: int = 8, num_classes: int = 4):
        self.num_channels = num_channels
        self.num_classes = num_classes
        self.model = None
        self.scaler = None

    def fit(self, X: np.ndarray, y: np.ndarray):
        if not SKLEARN_AVAILABLE:
            raise RuntimeError("scikit-learn not available for training")
        self.scaler = StandardScaler()
        Xs = self.scaler.fit_transform(X)
        self.model = SVC(probability=True, kernel="rbf")
        self.model.fit(Xs, y)

    def predict(self, X: np.ndarray):
        if self.model is None or self.scaler is None:
            raise RuntimeError("Model not trained")
        Xs = self.scaler.transform(X)
        probs = self.model.predict_proba(Xs)
        preds = self.model.predict(Xs)
        return preds, probs


def extract_motor_imagery_features(eeg_signal: np.ndarray, fs: float = 250.0) -> Dict[str, float]:
    """Simple feature set: bandpowers (mu/beta) and RMS per channel.

    Accepts 1D (samples) or 2D (channels, samples).
    """
    if eeg_signal.ndim == 1:
        eeg_signal = eeg_signal[np.newaxis, :]

    feats = []
    for ch in range(eeg_signal.shape[0]):
        s = eeg_signal[ch, :]
        mu = bandpower_simple(s, fs, (8, 13))
        beta = bandpower_simple(s, fs, (13, 30))
        rms = float(np.sqrt(np.mean(s ** 2)))
        feats.append([mu, beta, rms])

    arr = np.array(feats).flatten()
    # return a dict for compatibility
    return {f"f{i}": float(v) for i, v in enumerate(arr)}


def bandpower_simple(x: np.ndarray, fs: float, band: tuple) -> float:
    # lightweight DFT-based bandpower
    n = len(x)
    if n < 2:
        return 0.0
    freqs = np.fft.rfftfreq(n, 1.0 / fs)
    psd = np.abs(np.fft.rfft(x)) ** 2
    idx = (freqs >= band[0]) & (freqs <= band[1])
    return float(psd[idx].sum()) if np.any(idx) else 0.0


def classify_motor_imagery(
    eeg_signal: np.ndarray,
    fs: float = 250.0,
    model: Optional[MotorImageryNet] = None,
) -> Dict[str, Any]:
    feats = extract_motor_imagery_features(eeg_signal, fs)
    classes = ["left_hand", "right_hand", "feet", "tongue"]
    if model is not None and getattr(model, "model", None) is not None:
        X = np.array([list(feats.values())])
        try:
            preds, probs = model.predict(X)
            return {
                "method": "sklearn",
                "predicted_class": classes[int(preds[0])],
                "class_probabilities": {
                    c: float(p) for c, p in zip(classes, probs[0])
                },
                "confidence": float(max(probs[0])),
            }
        except Exception:
            pass

    # Fallback heuristic using ratio of mu/beta
    vals = list(feats.values())
    mu = vals[0] if vals else 0.0
    beta = vals[1] if len(vals) > 1 else 0.0
    if mu > beta * 1.2:
        pred = "left_hand"
    else:
        pred = "right_hand"
    probs = {c: 1.0 / len(classes) for c in classes}
    return {"method": "heuristic", "predicted_class": pred, "class_probabilities": probs, "confidence": float(0.5)}


def train_motor_imagery_model(X: np.ndarray, y: np.ndarray, num_channels: int = 8) -> MotorImageryNet:
    m = MotorImageryNet(num_channels=num_channels)
    if not SKLEARN_AVAILABLE:
        raise RuntimeError("scikit-learn not available for training")
    m.fit(X, y)
    return m

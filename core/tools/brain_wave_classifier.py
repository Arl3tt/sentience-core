"""Lightweight brain-wave classifier utilities.

Simple, dependency-light helpers used in tests and CI:
- ``bandpower``: estimate power in a frequency band using Welch PSD
- ``classify_brainwave_bands``: return power estimates for common bands
- ``classify_cognitive_state``: simple heuristic state based on ratios
- ``classify_multi_channel``: convenience for multi-channel inputs

The implementations are intentionally minimal so they run in CI without
heavy model dependencies.
"""

from typing import Dict, Any

import numpy as np
from scipy import signal, integrate


def bandpower(eeg: np.ndarray, fs: float, band: tuple[float, float]) -> float:
    """Estimate band power for a 1D EEG signal using Welch PSD."""
    f, Pxx = signal.welch(eeg, fs=fs, nperseg=min(256, len(eeg)))
    idx = (f >= band[0]) & (f <= band[1])
    if not np.any(idx):
        return 0.0
    return float(integrate.trapezoid(Pxx[idx], f[idx]))


def classify_brainwave_bands(eeg_signal: np.ndarray, fs: float = 250.0) -> Dict[str, float]:
    """Return absolute band-power estimates for common EEG bands.

    Accepts 1D (samples,) or 2D (channels, samples). For multi-channel
    input the channels are averaged before computing powers.
    """
    if eeg_signal.ndim == 2:
        eeg = np.mean(eeg_signal, axis=0)
    else:
        eeg = eeg_signal

    bands = {
        "delta": (0.5, 4),
        "theta": (4, 8),
        "alpha": (8, 13),
        "beta": (13, 30),
        "gamma": (30, 45),
    }

    powers: Dict[str, float] = {}
    for name, rng in bands.items():
        powers[f"{name}_power"] = bandpower(eeg, fs, rng)

    # also include relative ratios (power / total)
    total = sum(powers.values()) if powers else 0.0
    for name in bands.keys():
        key = f"{name}_power"
        ratio_key = f"{name}_power_ratio"
        powers[ratio_key] = float(powers.get(key, 0.0) / total) if total > 0 else 0.0

    return powers


def classify_cognitive_state(eeg_signal: np.ndarray, fs: float = 250.0) -> Dict[str, Any]:
    """Heuristic cognitive-state classifier returning predicted state and scores."""
    p = classify_brainwave_bands(eeg_signal, fs)
    alpha = p.get("alpha_power", 0.0)
    theta = p.get("theta_power", 0.0)
    beta = p.get("beta_power", 0.0)

    scores = {
        "relaxation": float(alpha / (beta + 1e-9)),
        "drowsy": float(theta / (alpha + 1e-9)),
        "alert": float(beta / (alpha + 1e-9)),
    }

    predicted = max(scores.items(), key=lambda x: x[1])[0]
    return {"predicted_state": predicted, "state_scores": scores}


def classify_multi_channel(eeg_data: np.ndarray, fs: float = 250.0) -> Dict[str, Any]:
    """Aggregate per-channel bandpowers and produce a global state."""
    if eeg_data.ndim == 1:
        return classify_cognitive_state(eeg_data, fs)

    channel_results = [classify_brainwave_bands(eeg_data[ch, :], fs) for ch in range(eeg_data.shape[0])]
    agg: Dict[str, float] = {}
    keys = channel_results[0].keys()
    for k in keys:
        agg[k] = float(np.mean([c.get(k, 0.0) for c in channel_results]))

    global_state = classify_cognitive_state(np.mean(eeg_data, axis=0), fs)
    return {"channels": channel_results, "aggregate": agg, "global_state": global_state}

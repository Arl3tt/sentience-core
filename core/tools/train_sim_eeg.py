"""
train_sim_eeg.py

Safe toy training loop for simulated EEG motor-imagery data.

- Generates synthetic EEG-like signals for two classes (left / right).
- Extracts simple spectral features (band power) and time-domain stats.
- Trains a lightweight classifier (Logistic Regression).
- Saves model and a small dataset to ./data/simulated and ./data/models.
- Prints metrics and a short JSON-like summary to stdout for the Executor to capture.

Dependencies: numpy, scikit-learn (already in requirements)
"""

import os
import json
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
import joblib
import time

RNG_SEED = 42
np.random.seed(RNG_SEED)

OUT_DIR = os.path.join("data", "simulated")
MODEL_DIR = os.path.join("data", "models")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)


def simulate_eeg(n_samples=400, n_channels=8, duration_s=1.0, sfreq=128):
    """
    Simulate pseudo-EEG epochs for two classes.
    Class 0 -> stronger 10 Hz (alpha) component
    Class 1 -> stronger 18 Hz (beta) component
    Returns X: (n_samples, n_channels, n_times), y: (n_samples,)
    """
    n_times = int(duration_s * sfreq)
    t = np.linspace(0, duration_s, n_times, endpoint=False)
    X = np.zeros((n_samples, n_channels, n_times), dtype=np.float32)
    y = np.zeros(n_samples, dtype=np.int64)
    for i in range(n_samples):
        cls = 0 if i < n_samples//2 else 1
        y[i] = cls
        for ch in range(n_channels):
            # base noise
            signal = 0.5 * np.random.randn(n_times)
            if cls == 0:
                # alpha band dominant
                signal += 1.0 * np.sin(2.0 * np.pi * 10.0 * t) * (0.6 + 0.4*np.random.rand())
            else:
                # beta band dominant
                signal += 1.0 * np.sin(2.0 * np.pi * 18.0 * t) * (0.6 + 0.4*np.random.rand())
            # small channel-specific scaling and offset
            signal = signal * (0.8 + 0.4*np.random.rand()) + 0.01*np.random.randn()
            X[i, ch, :] = signal
    return X, y, sfreq


def extract_features(X, sfreq):
    """
    Very simple feature extractor:
    - Band-power in delta/theta/alpha/beta ranges via FFT energy sums
    - Mean and std per channel
    Returns features shape (n_samples, n_channels * n_features_per_channel)
    """
    n_samples, n_channels, n_times = X.shape
    freqs = np.fft.rfftfreq(n_times, 1.0 / sfreq)

    def band_power(epoch, fmin, fmax):
        fft = np.abs(np.fft.rfft(epoch)) ** 2
        mask = (freqs >= fmin) & (freqs <= fmax)
        return fft[mask].sum()

    feats = []
    for i in range(n_samples):
        ch_feats = []
        for ch in range(n_channels):
            epoch = X[i, ch, :]
            # time domain
            ch_feats.append(epoch.mean())
            ch_feats.append(epoch.std())
            # band powers
            ch_feats.append(band_power(epoch, 1, 4))    # delta
            ch_feats.append(band_power(epoch, 4, 8))    # theta
            ch_feats.append(band_power(epoch, 8, 13))   # alpha
            ch_feats.append(band_power(epoch, 13, 30))  # beta
        feats.append(ch_feats)
    return np.array(feats, dtype=np.float32)


def run_training(X, y, sfreq, params=None):
    start = time.time()

    # Save a tiny sample dataset for inspection (100 samples)
    sample_idx = np.arange(min(100, X.shape[0]))
    np.savez_compressed(os.path.join(OUT_DIR, "sim_eeg_sample.npz"),
                        X=X[sample_idx], y=y[sample_idx], sfreq=sfreq)

    # Feature extraction
    feats = extract_features(X, sfreq)

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        feats, y, test_size=0.2, random_state=RNG_SEED, stratify=y
    )

    # Model: lightweight classifier
    clf = LogisticRegression(max_iter=500, solver='liblinear')
    clf.fit(X_train, y_train)

    # Evaluation
    preds = clf.predict(X_test)
    acc = accuracy_score(y_test, preds)
    report = classification_report(y_test, preds, output_dict=True)

    # Save model & metadata
    model_path = os.path.join(MODEL_DIR, "sim_eeg_logreg.pkl")
    joblib.dump(clf, model_path)

    meta = {
        "model_id": "sim_eeg_logreg",
        "model_path": model_path,
        "accuracy": float(acc),
        "classification_report": report,
        "n_train": int(X_train.shape[0]),
        "n_test": int(X_test.shape[0]),
        "params": params or {},
        "timestamp": time.time(),
        "notes": "Synthetic EEG toy model (alpha vs beta simulation)."
    }

    # Save metadata
    with open(os.path.join(MODEL_DIR, "sim_eeg_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    # Log to history
    from core.tools.model_logger import log_training_result
    result = log_training_result(meta)

    elapsed = time.time() - start

    # Print machine-parseable summary for the Executor/Critic
    summary = {
        "status": "ok",
        "model_id": meta["model_id"],
        "accuracy": meta["accuracy"],
        "model_path": meta["model_path"],
        "params": meta["params"],
        "elapsed_s": elapsed,
        "improved": result["improved"],
        "prev_best": result["prev_best"]
    }
    print(json.dumps(summary))

    # Print human friendly output
    print("\n=== Training complete ===")
    print(f"Accuracy: {acc:.3f}")
    print(f"Model saved to: {model_path}")
    print(f"Elapsed (s): {elapsed:.2f}")
    if result["improved"]:
        print(f"Improved by: {acc - result['prev_best']:.3f}")

    return summary


def parse_args():
    """Parse command line arguments"""
    import argparse
    parser = argparse.ArgumentParser(description="Train EEG classifier on simulated data")
    parser.add_argument("--n_samples", type=int, default=400, help="Number of training samples")
    parser.add_argument("--n_channels", type=int, default=8, help="Number of EEG channels")
    parser.add_argument("--duration_s", type=float, default=1.0, help="Duration of each sample in seconds")
    parser.add_argument("--sfreq", type=float, default=128, help="Sampling frequency in Hz")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    params = {
        "n_samples": args.n_samples,
        "n_channels": args.n_channels,
        "duration_s": args.duration_s,
        "sfreq": args.sfreq
    }

    X, y, sfreq = simulate_eeg(**params)
    run_training(X, y, sfreq, params=params)

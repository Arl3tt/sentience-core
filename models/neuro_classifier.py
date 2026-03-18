"""Lightweight neuro-state classifier using scikit-learn.

This module provides a simple API to train and use a classifier that predicts
cognitive tags (focus, fatigue, stress, flow, drowsy, relaxed) from feature
vectors saved by the preprocessing pipeline.

It expects training data to be available as features JSON files with a 'label'
or 'tags' field in the meta. This is a scaffold — you can adapt it to your
label format.
"""
from typing import Dict, Any, List, Optional
import os
import json
import numpy as np
from sklearn.linear_model import LogisticRegression
import joblib


def _vectorize(features: Dict[str, Any]) -> np.ndarray:
    bands = ['delta', 'theta', 'alpha', 'beta', 'gamma']
    vec = []
    for b in bands:
        try:
            vec.append(float(np.mean(features.get(f"{b}_power", [0.0]))))
        except Exception:
            vec.append(0.0)
    try:
        vec.append(float(np.mean(features.get('spectral_entropy', [0.0]))))
    except Exception:
        vec.append(0.0)
    return np.asarray(vec, dtype=float)


def train_classifier(state_dir: str, out_path: str):
    X = []
    y = []
    for fname in os.listdir(state_dir):
        if not fname.endswith('.features.json'):
            continue
        path = os.path.join(state_dir, fname)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                feat = json.load(f)
        except Exception:
            continue
        label = None
        # try several keys that might contain a label
        for k in ('label', 'tags', 'predicted_tags'):
            if k in feat and isinstance(feat[k], (str, dict)):
                label = feat[k]
                break
        if label is None:
            continue
        # for dict tags, choose the highest-score tag
        if isinstance(label, dict):
            if label:
                label = max(label.items(), key=lambda kv: kv[1])[0]
            else:
                continue

        vec = _vectorize(feat)
        X.append(vec)
        y.append(str(label))

    if not X:
        raise RuntimeError('No labeled training data found in state_dir')

    X = np.stack(X, axis=0)
    clf = LogisticRegression(max_iter=200)
    clf.fit(X, y)
    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    joblib.dump(clf, out_path)
    return out_path


def load_classifier(path: str):
    if not os.path.exists(path):
        return None
    return joblib.load(path)


def predict_tags(features: Dict[str, Any], model_path: Optional[str] = None) -> Dict[str, float]:
    """Predict cognitive tags from EEG features.
    
    If model_path is not provided, will try:
    1. memory/neural_state/neuro_classifier.joblib (preferred)
    2. models/neuro_classifier.joblib (fallback)
    """
    if model_path is None:
        paths = [
            os.path.join('memory', 'neural_state', 'neuro_classifier.joblib'),
            os.path.join('models', 'neuro_classifier.joblib')
        ]
        for p in paths:
            if os.path.exists(p):
                model_path = p
                break
    if model_path is None or not os.path.exists(model_path):
        return {}
    clf = load_classifier(model_path)
    if clf is None:
        return {}
    vec = _vectorize(features).reshape(1, -1)
    probs = clf.predict_proba(vec)[0]
    classes = clf.classes_
    return {str(c): float(p) for c, p in zip(classes, probs)}

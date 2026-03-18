"""Embedding model for EEG features using trained autoencoder

The embedding is now computed using a trained autoencoder model that projects
the features into a learned latent space. If the model is not available or
fails to load, it will fall back to the deterministic random projection.

API:
  compute_embedding(features: dict, dim: int = 32, save_path: str | None = None) -> np.ndarray

The function will return a numpy array of shape (dim,) and optionally
write it to save_path using np.save.
"""
from __future__ import annotations
import os
import numpy as np
from typing import Dict, Any, Optional
from pathlib import Path

try:
    import torch
except ImportError:
    torch = None  # type: ignore


def _vectorize_features(features: Dict[str, Any]) -> np.ndarray:
    """Convert selected features into a flat numeric vector.

    Currently uses:
      - mean band powers: delta/theta/alpha/beta/gamma
      - mean spectral entropy
      - simple band ratios: alpha_beta, theta_beta, theta_alpha

    If a feature is missing, zero is used as default.
    """
    bands = ['delta', 'theta', 'alpha', 'beta', 'gamma']
    vec = []
    for b in bands:
        vals = features.get(f"{b}_power", None)
        try:
            v = np.mean(np.array(vals, dtype=float))
        except Exception:
            v = 0.0
        vec.append(float(v))

    # spectral entropy
    try:
        se = np.mean(np.array(features.get('spectral_entropy', [0.0]), dtype=float))
    except Exception:
        se = 0.0
    vec.append(float(se))

    # ratios
    for r in ['alpha_beta_ratio', 'theta_beta_ratio', 'theta_alpha_ratio']:
        try:
            v = np.mean(np.array(features.get(r, [0.0]), dtype=float))
        except Exception:
            v = 0.0
        vec.append(float(v))

    return np.asarray(vec, dtype=float)


def load_autoencoder(model_path: str | None = None) -> Optional[Any]:
    """Load the trained autoencoder model if available."""
    if torch is None:
        return None

    if model_path is None:
        model_path = os.path.join(os.path.dirname(__file__), 'autoencoder.pth')
    if not os.path.exists(model_path):
        return None

    try:
        model = torch.load(model_path)
        model.eval()  # set to inference mode
        return model
    except Exception:
        return None


def compute_embedding(features: Dict[str, Any], dim: int = 32,
                     save_path: Optional[str] = None,
                     model_path: Optional[str] = None) -> np.ndarray:
    """Compute embedding vector from features using trained autoencoder.

    If the autoencoder model is not available or fails to load, falls back
    to random projection.
    """
    vec = _vectorize_features(features)
    orig_dim = vec.shape[0]

    if orig_dim <= 0:
        # handle empty features
        emb = np.zeros((dim,), dtype=float)
    else:
        # try to use trained autoencoder
        model = load_autoencoder(model_path)
        if model is not None and torch is not None:
            try:
                with torch.no_grad():
                    x = torch.from_numpy(vec.astype(np.float32)).unsqueeze(0)
                    emb = model.encode(x).squeeze(0).numpy()
                    if emb.shape[0] != dim:
                        # reshape if needed (shouldn't happen with proper model)
                        rng = np.random.RandomState(123456)
                        proj = rng.normal(size=(emb.shape[0], dim)).astype(float)
                        emb = emb.reshape(1, -1).dot(proj).reshape(-1)
            except Exception:
                # fall back to random projection on any error
                model = None

        if model is None:
            # fallback: deterministic random projection
            rng = np.random.RandomState(123456)
            proj = rng.normal(size=(orig_dim, dim)).astype(float)
            emb = vec.reshape(1, -1).dot(proj).reshape(-1)

    # ensure emb is numpy array and normalize to unit norm (avoid zero division)
    try:
        emb = np.asarray(emb, dtype=float)
    except Exception:
        emb = np.asarray([float(emb)])
    norm = np.linalg.norm(emb)
    if norm == 0:
        norm = 1.0
    emb = emb / norm

    if save_path:
        try:
            np.save(save_path, emb)
        except Exception:
            # best-effort save; don't raise
            pass

    return emb

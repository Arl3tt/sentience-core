"""Autoencoder scaffold for EEG feature embeddings (PyTorch).

This file contains a lightweight autoencoder class and training helper.
Imports of torch are done lazily so code can be inspected or imported on
systems without PyTorch installed. Use `train_autoencoder` to train on
features saved under `memory/neural_state/*.features.json` when you have
PyTorch available.
"""
from typing import List, Dict, Any
import json
import os
import numpy as np


class AutoencoderWrapper:
    """Wrapper that lazily loads PyTorch and provides fit/encode/save APIs."""
    def __init__(self, input_dim: int, latent_dim: int = 16):
        self.input_dim = input_dim
        self.latent_dim = latent_dim
        self._model = None
        self._torch = None

    def _ensure_torch(self):
        if self._torch is None:
            try:
                import torch
                import torch.nn as nn
                self._torch = torch
                # define a tiny autoencoder
                class AE(nn.Module):
                    def __init__(self, inp, lat):
                        super().__init__()
                        self.enc = nn.Sequential(
                            nn.Linear(inp, max(lat * 4, 32)),
                            nn.ReLU(),
                            nn.Linear(max(lat * 4, 32), lat)
                        )
                        self.dec = nn.Sequential(
                            nn.Linear(lat, max(lat * 4, 32)),
                            nn.ReLU(),
                            nn.Linear(max(lat * 4, 32), inp)
                        )

                    def forward(self, x):
                        z = self.enc(x)
                        return self.dec(z)

                    def encode(self, x):
                        return self.enc(x)

                self._model = AE(self.input_dim, self.latent_dim)
            except Exception as e:
                raise RuntimeError("PyTorch is required to use AutoencoderWrapper") from e

    def fit(self, X: np.ndarray, epochs: int = 50, batch_size: int = 32, lr: float = 1e-3):
        self._ensure_torch()
        torch = self._torch
        assert torch is not None, "torch must be available"
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        assert self._model is not None, "model must be initialized before training"
        model = self._model.to(device)
        opt = torch.optim.Adam(model.parameters(), lr=lr)
        loss_fn = torch.nn.MSELoss()

        X_t = torch.from_numpy(np.asarray(X, dtype=np.float32))
        dataset = torch.utils.data.TensorDataset(X_t)
        loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

        model.train()
        for ep in range(epochs):
            total = 0.0
            for (batch,) in loader:
                batch = batch.to(device)
                opt.zero_grad()
                recon = model(batch)
                loss = loss_fn(recon, batch)
                loss.backward()
                opt.step()
                total += float(loss.item()) * batch.size(0)
            # no logging here to keep training silent in scripts

        self._model = model.cpu()

    def encode(self, X: np.ndarray) -> np.ndarray:
        self._ensure_torch()
        torch = self._torch
        assert torch is not None, "torch must be available"
        model = self._model
        if model is None:
            raise RuntimeError("Model not trained or loaded")
        model.eval()
        with torch.no_grad():
            t = torch.from_numpy(np.asarray(X, dtype=np.float32))
            z = model.encode(t).numpy()
        return z

    def save(self, path: str):
        # save model state dict using torch if available
        self._ensure_torch()
        torch = self._torch
        assert torch is not None, "torch must be available"
        assert self._model is not None, "model must be initialized before save"
        torch.save(self._model.state_dict(), path)

    def load(self, path: str):
        self._ensure_torch()
        torch = self._torch
        assert torch is not None, "torch must be available"
        # create fresh model and load state
        if self._model is None:
            # instantiate architecture by re-running ensure (architecture depends on input_dim/latent_dim)
            self._ensure_torch()
        state = torch.load(path, map_location='cpu')
        if self._model is None:
            raise RuntimeError("Autoencoder model not initialized before load")
        self._model.load_state_dict(state)


def gather_feature_vectors(state_dir: str) -> np.ndarray:
    """Collect flat feature vectors from stored features JSON files.

    This helper expects features saved by `save_neural_session` as JSON with
    numeric lists for band powers and spectral_entropy.
    """
    vecs = []
    for fname in os.listdir(state_dir):
        if not fname.endswith('.features.json'):
            continue
        path = os.path.join(state_dir, fname)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                feat = json.load(f)
            # simple vectorization: mean band powers + mean spectral entropy
            bands = ['delta', 'theta', 'alpha', 'beta', 'gamma']
            v = []
            for b in bands:
                v.append(np.mean(feat.get(f"{b}_power", [0.0])))
            v.append(np.mean(feat.get('spectral_entropy', [0.0])))
            vecs.append(v)
        except Exception:
            continue
    if not vecs:
        return np.zeros((0,))
    return np.asarray(vecs, dtype=float)


def train_autoencoder(state_dir: str, out_path: str, latent_dim: int = 16, epochs: int = 50):
    X = gather_feature_vectors(state_dir)
    if X.size == 0:
        raise RuntimeError("No feature vectors found to train autoencoder")
    ae = AutoencoderWrapper(input_dim=X.shape[1], latent_dim=latent_dim)
    ae.fit(X, epochs=epochs)
    ae.save(out_path)

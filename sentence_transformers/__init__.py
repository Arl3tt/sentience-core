import numpy as np

class SentenceTransformer:
    def __init__(self, model_name: str = None):
        # lightweight stub: fixed embedding dim
        self._dim = 128

    def encode(self, texts):
        # Return a small non-zero vector to avoid zero-norm issues
        v = np.ones(self._dim, dtype=np.float32) * 1e-6
        if isinstance(texts, str):
            return v
        try:
            # assume iterable of texts
            return np.vstack([v for _ in texts])
        except Exception:
            return v

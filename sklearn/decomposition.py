import numpy as np

class PCA:
    def __init__(self, n_components=None, whiten=False):
        self.n_components = n_components
        self.whiten = whiten
        self.explained_variance_ = None
        self.mean_ = None

    def fit_transform(self, X):
        X = np.asarray(X)
        self.mean_ = X.mean(axis=0) if X.size else np.array([])
        n = X.shape[1] if self.n_components is None else self.n_components
        n = min(n, X.shape[1]) if X.size else 0
        # simple stub: return first n columns (or the array itself)
        self.explained_variance_ = np.ones(n)
        if n == 0:
            return X
        if X.shape[1] >= n:
            return X[:, :n]
        return X

    def inverse_transform(self, X_pca):
        # naive inverse: pad with zeros and add mean
        Xp = np.asarray(X_pca)
        if self.mean_ is None:
            return Xp
        if Xp.ndim == 1:
            Xp = Xp.reshape(1, -1)
        if Xp.shape[1] < self.mean_.shape[0]:
            pad = np.zeros((Xp.shape[0], self.mean_.shape[0] - Xp.shape[1]))
            X_full = np.concatenate([Xp, pad], axis=1)
        else:
            X_full = Xp[:, : self.mean_.shape[0]]
        return X_full + self.mean_


class FastICA:
    def __init__(self, n_components=None, whiten=False, random_state=None):
        self.n_components = n_components

    def fit_transform(self, X):
        X = np.asarray(X)
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        n = X.shape[1] if self.n_components is None else min(self.n_components, X.shape[1])
        return X[:, :n]

    def inverse_transform(self, S):
        # identity-like inverse
        return S

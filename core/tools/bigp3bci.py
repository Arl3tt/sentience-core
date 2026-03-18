"""
bigP3BCI dataset integration

Module: core.tools.bigp3bci
Provides helpers to download, load and preprocess the "bigP3BCI" P300 dataset.
This module is intentionally dependency-light and uses optional imports for network access.

Functions:
- download_bigp3_dataset(url, dest_path): download and extract dataset archive
- load_bigp3_record(record_path): load a single recording file (simple numpy/pickle reader)
- preprocess_bigp3(raw_data, fs, band=(0.5, 30)): basic bandpass + downsample preprocessing
- get_bigp3_metadata(meta_path): read metadata file if present
- create_bigp3_interface(...): factory to return a small helper object for dataset operations
"""

from typing import Optional, Dict, Any, Tuple
import os
import zipfile
import json
import numpy as np

# Optional network dependency
try:
    import requests
    REQUESTS_AVAILABLE = True
except Exception:
    REQUESTS_AVAILABLE = False


def download_bigp3_dataset(url: str, dest_path: str) -> str:
    """
    Download the bigP3BCI dataset archive from `url` and extract into `dest_path`.
    Returns the path to the extracted folder.

    If `requests` is not available, raises RuntimeError.
    """
    if not REQUESTS_AVAILABLE:
        raise RuntimeError("requests package required to download dataset; install requests or download manually")

    os.makedirs(dest_path, exist_ok=True)
    resp = requests.get(url, stream=True)
    resp.raise_for_status()

    # Attempt to guess filename
    filename = url.split("/")[-1] or "bigp3bci.zip"
    archive_path = os.path.join(dest_path, filename)

    with open(archive_path, "wb") as fh:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                fh.write(chunk)

    # If it's a zip, extract
    try:
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(dest_path)
    except zipfile.BadZipFile:
        # Not a zip file — leave as-is
        pass

    return dest_path


def load_bigp3_record(record_path: str) -> Dict[str, Any]:
    """
    Load a single bigP3 record from a file. Supports JSON, NPZ, NPY, or pickled numpy arrays.

    Returns a dict with keys: `signals` (np.ndarray shape (samples, channels)), `fs` (float), and optional `meta`.
    """
    if not os.path.exists(record_path):
        raise FileNotFoundError(record_path)

    _, ext = os.path.splitext(record_path)
    ext = ext.lower()

    if ext == ".json":
        with open(record_path, "r", encoding="utf8") as fh:
            data = json.load(fh)
        # Expecting data to contain base64 or nested arrays; try to convert
        signals = np.array(data.get("signals", []))
        fs = float(data.get("fs", 250.0))
        meta = data.get("meta", {})
        return {"signals": signals, "fs": fs, "meta": meta}

    if ext == ".npz":
        archive = np.load(record_path, allow_pickle=True)
        signals = archive.get("signals")
        fs = float(archive.get("fs", 250.0))
        meta = archive.get("meta", {})
        return {"signals": signals, "fs": fs, "meta": meta}

    if ext == ".npy":
        arr = np.load(record_path, allow_pickle=True)
        return {"signals": arr, "fs": 250.0, "meta": {}}

    # Try to read pickled numpy
    try:
        import pickle
        with open(record_path, "rb") as fh:
            data = pickle.load(fh)
        if isinstance(data, dict):
            return data
        # Otherwise assume it's raw array
        return {"signals": np.asarray(data), "fs": 250.0, "meta": {}}
    except Exception:
        raise RuntimeError(f"Unsupported record format: {record_path}")


def preprocess_bigp3(
    raw_data: Dict[str, Any],
    fs: Optional[float] = None,
    band: Tuple[float, float] = (0.5, 30.0),
    downsample_to: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Preprocess raw bigP3 data.
    - Expects raw_data to include `signals` (samples, channels) and optionally `fs`.
    - Applies simple bandpass via FFT-based filtering and optional downsampling.

    Returns dict with `signals`, `fs`, and `meta`.
    """
    signals = raw_data.get("signals")
    if signals is None:
        raise ValueError("raw_data must include 'signals'")

    signals = np.asarray(signals)
    if fs is None:
        fs = float(raw_data.get("fs", 250.0))

    # Ensure shape (samples, channels)
    if signals.ndim == 1:
        signals = signals.reshape(-1, 1)

    # Simple bandpass in frequency domain (stable and dependency-light)
    n = signals.shape[0]
    freqs = np.fft.rfftfreq(n, d=1.0 / fs)
    fft_data = np.fft.rfft(signals, axis=0)

    low, high = band
    mask = (freqs >= low) & (freqs <= high)

    # Zero out frequencies outside band
    fft_data[~mask, :] = 0
    filtered = np.fft.irfft(fft_data, n=n, axis=0)

    # Optional downsampling
    if downsample_to and downsample_to < fs:
        factor = int(round(fs / downsample_to))
        if factor > 1:
            filtered = filtered[::factor, :]
            fs = fs / factor

    return {"signals": filtered, "fs": float(fs), "meta": raw_data.get("meta", {})}


def get_bigp3_metadata(meta_path: str) -> Dict[str, Any]:
    """
    Load metadata JSON for the dataset if available.
    """
    if not os.path.exists(meta_path):
        raise FileNotFoundError(meta_path)
    with open(meta_path, "r", encoding="utf8") as fh:
        return json.load(fh)


class BigP3Interface:
    """Lightweight interface for dataset operations."""
    def __init__(self, base_path: str):
        self.base_path = base_path

    def list_records(self) -> list:
        files = []
        for root, _, filenames in os.walk(self.base_path):
            for fn in filenames:
                if fn.lower().endswith(('.npz', '.npy', '.json')):
                    files.append(os.path.join(root, fn))
        return files

    def load(self, record_path: str) -> Dict[str, Any]:
        return load_bigp3_record(record_path)

    def preprocess(self, record_path: str, **kwargs) -> Dict[str, Any]:
        data = self.load(record_path)
        return preprocess_bigp3(data, **kwargs)


def create_bigp3_interface(base_path: str) -> BigP3Interface:
    """Factory to create a BigP3Interface for a local dataset directory."""
    return BigP3Interface(base_path)

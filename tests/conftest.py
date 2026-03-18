import numpy as np
import pytest


@pytest.fixture
def sample_signal():
    # 1024 samples, single channel
    rng = np.random.RandomState(42)
    return rng.randn(1024)


@pytest.fixture
def sample_multichannel():
    # 1024 samples, 4 channels
    rng = np.random.RandomState(1)
    return rng.randn(1024, 4)


@pytest.fixture
def sample_epoch():
    # 800 samples, 6 channels typical ERP epoch
    rng = np.random.RandomState(2)
    return rng.randn(800, 6)


@pytest.fixture
def tmp_bigp3_npz(tmp_path):
    import numpy as np
    path = tmp_path / "record.npz"
    signals = np.random.randn(500, 3)
    fs = 250.0
    np.savez(path, signals=signals, fs=fs, meta={"id": "test"})
    return str(path)

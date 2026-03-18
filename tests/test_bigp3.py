import os
import numpy as np
from core.tools.bigp3bci import load_bigp3_record, preprocess_bigp3, create_bigp3_interface


def test_load_npz(tmp_bigp3_npz):
    data = load_bigp3_record(tmp_bigp3_npz)
    assert "signals" in data and "fs" in data
    assert isinstance(data["signals"], np.ndarray)


def test_preprocess_and_downsample(tmp_bigp3_npz):
    data = load_bigp3_record(tmp_bigp3_npz)
    orig_n = data["signals"].shape[0]
    out = preprocess_bigp3(data, fs=data["fs"], downsample_to=125.0)
    assert out["signals"].shape[0] <= orig_n


def test_interface_list_and_load(tmp_path, tmp_bigp3_npz):
    base = tmp_path / "ds"
    base.mkdir()
    # copy file
    import shutil
    shutil.copy(tmp_bigp3_npz, base / "r.npz")
    iface = create_bigp3_interface(str(base))
    recs = iface.list_records()
    assert len(recs) >= 1
    ld = iface.load(recs[0])
    assert "signals" in ld

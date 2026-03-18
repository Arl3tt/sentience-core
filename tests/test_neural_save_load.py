"""Test neural session save and load."""
import numpy as np

from memory.memory_controller import save_neural_session, load_last_neural_embeddings


def test_save_and_load_embedding(tmp_path):
    # prepare small dummy features and embedding
    features = {'delta_power': [0.1, 0.2],
        'theta_power': [0.1, 0.1],
        'alpha_power': [0.2, 0.2],
        'beta_power': [0.3, 0.3],
        'gamma_power': [0.05, 0.05],
        'spectral_entropy': [4.5, 4.6]}
    embedding = np.random.RandomState(0).randn(16)
    session_meta = {'session_id': f'test_session_{int(tmp_path.stat().st_mtime) if tmp_path.exists() else 0}'}

    res = save_neural_session(session_meta, features, embedding)
    assert 'session_id' in res

    loaded = load_last_neural_embeddings(1)
    assert isinstance(loaded, list)
    assert len(loaded) >= 1
    sid, emb = loaded[0]
    assert sid == res['session_id']
    assert emb.shape[0] == embedding.shape[0]

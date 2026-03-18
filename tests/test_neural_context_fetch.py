from memory.memory_controller import save_neural_session, get_recent_neural_context
import numpy as np


def test_recent_neural_context(tmp_path):
    # Create a dummy session with features + embedding
    features = {'alpha_power': [0.2, 0.25],
        'beta_power': [0.3, 0.35],
        'theta_power': [0.15, 0.1],
        'gamma_power': [0.05, 0.02],
        'spectral_entropy': [4.0, 4.2]}
    embedding = np.ones(16)
    meta = {'session_id': 'test_recent_session'}

    save_neural_session(meta, features, embedding)

    ctx = get_recent_neural_context(window_seconds=3600, max_embeddings=4)
    assert ctx is not None
    assert 'avg_embedding' in ctx
    assert 'latest_features' in ctx
    assert ctx['summary']['count'] >= 1

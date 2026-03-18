import numpy as np
from core.agents.neuro_behavior import neuro_weighted_retrieval
from memory import vector_store


def test_neuro_weighted_retrieval_prefers_neural_when_beta_high(tmp_path):
    # Clear fallback store
    vector_store.FALLBACK_STORE.clear()

    # Create two synthetic vectors in 3D space
    doc1 = {"id": "d1", "text": "doc one", "meta": {}}
    doc2 = {"id": "d2", "text": "doc two", "meta": {}}
    v1 = [0.99, 0.01, 0.0]
    v2 = [0.0, 0.9, 0.1]
    # Add vectors directly (pass embedding to avoid embed_text calls)
    vector_store.add_vector("d1", "doc one", {}, embedding=v1)
    vector_store.add_vector("d2", "doc two", {}, embedding=v2)

    # neural_embedding close to v1
    neural_emb = [1.0, 0.0, 0.0]

    results = neuro_weighted_retrieval("unused query", alpha=0.0, beta=10.0, neural_embedding=neural_emb, top_k=2)
    # Expect d1 to come first because neural similarity strongly favors it
    assert len(results) >= 1
    assert results[0]["id"] == "d1"

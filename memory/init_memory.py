# memory/init_memory.py
"""
Run this once after adding memory package to create directories and verify embeddings.
"""
from .episodic_store import add_episode, query_recent
from .vector_store import add_vector, query_vectors, embed_text
from .memory_controller import store_memory, semantic_search
import os

def smoke_test():
    print("Running memory smoke test...")
    # create example memory
    store_memory("Initialized memory: test record. Model improved significantly.", {"source":"init_test"})
    results = semantic_search("model improved", top_k=3)
    print("Search results:", results[:3])
    print("Recent episodes:", query_recent(5))

if __name__ == "__main__":
    smoke_test()
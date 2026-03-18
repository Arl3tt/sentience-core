# memory/vector_store.py
"""
Vector store interface: tries Chroma (recommended), falls back to in-memory sqlite similarity.
Uses OpenAI text-embedding-3-small by default, with local sentence-transformers fallback.
"""
import os, json, logging
from typing import List, Dict, Any
from config import CHROMA_PERSIST, EMBEDDING_MODEL
log = logging.getLogger("vector_store")
log.setLevel(logging.INFO)

# Embedding provider abstraction
_EMBED_MODEL = None
_USE_OPENAI = False
try:
    from openai import OpenAI
    # will check OPENAI_API_KEY at runtime; avoid raising immediately
    _USE_OPENAI = True
except Exception:
    _USE_OPENAI = False

# local fallback
_local_encoder = None
try:
    from sentence_transformers import SentenceTransformer
    _local_encoder = SentenceTransformer("all-MiniLM-L6-v2")
except Exception:
    _local_encoder = None


def embed_text(text: str) -> List[float]:
    # Try OpenAI embeddings if API key available in env
    try:
        import os
        if os.getenv("OPENAI_API_KEY"):
            import openai
            model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
            resp = openai.Embedding.create(input=[text], model=model)
            return resp["data"][0]["embedding"]
    except Exception as e:
        log.debug("OpenAI embed failed or not configured: %s", e)
    # fallback to local
    if _local_encoder:
        vec = _local_encoder.encode(text).astype(float).tolist()
        return vec
    raise RuntimeError("No embedding model available. Set OPENAI_API_KEY or install sentence-transformers.")


# Chroma setup (optional)
USE_CHROMA = True
try:
    import chromadb
    from chromadb.config import Settings
    client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=CHROMA_PERSIST))
    COLLECTION_NAME = "copilot_memory"
    try:
        collection = client.get_collection(COLLECTION_NAME)
    except Exception:
        collection = client.create_collection(COLLECTION_NAME)
    log.info("Chroma initialized at %s", CHROMA_PERSIST)
except Exception as e:
    log.warning("Chroma unavailable, falling back: %s", e)
    USE_CHROMA = False
    collection = None

# Simple in-memory fallback (kept persistent in episodes DB as needed)
FALLBACK_STORE = []


def add_vector(id: str, text: str, metadata: Dict[str, Any], embedding: List[float]=None):
    emb = embedding or embed_text(text)
    if USE_CHROMA and collection:
        collection.add(ids=[id], documents=[text], metadatas=[metadata or {}], embeddings=[emb])
        return True
    else:
        FALLBACK_STORE.append({ "id":id, "text":text, "meta":metadata or {}, "emb": emb })
        return True


def query_vectors(query: str, top_k: int=5) -> List[Dict[str, Any]]:
    qemb = embed_text(query)
    if USE_CHROMA and collection:
        res = collection.query(query_embeddings=[qemb], n_results=top_k, include=["documents", "metadatas", "ids"])
        out = []
        for i in range(len(res["ids"][0])):
            out.append({ "id": res["ids"][0][i], "text": res["documents"][0][i], "meta": res["metadatas"][0][i] })
        return out
    else:
        # naive cosine similarity over FALLBACK_STORE
        import numpy as np
        qv = np.array(qemb, dtype=float)
        scored = []
        for item in FALLBACK_STORE:
            ev = np.array(item["emb"], dtype=float)
            score = float(np.dot(qv, ev) / ( (np.linalg.norm(qv)*np.linalg.norm(ev)) + 1e-8 ))
            scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [ { "id": s[1]["id"], "text": s[1]["text"], "meta": s[1]["meta"], "score": float(s[0]) } for s in scored[:top_k]]


def query_by_embedding(embedding: List[float], top_k: int=5) -> List[Dict[str, Any]]:
    """Query the vector store by an already-computed embedding.

    Returns a list of items with scores (higher is more similar). Works with Chroma when
    available or falls back to a naive cosine scorer over `FALLBACK_STORE`.
    """
    if embedding is None:
        raise ValueError("embedding must be provided")
    if USE_CHROMA and collection:
        try:
            res = collection.query(query_embeddings=[embedding], n_results=top_k, include=["documents", "metadatas", "ids", "distances"])
            out = []
            ids = res.get("ids", [[]])[0]
            docs = res.get("documents", [[]])[0]
            metas = res.get("metadatas", [[]])[0]
            dists = res.get("distances", [[]])[0] if "distances" in res else [None]*len(ids)
            for i in range(len(ids)):
                score = None
                if dists and dists[i] is not None:
                    # Chromadb may return distance; convert to similarity in [0,1]
                    try:
                        # assume distance in [0,2] for cosine-like distances
                        score = float(max(0.0, 1.0 - float(dists[i])))
                    except Exception:
                        score = None
                out.append({ "id": ids[i], "text": docs[i], "meta": metas[i] if metas else {}, "score": score })
            return out
        except Exception as e:
            log.warning("Chroma query_by_embedding failed, falling back: %s", e)

    # Fallback: compute cosine similarity over stored embeddings
    import numpy as np
    qv = np.array(embedding, dtype=float)
    scored = []
    for item in FALLBACK_STORE:
        ev = np.array(item.get("emb", []), dtype=float)
        if ev.size == 0:
            continue
        score = float(np.dot(qv, ev) / ((np.linalg.norm(qv) * np.linalg.norm(ev)) + 1e-8))
        scored.append((score, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [ { "id": s[1]["id"], "text": s[1]["text"], "meta": s[1]["meta"], "score": float(s[0]) } for s in scored[:top_k]]
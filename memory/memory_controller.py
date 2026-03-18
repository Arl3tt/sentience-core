# memory/memory_controller.py
"""
High-level memory controller:
- writes safe episodic records
- stores vectors in vector_store
- semantic retrieval routing
- small emotional tagging (enabled)
- human_confirm_writes gating flag
"""
import os, json, logging
from typing import List, Dict, Any, Optional, Any as _Any
from .schemas import MemoryRecord
from .vector_store import add_vector, query_vectors
from .episodic_store import add_episode, query_recent
log = logging.getLogger("memory_controller")
log.setLevel(logging.INFO)

# config flags
HUMAN_CONFIRM_WRITES = os.getenv("HUMAN_CONFIRM_WRITES", "false").lower() in ("1","true","yes")
EMOTIONAL_MEMORY = True  # you asked yes

# tiny sentiment heuristic (no heavy deps)
_POS_WORDS = set(["good","great","improved","improvement","success","win","positive","nice","accurate","accurately"])
_NEG_WORDS = set(["bad","fail","failed","error","poor","low","degraded","negative","wrong","inaccurate"])

def sentiment_score(text: str) -> Dict[str, Any]:
    txt = text.lower()
    words = txt.split()
    score = 0
    for w in words:
        if w in _POS_WORDS: score += 1
        if w in _NEG_WORDS: score -= 1
    # normalize roughly
    sentiment = "neutral"
    if score >= 2: sentiment = "positive"
    elif score <= -2: sentiment = "negative"
    return {"score": score, "label": sentiment}

def store_memory(text: str, meta: Optional[Dict[str, Any]] = None, allow_write: bool = True):
    meta = meta or {}
    # safety gate
    if HUMAN_CONFIRM_WRITES and not allow_write:
        log.info("Human confirmation required to write memory — skipping write: %s", text[:80])
        add_episode("memory.skipped", text, {"reason":"human_confirm_required"})
        return None

    # emotional tagging
    emo = sentiment_score(text) if EMOTIONAL_MEMORY else {"score":0,"label":"na"}
    rec = MemoryRecord.create(text=text, meta={**meta, "emotion": emo}, embedding_meta={})
    # embed and add to vector store
    try:
        emb = None
        # embed lazily to allow control; pass as Any to satisfy downstream type expectations
        emb_any: _Any = emb
        add_vector(rec.id, text, rec.meta, embedding=emb_any)
    except Exception as e:
        log.exception("Vector store write failed: %s", e)
    # add episodic record (text + meta)
    add_episode("memory.write", text, {"meta": rec.meta})
    return rec.to_dict()

def semantic_search(query: str, top_k: int=6):
    hits = query_vectors(query, top_k=top_k)
    # return simplified structure
    return hits


# --- Neural session persistence utilities ---------------------------------
import time
import glob
from datetime import datetime, timezone
import numpy as np

# directory where neural session artifacts (meta, features, embeddings) are stored
NEURAL_STATE_DIR = os.path.join(os.path.dirname(__file__), "neural_state")
os.makedirs(NEURAL_STATE_DIR, exist_ok=True)


def _to_json_serializable(obj):
    """Recursively convert numpy types/arrays into JSON-serializable structures."""
    if obj is None:
        return None
    if isinstance(obj, (int, float, str, bool)):
        return obj
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (list, tuple)):
        return [_to_json_serializable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _to_json_serializable(v) for k, v in obj.items()}
    # fallback
    try:
        return float(obj)
    except Exception:
        return str(obj)


def save_neural_session(session_meta: Dict[str, Any], features: Dict[str, Any], embedding: Optional[np.ndarray] = None):
    """Persist a neural session: meta (JSON), features (JSON-safe), and optional embedding (npy).

    Returns a dict with saved file paths and session_id.
    """
    ts = int(time.time())
    session_id = session_meta.get("session_id") or f"session_{ts}"
    # ensure directory exists
    os.makedirs(NEURAL_STATE_DIR, exist_ok=True)

    meta_path = os.path.join(NEURAL_STATE_DIR, f"{session_id}.meta.json")
    features_path = os.path.join(NEURAL_STATE_DIR, f"{session_id}.features.json")
    embedding_path = os.path.join(NEURAL_STATE_DIR, f"{session_id}.embedding.npy")

    # enrich meta with timestamp
    meta = dict(session_meta)
    if "timestamp" not in meta:
        meta["timestamp"] = datetime.now(timezone.utc).isoformat()

    # write meta
    try:
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(_to_json_serializable(meta), f, indent=2)
    except Exception as e:
        log.exception("Failed to write neural session meta: %s", e)

    # write features as JSON-safe
    try:
        with open(features_path, "w", encoding="utf-8") as f:
            json.dump(_to_json_serializable(features), f, indent=2)
    except Exception as e:
        log.exception("Failed to write neural session features: %s", e)

    # Run lightweight classifier (if available) to predict cognitive tags and
    # store predictions in both meta and features files (best-effort)
    try:
        from models.neuro_classifier import predict_tags
        preds = predict_tags(features)
        if preds:
            # Store predictions in both meta and features
            meta.setdefault('predicted_tags', preds)
            features['predicted_tags'] = preds

            # Update both files
            try:
                with open(meta_path, 'w', encoding='utf-8') as f:
                    json.dump(_to_json_serializable(meta), f, indent=2)
                with open(features_path, 'w', encoding='utf-8') as f:
                    json.dump(_to_json_serializable(features), f, indent=2)
            except Exception as e:
                log.warning("Failed to save predictions: %s", e)
    except Exception as e:
        log.warning("Failed to generate predictions: %s", e)
        preds = {}

    # write embedding as numpy binary if provided
    try:
        if embedding is not None:
            np.save(embedding_path, np.asarray(embedding))
    except Exception as e:
        log.exception("Failed to write neural session embedding: %s", e)

    # mark in episodic store for discoverability
    try:
        add_episode("neural.session.save", json.dumps({"session_id": session_id}), {"meta": meta})
    except Exception as e:
        log.exception("Failed to add episodic marker for neural session: %s", e)

    return {"session_id": session_id, "meta_path": meta_path, "features_path": features_path, "embedding_path": embedding_path}


def _list_neural_sessions(limit: int = 20):
    """Return recent session ids sorted by meta file mtime (descending)."""
    pattern = os.path.join(NEURAL_STATE_DIR, "*.meta.json")
    files = glob.glob(pattern)
    files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    sessions = []
    for p in files[:limit]:
        name = os.path.basename(p)
        sid = name.rsplit(".", 2)[0]
        sessions.append({"session_id": sid, "meta_path": p, "mtime": os.path.getmtime(p)})
    return sessions


def load_last_neural_embeddings(n: int = 4):
    """Load embeddings for the most recent n sessions. Returns list of (session_id, embedding).

    Skips sessions without embeddings.
    """
    sessions = _list_neural_sessions(limit=n * 2)  # overfetch to allow skipping
    loaded = []
    for s in sessions:
        sid = s["session_id"]
        emb_path = os.path.join(NEURAL_STATE_DIR, f"{sid}.embedding.npy")
        if os.path.exists(emb_path):
            try:
                emb = np.load(emb_path)
                loaded.append((sid, emb))
                if len(loaded) >= n:
                    break
            except Exception as e:
                log.exception("Failed to load embedding for %s: %s", sid, e)
    return loaded


def get_recent_neural_context(window_seconds: int = 300, max_embeddings: int = 8):
    """Return an aggregated neural context from recent embeddings within window_seconds.

    Returns None if no usable embeddings found. Otherwise returns dict with:
     - avg_embedding: numpy array
     - sessions: list of session ids used
     - summary: minimal metadata (count, latest_timestamp)
    """
    now = time.time()
    sessions = _list_neural_sessions(limit=max_embeddings * 3)
    used = []
    embs = []
    for s in sessions:
        # read meta timestamp when available
        try:
            with open(s["meta_path"], "r", encoding="utf-8") as f:
                meta = json.load(f)
            ts_str = meta.get("timestamp")
            if ts_str:
                try:
                    # attempt ISO parse (very permissive)
                    ts = datetime.fromisoformat(ts_str.replace("Z", "")).timestamp()
                except Exception:
                    ts = s.get("mtime", os.path.getmtime(s["meta_path"]))
            else:
                ts = s.get("mtime", os.path.getmtime(s["meta_path"]))
        except Exception:
            ts = s.get("mtime", os.path.getmtime(s["meta_path"]))

        if now - ts > window_seconds:
            continue

        emb_path = os.path.join(NEURAL_STATE_DIR, f"{s['session_id']}.embedding.npy")
        if os.path.exists(emb_path):
            try:
                emb = np.load(emb_path)
                embs.append(emb)
                used.append(s["session_id"])
            except Exception as e:
                log.exception("Failed to load embedding %s: %s", emb_path, e)

        if len(embs) >= max_embeddings:
            break

    if not embs:
        return None

    # Ensure all embeddings have the same shape before stacking
    try:
        if not embs:
            return None
        target_shape = embs[0].shape
        embs_filtered = [e for e in embs if getattr(e, 'shape', None) == target_shape]
        if not embs_filtered:
            return None
        avg = np.mean(np.stack(embs_filtered, axis=0), axis=0)
    except Exception as e:
        log.exception("Failed to compute average embedding: %s", e)
        return None

    # Attempt to load latest features JSON for convenience (best-effort)
    latest_features = None
    if used:
        latest_sid = used[0]
        feat_path = os.path.join(NEURAL_STATE_DIR, f"{latest_sid}.features.json")
        if os.path.exists(feat_path):
            try:
                with open(feat_path, 'r', encoding='utf-8') as f:
                    latest_features = json.load(f)
            except Exception:
                latest_features = None

    return {
        "avg_embedding": avg,
        "sessions": used,
        "summary": {"count": len(used), "latest": used[0] if used else None},
        "latest_features": latest_features
    }

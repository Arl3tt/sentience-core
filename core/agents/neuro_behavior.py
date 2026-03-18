"""Neuro-conditioned behavior helpers

Simple utilities for selecting a policy from neural/context features, mutating
system prompts based on selected policy, and performing a hybrid retrieval that
weights semantic search and neural similarity.
"""
from typing import List, Dict, Any
import logging

log = logging.getLogger("neuro_behavior")

# Import memstore and vector_store with safe fallbacks when optional deps are
# not installed (helps test collection in minimal environments).
try:
    from core.memory import memstore
except Exception:
    class _DummyMemstore:
        def semantic_search(self, *args, **kwargs):
            return []

    memstore = _DummyMemstore()

try:
    from memory import vector_store
except Exception:
    class _DummyVectorStore:
        def query_by_embedding(self, *args, **kwargs):
            return []

    vector_store = _DummyVectorStore()


def select_policy_action(neural_context: Dict[str, Any]) -> str:
    """Choose a policy label based on simple neural features in `neural_context`.

    Expected keys: 'attention' (0..1), optional 'fatigue' (0..1).
    Returns one of: 'boost_focus', 'rest', 'maintain'.
    """
    attention = float(neural_context.get("attention", 0.5))
    fatigue = float(neural_context.get("fatigue", 0.0))
    if attention >= 0.7 and fatigue < 0.6:
        return "boost_focus"
    if attention <= 0.3 or fatigue >= 0.7:
        return "rest"
    return "maintain"


def mutate_system_prompt(system_prompt: str, policy: str) -> str:
    """Return a mutated system prompt that nudges behavior according to `policy`.

    This is intentionally simple: it appends short instructions that downstream
    LLM callers can use.
    """
    additions = {
        "boost_focus": (
            "Prioritize concise, high-focus steps and minimize small talk."
        ),
        "rest": (
            "Suggest short rest, breathing, or low-effort tasks to recover attention."
        ),
        "maintain": "Proceed as normal, balancing depth and brevity.",
    }
    suffix = additions.get(policy, "")
    if suffix:
        return (
            f"{system_prompt}\n\n[NeuroPolicy:{policy}] "
            f"{suffix}"
        )
    return system_prompt


def neuro_weighted_retrieval(
    query: str,
    alpha: float,
    beta: float,
    neural_embedding: List[float],
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """Hybrid retrieval that combines semantic relevance and neural similarity.

    - `alpha` weights semantic (text) relevance.
    - `beta` weights neural similarity (embedding closeness to `neural_embedding`).

    If semantic search or vector-by-embedding fail, falls back gracefully.
    Returns a list of hits sorted by combined score.
    """
    semantic_hits = []
    try:
        semantic_hits = memstore.semantic_search(query, top_k=top_k) or []
    except Exception as e:
        log.debug("semantic_search failed: %s", e)

    neural_hits = []
    try:
        if neural_embedding is not None:
            neural_hits = vector_store.query_by_embedding(neural_embedding, top_k=top_k) or []
    except Exception as e:
        log.debug("query_by_embedding failed: %s", e)

    # Build score maps
    scores = {}
    # Semantic: assign a normalized score based on rank if explicit score missing
    for idx, h in enumerate(semantic_hits):
        hid = str(h.get("id"))
        s = None
        if isinstance(h, dict) and "score" in h and h["score"] is not None:
            try:
                s = float(h["score"])
            except Exception:
                s = None
        if s is None:
            # fallback: higher rank => higher score
            s = 1.0 / (idx + 1)
        scores.setdefault(
            hid,
            {
                "semantic": 0.0,
                "neural": 0.0,
                "doc": h.get("doc") or h.get("text") or h.get("documents"),
            },
        )
        scores[hid]["semantic"] = s

    # Neural hits provide 'score' and 'text'
    for idx, h in enumerate(neural_hits):
        hid = str(h.get("id"))
        s = float(h.get("score", 0.0)) if h.get("score") is not None else (1.0 / (idx + 1))
        scores.setdefault(hid, {"semantic": 0.0, "neural": 0.0, "doc": h.get("text")})
        scores[hid]["neural"] = s

    # Compute combined score and return top_k
    combined = []
    for hid, parts in scores.items():
        sem = parts.get("semantic", 0.0) or 0.0
        neu = parts.get("neural", 0.0) or 0.0
        # simple linear weighting; allow alpha/beta to be zero to disable either branch
        c = (alpha * sem) + (beta * neu)
        combined.append(
            {
                "id": hid,
                "doc": parts.get("doc"),
                "semantic": sem,
                "neural": neu,
                "score": float(c),
            }
        )

    combined.sort(key=lambda x: x["score"], reverse=True)
    return combined[:top_k]

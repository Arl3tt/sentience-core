"""Rule-based neuro policy for minimum viable closed-loop behavior (Mode B)

This module contains a simple deterministic policy that inspects recent
features (provided in neural_ctx['latest_features']) and returns an action.

The policy interface:
  neuro_policy(neural_ctx: dict) -> dict

Returned dict example:
  {"action": "cue_focus", "message": "Micro-break?", "tags": {...}, "scores": {...}}
"""
from typing import Dict, Any
import numpy as np


def _mean_of(feature, default=0.0):
    try:
        return float(np.mean(np.array(feature, dtype=float)))
    except Exception:
        return float(default)


def neuro_policy(neural_ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Inspect neural context and return a simple action decision.

    Rules (first-match):
      - low alpha + high beta -> protect_flow / deep_work
      - high theta -> anti-drowsy cue
      - elevated spectral entropy -> simplify UI
      - stable high gamma -> protect flow

    Scoring is heuristic and intended as a starting point.
    """
    if not neural_ctx:
        return {"action": "neutral", "message": "no_neural_context"}

    features = neural_ctx.get("latest_features")
    if not features:
        return {"action": "neutral", "message": "no_features"}

    alpha = _mean_of(features.get('alpha_power'))
    beta = _mean_of(features.get('beta_power'))
    theta = _mean_of(features.get('theta_power'))
    gamma = _mean_of(features.get('gamma_power'))
    entropy = _mean_of(features.get('spectral_entropy'))

    # compute normalized ratios (avoid div-by-zero)
    alpha_beta = (alpha / (beta + 1e-9))
    theta_beta = (theta / (beta + 1e-9))

    # Rule: high theta indicates drowsiness/fatigue
    if theta > 0.5 * (alpha + beta + 1e-9):
        return {"action": "cue_anti_drowsy", "message": "Detected high theta — suggest alertness cue", "tags": {"fatigue": 0.9}}

    # Rule: low alpha + high beta -> focused/deep work
    if alpha_beta < 0.6 and beta > alpha:
        return {"action": "protect_flow", "message": "Brain state suggests focused work — minimize interruptions", "tags": {"flow": 0.8}}

    # Rule: elevated spectral entropy -> simplify UI
    if entropy > 5.5:
        return {"action": "simplify", "message": "High neural entropy detected — simplify stimuli", "tags": {"complexity": entropy}}

    # Rule: gamma burst (heuristic)
    if gamma > 0.8 * max(alpha, beta, theta + 1e-9):
        return {"action": "protect_flow", "message": "Gamma elevated — preserve current context", "tags": {"flow": 0.7}}

    return {"action": "neutral", "message": "no_rule_matched"}

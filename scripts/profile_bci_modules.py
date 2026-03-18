"""
Profile latency and throughput for core BCI modules.

Usage: python scripts/profile_bci_modules.py

Produces a small JSON report printed to stdout.
"""
import time
import json
import numpy as np
from statistics import mean

import sys
import os

# Ensure the repository root is on sys.path so `core` can be imported when
# running this script directly.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.tools import (
    classify_brainwave_bands,
    classify_cognitive_state,
    classify_multi_channel,
    classify_motor_imagery,
    extract_motor_imagery_features,
    P300Speller,
    create_speller_interface,
    create_neurofeedback_session,
    create_hybrid_bci,
    create_asd_analyzer
)

REPORT = {}

# Synthetic data settings
SAMPLES = 2500  # 10s at 250 Hz
CHANNELS = 8
FS = 250.0

signal = np.random.randn(SAMPLES, CHANNELS).astype(float)

def time_function(fn, *args, repeats=5, warmup=1, **kwargs):
    # warmup
    for _ in range(warmup):
        fn(*args, **kwargs)
    times = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn(*args, **kwargs)
        t1 = time.perf_counter()
        times.append(t1 - t0)
    return {"times": times, "avg": mean(times), "min": min(times), "max": max(times)}

# Brain wave classifier
bw_result = time_function(classify_cognitive_state, signal[:, 0], fs=FS)
REPORT['brain_wave_classifier'] = {
    "latency_avg_s": bw_result['avg'],
    "samples": SAMPLES,
    "throughput_sps": SAMPLES / bw_result['avg'] if bw_result['avg']>0 else None
}

# Multi-channel classification
mc_result = time_function(classify_multi_channel, signal, fs=FS)
REPORT['brain_wave_multi_channel'] = {
    "latency_avg_s": mc_result['avg'],
    "samples": SAMPLES,
    "channels": CHANNELS,
    "throughput_sps": (SAMPLES * CHANNELS) / mc_result['avg'] if mc_result['avg']>0 else None
}

# Motor imagery
mi_result = time_function(classify_motor_imagery, signal, fs=FS)
REPORT['motor_imagery'] = {
    "latency_avg_s": mi_result['avg'],
    "throughput_sps": SAMPLES / mi_result['avg'] if mi_result['avg']>0 else None
}

# Motor imagery feature extraction
mi_feat = time_function(extract_motor_imagery_features, signal, fs=FS)
REPORT['motor_imagery_features'] = {"latency_avg_s": mi_feat['avg']}

# P300 speller
sp = P300Speller()
# create a trial chunk: single flash epoch (1000 samples x channels)
epoch = np.random.randn(1000, CHANNELS)
sp_feature = time_function(sp.extract_p300_features, epoch, fs=FS)
sp_detect = time_function(sp.detect_p300, epoch, fs=FS)
REPORT['p300_speller'] = {
    "feature_latency_s": sp_feature['avg'],
    "detect_latency_s": sp_detect['avg']
}

# Neurofeedback
from core.tools import NeurofeedbackEngine, FeedbackTarget, FeedbackModality

engine = NeurofeedbackEngine()
nf_result = time_function(engine.create_neurofeedback_session, FeedbackTarget.RELAXATION, FeedbackModality.VISUAL, session_duration=60)
REPORT['neurofeedback'] = {"create_session_latency_s": nf_result['avg']}

# Hybrid BCI creation
try:
    hb = create_hybrid_bci()
    REPORT['hybrid_bci'] = {"creation_ok": True}
except Exception as e:
    REPORT['hybrid_bci'] = {"creation_ok": False, "error": str(e)}

# ASD analyzer creation
try:
    asd = create_asd_analyzer()
    REPORT['asd_analyzer'] = {"creation_ok": True}
except Exception as e:
    REPORT['asd_analyzer'] = {"creation_ok": False, "error": str(e)}

print(json.dumps(REPORT, indent=2))

"""
Neurofeedback loop utilities.

Provides a simple streaming NeurofeedbackEngine that computes bandpower
and invokes a callback with feedback values at a configurable interval.
Designed for testing and profiling; replace callback with UI hooks in real apps.
"""
from enum import Enum
from typing import Dict, Any, Optional, Tuple, Callable
import numpy as np
import threading
import time
from scipy import signal, integrate


class FeedbackTarget(Enum):
    RELAXATION = "relaxation"
    FOCUS = "focus"
    AROUSAL = "arousal"
    CALMNESS = "calmness"


class FeedbackModality(Enum):
    VISUAL = "visual"
    AUDITORY = "auditory"
    PROPRIOCEPTIVE = "proprioceptive"
    COMBINED = "combined"


def bandpower(eeg: np.ndarray, fs: float, band: tuple) -> float:
    f, Pxx = signal.welch(eeg, fs=fs, nperseg=min(256, len(eeg)))
    idx = (f >= band[0]) & (f <= band[1])
    return float(integrate.trapezoid(Pxx[idx], f[idx])) if np.any(idx) else 0.0


class NeurofeedbackEngine:
    def __init__(self, fs: float = 250.0, buffer_size: int = 1000, feedback_callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        self.fs = fs
        self.buffer_size = buffer_size
        self.feedback_callback = feedback_callback
        self._buffer = []
        self._running = False
        self._thread = None

    def _compute_feedback(self):
        if not self._buffer:
            return {"alpha_ratio": 0.0, "beta_ratio": 0.0}
        data = np.concatenate(self._buffer, axis=-1) if isinstance(self._buffer[0], np.ndarray) else np.array(self._buffer)
        if data.ndim > 1:
            data = np.mean(data, axis=0)
        a = bandpower(data, self.fs, (8, 13))
        b = bandpower(data, self.fs, (13, 30))
        total = a + b + 1e-9
        return {"alpha_ratio": float(a / total), "beta_ratio": float(b / total)}

    def _loop(self, interval_s: float):
        while self._running:
            fb = self._compute_feedback()
            if self.feedback_callback:
                try:
                    self.feedback_callback(fb)
                except Exception:
                    pass
            time.sleep(interval_s)

    def start(self, interval_s: float = 1.0):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, args=(interval_s,), daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)

    def push(self, eeg_window: np.ndarray):
        # eeg_window: channels x samples or 1D
        if not isinstance(eeg_window, np.ndarray):
            eeg_window = np.array(eeg_window)
        self._buffer.append(eeg_window)
        if len(self._buffer) > self.buffer_size:
            self._buffer.pop(0)

    def create_neurofeedback_session(self, target: FeedbackTarget, modality: FeedbackModality, session_duration: float = 600.0) -> Dict[str, Any]:
        # return a small session descriptor
        return {"session_id": f"nf_{int(time.time())}", "target": target.value, "modality": modality.value, "duration_s": session_duration}


def create_neurofeedback_session(target: FeedbackTarget, modality: FeedbackModality, session_duration: float = 600.0) -> Tuple[NeurofeedbackEngine, Dict[str, Any]]:
    engine = NeurofeedbackEngine()
    session = engine.create_neurofeedback_session(target, modality, session_duration)
    return engine, session

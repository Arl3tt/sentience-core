"""
P300 Speller utility classes and helpers.

This module provides a lightweight ERP feature extractor and simple detector
that can be used for integration tests and profiling. For production use,
replace with a trained classifier and more sophisticated averaging.
"""
import numpy as np
from typing import Dict, Tuple
from scipy import signal


class P300Speller:
    def __init__(self, num_channels: int = 8, downsample_rate: int = 6):
        self.num_channels = num_channels
        self.downsample_rate = downsample_rate

    def extract_p300_features(self, eeg_signal: np.ndarray, fs: float = 250.0) -> Dict[str, float]:
        """Extract simple ERP features: peak amplitude and latency on averaged channels.

        Handles both (samples, channels) and (channels, samples) orientations.
        """
        if eeg_signal.ndim == 2:
            # if first dim is longer than second, assume (samples, channels)
            if eeg_signal.shape[0] >= eeg_signal.shape[1]:
                data = np.mean(eeg_signal, axis=1)
            else:
                data = np.mean(eeg_signal, axis=0)
        else:
            data = eeg_signal

        # bandpass 1-12 Hz typical for P300
        b, a = signal.butter(3, [1 / (fs / 2), 12 / (fs / 2)], btype="band")
        filt = signal.filtfilt(b, a, data)

        peak_idx = np.argmax(np.abs(filt))
        peak_amp = float(filt[peak_idx])
        peak_time = float(peak_idx) / fs
        return {"peak_amp": peak_amp, "peak_time_s": peak_time}

    def detect_p300(self, eeg_signal: np.ndarray, fs: float = 250.0, threshold: float = 0.5) -> Tuple[bool, float]:
        feats = self.extract_p300_features(eeg_signal, fs)
        score = abs(feats.get("peak_amp", 0.0))
        return (score >= threshold, float(score))

    def classify_p300_response(self, row_scores: np.ndarray, col_scores: np.ndarray) -> Tuple[int, int, float]:
        # pick max score indices
        r = int(np.argmax(row_scores))
        c = int(np.argmax(col_scores))
        confidence = float(max(row_scores.max(), col_scores.max()))
        return r, c, confidence

    def select_character(self, row: int, col: int) -> str:
        # simple 6x6 lookup if indices are within range
        table = [
            list("ABCDEF"),
            list("GHIJKL"),
            list("MNOPQR"),
            list("STUVWX"),
            list("YZ0123"),
            list("456789"),
        ]
        try:
            return table[row][col]
        except Exception:
            return "?"


def extract_p300_features(eeg_signal: np.ndarray, fs: float = 250.0) -> Dict[str, float]:
    sp = P300Speller()
    return sp.extract_p300_features(eeg_signal, fs)


def classify_p300_response(row_scores: np.ndarray, col_scores: np.ndarray) -> Tuple[int, int, float]:
    sp = P300Speller()
    return sp.classify_p300_response(row_scores, col_scores)


def create_speller_interface(num_channels: int = 8) -> P300Speller:
    return P300Speller(num_channels=num_channels)

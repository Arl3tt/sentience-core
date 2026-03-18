"""Real-time runner for OpenBCI Cyton that pipes windows into the preprocessing
and memory pipeline.

Features:
- Connects to a Cyton via pyOpenBCI (port configurable)
- Buffers samples into sliding windows and runs `preprocess_eeg`
- Persists each window as a neural session via `save_neural_session`
- Has a simulation mode that reads a recorded OpenBCI txt file and streams samples
  at the recorded sample rate (useful when hardware is not present)

Notes:
- Heavy operations (ICA, embedding) run in a worker thread so the board callback
  isn't blocked.
"""
from __future__ import annotations
import time
import argparse
import threading
import queue
from collections import deque
from pathlib import Path
import numpy as np
import traceback

try:
    from pyOpenBCI import OpenBCICyton
    HAS_PYOPENBCI = True
except Exception:
    HAS_PYOPENBCI = False

from data.openbci_reader import read_openbci_txt
from models.eeg_preprocessing import preprocess_eeg, FeatureHistory
from memory.memory_controller import save_neural_session


class LiveRunner:
    def __init__(self, port: str | None = None, fs: int = 250, window_s: float = 4.0, hop_s: float = 1.0,
                 channels: int | None = None, simulate_file: str | None = None):
        self.port = port
        self.fs = int(fs)
        self.window_s = float(window_s)
        self.hop_s = float(hop_s)
        self.window_samples = int(self.window_s * self.fs)
        self.hop_samples = max(1, int(self.hop_s * self.fs))
        self.channels = channels
        self.simulate_file = simulate_file

        # circular buffer for incoming samples (each sample is array of channels)
        self.buffer = deque(maxlen=self.window_samples)
        self.sample_counter = 0

        # worker queue for processing windows
        self.work_q: queue.Queue = queue.Queue()
        self.running = False
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)

        # feature history to provide temporal trends
        self.feature_history = FeatureHistory(window_size=10)

    def start(self):
        self.running = True
        self.worker_thread.start()

        if self.simulate_file:
            print(f"Simulation mode: streaming from {self.simulate_file}")
            signals, fs, channel_names = read_openbci_txt(self.simulate_file)
            self.fs = fs
            self.window_samples = int(self.window_s * self.fs)
            self.hop_samples = max(1, int(self.hop_s * self.fs))
            # stream samples at recorded rate
            for i in range(signals.shape[0]):
                sample = signals[i, :]
                self._handle_sample(sample)
                time.sleep(1.0 / float(self.fs))
                if not self.running:
                    break
            self.stop()
            return

        if not HAS_PYOPENBCI:
            raise RuntimeError("pyOpenBCI is not available in this environment. Install it or use --simulate")

        print(f"Connecting to OpenBCI Cyton on port {self.port} (fs={self.fs})")
        board = OpenBCICyton(port=self.port)
        try:
            # start_stream will call our callback with a sample object
            board.start_stream(self._cb_sample)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.running = False
        # allow worker to finish queued items
        self.work_q.put(None)
        print("Stopping live runner...")
        # join worker thread if it's alive
        try:
            if self.worker_thread.is_alive():
                self.worker_thread.join(timeout=2.0)
        except Exception:
            pass

    def _cb_sample(self, sample):
        # pyOpenBCI sample.channels_data is a list of floats
        arr = np.asarray(sample.channels_data, dtype=float)
        self._handle_sample(arr)

    def _handle_sample(self, arr: np.ndarray):
        # initialize channel count if unknown
        if self.channels is None:
            self.channels = arr.shape[0]

        self.buffer.append(arr)
        self.sample_counter += 1

        # when enough samples and on hop boundary, queue a processing job
        if len(self.buffer) >= self.window_samples and (self.sample_counter % self.hop_samples == 0):
            # snapshot current window
            window = np.stack(list(self.buffer), axis=0)
            timestamp = time.time()
            # push to worker queue (non-blocking)
            try:
                self.work_q.put_nowait((timestamp, window))
            except queue.Full:
                # drop if worker queue is busy
                pass

    def _worker_loop(self):
        print("Worker thread started")
        while True:
            item = self.work_q.get()
            if item is None:
                break
            timestamp, window = item
            try:
                self._process_window(timestamp, window)
            except Exception as e:
                print("Error processing window:", e)
                # print traceback for debugging
                print(traceback.format_exc())

    def _process_window(self, timestamp: float, window: np.ndarray):
        # window shape: (samples, channels)
        # defensive check
        if window is None or not hasattr(window, 'shape') or window.size == 0:
            print(f"Skipping empty window at {timestamp:.2f}")
            return
        print(f"Processing window at {timestamp:.2f}, shape={window.shape}")
        cleaned, features = preprocess_eeg(window, fs=self.fs, feature_history=self.feature_history)

        # build session meta
        session_meta = {
            # use millisecond resolution to avoid collisions when windows land
            # within the same second
            'session_id': f"live_{int(timestamp * 1000)}",
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(timestamp)),
            'source': 'openbci_cyton_live',
            'num_samples': int(window.shape[0]),
            'sample_rate': int(self.fs),
            'channel_count': int(window.shape[1])
        }

        # embedding: preprocess_eeg already attaches features['embedding'] when possible
        embedding = None
        try:
            emb = features.get('embedding')
            if emb:
                embedding = np.asarray(emb, dtype=float)
        except Exception:
            embedding = None

        # persist session (best-effort)
        try:
            res = save_neural_session(session_meta, features, embedding)
            print("Saved live session:", res.get('session_id'))
        except Exception as e:
            print("Failed to save live session:", e)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--port', default=None, help='Serial port for Cyton (e.g., COM3)')
    p.add_argument('--fs', type=int, default=250)
    p.add_argument('--window', type=float, default=4.0, help='Window size in seconds')
    p.add_argument('--hop', type=float, default=1.0, help='Hop size in seconds')
    p.add_argument('--simulate', default=None, help='Path to OpenBCI txt file to simulate live stream')
    p.add_argument('--max-samples', type=int, default=0, help='When simulating, stop after this many samples (0 => all)')
    args = p.parse_args()

    runner = LiveRunner(port=args.port, fs=args.fs, window_s=args.window, hop_s=args.hop, simulate_file=args.simulate)
    try:
        if args.simulate and args.max_samples and args.max_samples > 0:
            # when simulating, limit number of samples by temporarily overriding
            # the method to stream only a prefix
            signals, fs, channel_names = read_openbci_txt(args.simulate)
            runner.fs = fs
            runner.window_samples = int(runner.window_s * runner.fs)
            runner.hop_samples = max(1, int(runner.hop_s * runner.fs))
            max_n = min(args.max_samples, signals.shape[0])
            # start worker thread to process queued windows
            runner.worker_thread.start()
            for i in range(max_n):
                runner._handle_sample(signals[i, :])
            # allow queued jobs to finish
            time.sleep(1.0)
            runner.stop()
        else:
            runner.start()
    except KeyboardInterrupt:
        runner.stop()


if __name__ == '__main__':
    main()

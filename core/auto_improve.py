#!/usr/bin/env python3
"""
auto_improve.py - Automated model improvement system
Monitors training history and enqueues jobs to improve performance
"""
import threading
import time
from typing import Dict, Any
import numpy as np
from core.brain import EXEC_QUEUE
from core.tools.model_logger import get_latest_metrics

# Target accuracy threshold
TARGET_ACCURACY = 0.95

# Parameters to try varying for improvement
PARAM_RANGES = {
    "n_samples": [200, 400, 800],
    "n_channels": [4, 8, 16],
    "duration_s": [0.5, 1.0, 2.0],
    "sfreq": [64, 128, 256]
}

class AutoImproveManager(threading.Thread):
    def __init__(self, check_interval: int = 300):
        """Initialize manager with check interval in seconds"""
        super().__init__(daemon=True)
        self.check_interval = check_interval
        self._running = True
        
    def stop(self):
        """Stop the manager thread"""
        self._running = False
    
    def generate_next_params(self, current_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Generate new parameters to try based on history"""
        # Simple random sampling for now
        params = {
            param: np.random.choice(values)
            for param, values in PARAM_RANGES.items()
        }
        return params
    
    def enqueue_training_job(self, params: Dict[str, Any]):
        """Create and enqueue a preapproved training job"""
        cmd = "python core/tools/train_sim_eeg.py"
        if params:
            param_str = " ".join(f"--{k} {v}" for k, v in params.items())
            cmd = f"{cmd} {param_str}"
            
        item = {
            "task": {
                "title": "AutoImproveEEG",
                "desc": f"Automated training with params: {params}"
            },
            "research_summary": "Automatic model improvement attempt",
            "hits": [],
            "preapproved_action": {
                "action": "run_shell",
                "args": {"cmd": cmd}
            }
        }
        EXEC_QUEUE.put(item)
    
    def run(self):
        """Main improvement loop"""
        while self._running:
            try:
                # Get latest metrics
                metrics = get_latest_metrics()
                
                # Check if any model needs improvement
                for model_id, accuracy in metrics.items():
                    if accuracy < TARGET_ACCURACY:
                        # Generate and try new parameters
                        params = self.generate_next_params(metrics)
                        self.enqueue_training_job(params)
                        
            except Exception as e:
                print(f"Error in auto-improve loop: {e}")
                
            # Wait for next check
            time.sleep(self.check_interval)
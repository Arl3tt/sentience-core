#!/usr/bin/env python3
"""
model_logger.py - Log and track model training history
Records training metrics to CSV and notifies on improvements
"""
import csv
import json
import os
from datetime import datetime
from typing import Dict, Any
import ui.voice as voice
import core.memory as memory

HISTORY_FILE = os.path.join("data", "model_history.csv")
FIELDNAMES = ["timestamp", "model_id", "accuracy", "params", "notes"]

def ensure_history_file():
    """Ensure history CSV exists with headers"""
    if not os.path.exists(HISTORY_FILE):
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        with open(HISTORY_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()

def get_latest_metrics() -> Dict[str, float]:
    """Get the most recent metrics for each model type"""
    ensure_history_file()
    latest = {}
    try:
        with open(HISTORY_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                model_id = row["model_id"]
                accuracy = float(row["accuracy"])
                latest[model_id] = accuracy
    except (FileNotFoundError, ValueError):
        pass
    return latest

def log_training_result(result: Dict[str, Any]):
    """
    Log a training result to CSV history and memory episodes
    Announces improvements via TTS
    """
    ensure_history_file()
    
    # Parse the training result
    model_id = result.get("model_id", "unknown")
    accuracy = float(result.get("accuracy", 0))
    params = json.dumps(result.get("params", {}))
    notes = result.get("notes", "")
    
    # Get previous best accuracy
    latest_metrics = get_latest_metrics()
    prev_best = latest_metrics.get(model_id, 0)
    
    # Log to CSV
    row = {
        "timestamp": datetime.now().isoformat(),
        "model_id": model_id,
        "accuracy": accuracy,
        "params": params,
        "notes": notes
    }
    with open(HISTORY_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow(row)
    
    # Log to episodes
    episode_text = f"Training completed for {model_id}. Accuracy: {accuracy:.3f}"
    if accuracy > prev_best:
        improvement = accuracy - prev_best
        episode_text += f"\nImproved by {improvement:.3f} over previous best {prev_best:.3f}"
        # call through module so tests can monkeypatch `ui.voice.speak`
        try:
            voice.speak(f"Model accuracy improved by {improvement:.1%}")
        except Exception:
            pass

    # call through memory module so tests can monkeypatch `core.memory.add_episode`
    try:
        memory.add_episode("model_training", episode_text)
    except Exception:
        pass
    
    return {
        "prev_best": prev_best,
        "new_accuracy": accuracy,
        "improved": accuracy > prev_best
    }
#!/usr/bin/env python3
"""
enqueue_training.py - Manual task enqueuing script

Demonstrates how to directly enqueue a preapproved action for the Executor agent
to run without LLM interaction. Useful for automated/scripted workflows.
"""
from core.brain import EXEC_QUEUE

def enqueue_training_task():
    # Create a task item in the format expected by the Executor
    item = {
        "task": {
            "title": "TrainSimEEG",
            "desc": "Run the synthetic EEG training stub"
        },
        "research_summary": "Run the training stub to create a toy model",
        "hits": [],
        # Preapproved action bypasses LLM and executes directly
        "preapproved_action": {
            "action": "run_shell",
            "args": {"cmd": "python core/tools/train_sim_eeg.py"}
        }
    }

    # Place directly in EXEC_QUEUE - will be picked up by Executor
    EXEC_QUEUE.put(item)
    print("Enqueued training task; Executor will pick it up automatically.")

if __name__ == "__main__":
    enqueue_training_task()
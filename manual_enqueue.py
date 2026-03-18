# manual_enqueue.py (run from project root)
from core.brain import EXEC_QUEUE

item = {
    "task": {"title": "TrainSimEEG", "desc": "Run the synthetic EEG training stub"},
    "research_summary": "Run the training stub to create a toy model",
    "hits": []
}
# Place in EXEC_QUEUE in the same shape the Researcher would push.
# The Executor expects to call the LLM to propose an action, but we can instead
# directly put in a special field 'preapproved_action' and modify Executor to honor it.
item["preapproved_action"] = {
    "action": "run_shell",
    "args": {"cmd": "python core/tools/train_sim_eeg.py"}
}
EXEC_QUEUE.put(item)
print("Enqueued training item; Executor will pick it up.")
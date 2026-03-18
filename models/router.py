# Model router: choose embedding/LLM based on task type (simple policy)
from config import LLM_MODEL, EMBEDDING_MODEL
def choose_llm(task_type='general'):
    # expand policy later
    return LLM_MODEL
def choose_embedding():
    return EMBEDDING_MODEL

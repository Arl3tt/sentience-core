"""
Test script for LangGraph workflow
"""
import logging
from core.langgraph_runner import SentienceWorkflow

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def test_workflow():
    """Run a simple workflow test"""
    workflow = SentienceWorkflow()

    test_goal = "Train a synthetic EEG model to improve accuracy"

    log.info(f"Running workflow with goal: {test_goal}")

    result = workflow.run(test_goal)
    log.info("Workflow completed successfully")
    log.info(f"Final result: {result}")
    assert result is not None, "Workflow result should not be None"

if __name__ == "__main__":
    test_workflow()
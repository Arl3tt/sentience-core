# core.brain: orchestrates agents and provides shared queues
import queue
from core.agents import Planner, Researcher, Executor, Critic

GOAL_QUEUE = queue.Queue()
TASK_QUEUE = queue.Queue()
EXEC_QUEUE = queue.Queue()
RESULT_QUEUE = queue.Queue()


def start_agents():
    planner = Planner(goal_q=GOAL_QUEUE, task_q=TASK_QUEUE)
    researcher = Researcher(task_q=TASK_QUEUE, exec_q=EXEC_QUEUE)
    executor = Executor(exec_q=EXEC_QUEUE, result_q=RESULT_QUEUE)
    critic = Critic(result_q=RESULT_QUEUE, goal_q=GOAL_QUEUE)

    planner.start()
    researcher.start()
    executor.start()
    critic.start()

    return planner, researcher, executor, critic


def stop_agents(planner, researcher, executor, critic):
    planner.stop()
    researcher.stop()
    executor.stop()
    critic.stop()

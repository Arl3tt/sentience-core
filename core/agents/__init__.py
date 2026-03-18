#!/usr/bin/env python3
"""Package wrapper exposing agent classes and helpers.

This file contains the core agent implementations previously located in
core/agents.py; having them under the package allows imports like
from core.agents import Planner and submodule imports like
from core.agents.neuro_behavior import ... to coexist.
"""
import threading
import json
import time
from openai import OpenAI
from config import OPENAI_API_KEY, LLM_MODEL, SAFE_MODE
from memory.memory_controller import semantic_search, store_memory
from core.tools.tool_runner import run_python_snippet, run_shell
try:
    from ui.voice import speak
except Exception:
    def speak(*args, **kwargs):
        return None

client = OpenAI(api_key=OPENAI_API_KEY)


def call_llm(prompt, max_tokens: int = 600, temp: float = 0.2) -> str:
    messages = [
        {"role": "system", "content": "You are Hybrid Copilot agent."},
        {"role": "user", "content": prompt},
    ]
    res = client.chat.completions.create(
        model=LLM_MODEL, messages=messages, max_tokens=max_tokens, temperature=temp
    )
    text = res.choices[0].message.content.strip()
    store_memory(text, {"kind": "llm"})
    return text


class AgentBase(threading.Thread):
    def __init__(self, name: str):
        super().__init__(daemon=True)
        self.name = name
        self._running = True

    def stop(self) -> None:
        self._running = False


class Planner(AgentBase):
    def __init__(self, *, goal_q, task_q):
        super().__init__("Planner")
        self.goal_q = goal_q
        self.task_q = task_q

    def run(self) -> None:
        while self._running:
            try:
                goal = self.goal_q.get(timeout=1)
            except Exception:
                time.sleep(0.2)
                continue

            store_memory(goal, {"kind": "planner.goal"})
            ctx = semantic_search(goal, top_k=4)
            prompt = f"\nGoal: {goal}\nContext:\n"
            for c in ctx:
                prompt += c.get("doc", "")[:500] + "\n---\n"
            prompt += (
                "\nProduce a JSON array of tasks like: "
                "[{\"title\": \"...\", \"desc\": \"...\", \"estimate_hours\": 1.0}]"
            )

            tasks_text = call_llm(prompt)
            try:
                tasks = json.loads(tasks_text)
                for t in tasks:
                    self.task_q.put(t)
                    store_memory(json.dumps(t), {"kind": "planner.task"})
            except Exception:
                # fallback single task
                t = {"title": "PlanResult", "desc": tasks_text, "estimate_hours": 1.0}
                self.task_q.put(t)
                store_memory(tasks_text, {"kind": "planner.task"})


class Researcher(AgentBase):
    def __init__(self, *, task_q, exec_q):
        super().__init__("Researcher")
        self.task_q = task_q
        self.exec_q = exec_q

    def run(self) -> None:
        while self._running:
            try:
                task = self.task_q.get(timeout=1)
            except Exception:
                time.sleep(0.2)
                continue

            store_memory(str(task), {"kind": "researcher.task"})
            q = task.get("desc") or task.get("title")
            hits = semantic_search(q, top_k=5)
            summary_prompt = f"Summarize actionable steps for task: {task.get('title')}\nContext:\n"
            for h in hits:
                summary_prompt += h.get("doc", "")[:600] + "\n---\n"
            summary = call_llm(summary_prompt, max_tokens=400)
            self.exec_q.put({"task": task, "summary": summary, "hits": hits})
            store_memory(summary, {"kind": "researcher.summary"})


class Executor(AgentBase):
    def __init__(self, *, exec_q, result_q):
        super().__init__("Executor")
        self.exec_q = exec_q
        self.result_q = result_q

    def run(self) -> None:
        while self._running:
            try:
                item = self.exec_q.get(timeout=1)
            except Exception:
                time.sleep(0.2)
                continue

            task = item.get("task")
            summary = item.get("summary")

            try:
                # Check for preapproved action first
                if item.get("preapproved_action"):
                    j = item["preapproved_action"]
                    store_memory(json.dumps(j), {"kind": "executor.preapproved"})
                else:
                    # Normal LLM-based action proposal flow
                    action_prompt = (
                        f"Given task: {task}\n"
                        f"Summary: {summary}\n"
                        + (
                            "If runnable code is appropriate, return a JSON like "
                            "{\"action\": \"run_code\", \"args\": {\"code\": \"print('hi')\"}} otherwise return a plan."
                        )
                    )

                    out = call_llm(action_prompt)
                    last = out.strip().splitlines()[-1]
                    try:
                        j = json.loads(last)
                        store_memory(json.dumps(j), {"kind": "executor.proposal"})
                    except Exception:
                        store_memory(out, {"kind": "executor.plan"})
                        self.result_q.put({"task": task, "result": out})
                        continue

                if not item.get("preapproved_action"):
                    speak("Executor proposes an action. Confirm?")
                    if SAFE_MODE:
                        ok = input("Approve action (y/N): ")
                        if ok.strip().lower() != "y":
                            store_memory("aborted_by_user", {"kind": "executor"})
                            continue

                # Execute the action (whether preapproved or LLM-proposed)
                if j["action"] == "run_code":
                    res = run_python_snippet(j["args"].get("code", ""))
                    store_memory(str(res), {"kind": "executor.result"})
                    self.result_q.put({"task": task, "result": res})
                    if not item.get("preapproved_action"):
                        speak("Execution done.")
                elif j["action"] == "run_shell":
                    res = run_shell(j["args"].get("cmd", ""))
                    store_memory(str(res), {"kind": "executor.result"})
                    self.result_q.put({"task": task, "result": res})
                    if not item.get("preapproved_action"):
                        speak("Shell run finished.")
                else:
                    store_memory(json.dumps(j), {"kind": "executor.note"})
                    self.result_q.put({"task": task, "result": str(j)})
            except Exception as e:
                store_memory(str(e), {"kind": "executor.error"})
                self.result_q.put({"task": task, "result": f"Error: {str(e)}"})


class Critic(AgentBase):
    def __init__(self, *, result_q, goal_q):
        super().__init__("Critic")
        self.result_q = result_q
        self.goal_q = goal_q

    def run(self) -> None:
        while self._running:
            try:
                r = self.result_q.get(timeout=1)
            except Exception:
                time.sleep(0.2)
                continue

            # simple reflexion: ask LLM to evaluate result and propose improvements
            summary = r.get("result")
            eval_prompt = f"Evaluate the result: {summary}\nSuggest improvements or next steps (JSON actions or plan)."
            critique = call_llm(eval_prompt, max_tokens=300)
            store_memory(critique, {"kind": "critic"})

            # if critique suggests further tasks, push to goal queue
            last = critique.strip().splitlines()[-1]
            try:
                j = json.loads(last)
                if isinstance(j, list):
                    for item in j:
                        self.goal_q.put(item.get("title") + ": " + item.get("desc"))
            except Exception:
                # ignore parsing errors
                pass

import pytest
from core.agents.neuro_behavior import select_policy_action, mutate_system_prompt


def test_select_policy_action_boost():
	ctx = { "attention": 0.8, "fatigue": 0.1 }
	assert select_policy_action(ctx) == "boost_focus"


def test_select_policy_action_rest():
	ctx = { "attention": 0.2, "fatigue": 0.8 }
	assert select_policy_action(ctx) == "rest"


def test_mutate_system_prompt():
	base = "You are an assistant."
	out = mutate_system_prompt(base, "boost_focus")
	assert "NeuroPolicy:boost_focus" in out
	assert "Prioritize concise" in out

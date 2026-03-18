import os
import tempfile
from unittest import mock

import core.tools.model_logger as model_logger


def test_log_training_result_calls_speak_and_add_episode(tmp_path, monkeypatch):
    # Redirect history file to temp location
    tmpfile = tmp_path / "history.csv"
    monkeypatch.setattr(model_logger, "HISTORY_FILE", str(tmpfile))

    # Patch speak and add_episode to observe calls
    called = {}

    def fake_speak(msg):
        called['speak'] = msg

    def fake_add_episode(role, content, metadata=None):
        called['episode'] = (role, content)

    monkeypatch.setattr('ui.voice.speak', fake_speak)
    monkeypatch.setattr('core.memory.add_episode', fake_add_episode)

    res = model_logger.log_training_result({ "model_id": "m1", "accuracy": 0.9, "params": {} })
    assert res.get('new_accuracy') == 0.9
    # speak should have been called because this is improvement over default 0
    assert 'speak' in called
    assert 'episode' in called

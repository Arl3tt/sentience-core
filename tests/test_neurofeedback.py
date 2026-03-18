from core.tools import NeurofeedbackEngine, FeedbackTarget, FeedbackModality

def test_create_session_and_push(sample_epoch):
    engine = NeurofeedbackEngine()
    session = engine.create_neurofeedback_session(FeedbackTarget.RELAXATION, FeedbackModality.VISUAL, session_duration=10)
    assert isinstance(session, dict) and "session_id" in session

    # push a few windows and ensure internal buffer grows
    before = len(engine._buffer)
    engine.push(sample_epoch)
    engine.push(sample_epoch)
    after = len(engine._buffer)
    assert after >= before + 2

    fb = engine._compute_feedback()
    assert "alpha_ratio" in fb and "beta_ratio" in fb

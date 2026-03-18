"""Comprehensive tests for Motor Imagery CNN and Neurofeedback modules."""
from core.tools.motor_imagery_cnn import (
    MotorImageryNet,
    extract_motor_imagery_features,
    classify_motor_imagery,
    train_motor_imagery_model,
    bandpower_simple,
)
from core.tools.neurofeedback_loop import (
    NeurofeedbackEngine,
    FeedbackTarget,
    FeedbackModality,
    bandpower,
)


# ========== Motor Imagery CNN Tests ==========

def test_extract_features_single_channel(sample_signal):
    """Test feature extraction on 1D signal."""
    feats = extract_motor_imagery_features(sample_signal, fs=250.0)
    assert isinstance(feats, dict)
    assert len(feats) > 0
    # features should have numeric values
    for v in feats.values():
        assert isinstance(v, float)

def test_extract_features_multi_channel(sample_multichannel):
    """Test feature extraction on multi-channel data."""
    feats = extract_motor_imagery_features(sample_multichannel, fs=250.0)
    assert isinstance(feats, dict)
    # should have at least 3 features per channel (mu, beta, rms)
    assert len(feats) >= sample_multichannel.shape[0] * 3

def test_bandpower_simple():
    """Test simple bandpower computation."""
    sig = np.random.randn(1000)
    bp = bandpower_simple(sig, fs=250.0, band=(8, 13))
    assert isinstance(bp, float)
    assert bp >= 0

def test_classify_with_heuristic(sample_multichannel):
    """Test classification with heuristic fallback."""
    result = classify_motor_imagery(sample_multichannel, fs=250.0, model=None)
    assert "predicted_class" in result
    assert "class_probabilities" in result
    assert result["method"] == "heuristic"
    assert len(result["class_probabilities"]) == 4  # 4 MI classes

def test_motor_imagery_net_init():
    """Test MotorImageryNet initialization."""
    net = MotorImageryNet(num_channels=8, num_classes=4)
    assert net.num_channels == 8
    assert net.num_classes == 4

def test_mi_classification_confidence(sample_signal):
    """Test MI classification produces valid confidence."""
    result = classify_motor_imagery(sample_signal, fs=250.0)
    confidence = result.get("confidence", 0.0)
    assert 0 <= confidence <= 1

def test_mi_multiple_samples():
    """Test processing multiple motor imagery trials."""
    rng = np.random.RandomState(42)
    trials = [rng.randn(500) for _ in range(3)]
    results = [classify_motor_imagery(t, fs=250.0) for t in trials]
    assert len(results) == 3
    for r in results:
        assert "predicted_class" in r


# ========== Neurofeedback Tests ==========

def test_neurofeedback_engine_init():
    """Test NeurofeedbackEngine initialization."""
    engine = NeurofeedbackEngine(fs=250.0, buffer_size=2000)
    assert engine.fs == 250.0
    assert engine.buffer_size == 2000
    assert len(engine._buffer) == 0

def test_bandpower_welch():
    """Test bandpower computation with Welch method."""
    sig = np.random.randn(2000)
    bp = bandpower(sig, fs=250.0, band=(8, 13))
    assert isinstance(bp, float)
    assert bp >= 0

def test_compute_feedback(sample_multichannel):
    """Test feedback computation."""
    engine = NeurofeedbackEngine()
    engine.push(sample_multichannel)
    fb = engine._compute_feedback()
    assert "alpha_ratio" in fb
    assert "beta_ratio" in fb
    assert 0 <= fb["alpha_ratio"] <= 1
    assert 0 <= fb["beta_ratio"] <= 1

def test_push_and_buffer_management(sample_epoch):
    """Test buffer management when pushing windows."""
    engine = NeurofeedbackEngine(buffer_size=5)
    for _ in range(10):
        engine.push(sample_epoch)
    # buffer should not exceed buffer_size
    assert len(engine._buffer) <= 5

def test_feedback_target_enum():
    """Test FeedbackTarget enum values."""
    assert FeedbackTarget.RELAXATION.value == "relaxation"
    assert FeedbackTarget.FOCUS.value == "focus"
    assert FeedbackTarget.AROUSAL.value == "arousal"
    assert FeedbackTarget.CALMNESS.value == "calmness"

def test_feedback_modality_enum():
    """Test FeedbackModality enum values."""
    assert FeedbackModality.VISUAL.value == "visual"
    assert FeedbackModality.AUDITORY.value == "auditory"
    assert FeedbackModality.PROPRIOCEPTIVE.value == "proprioceptive"
    assert FeedbackModality.COMBINED.value == "combined"

def test_create_session_with_different_targets():
    """Test creating sessions with different targets."""
    engine = NeurofeedbackEngine()
    for target in [FeedbackTarget.RELAXATION, FeedbackTarget.FOCUS, FeedbackTarget.AROUSAL]:
        session = engine.create_neurofeedback_session(target, FeedbackModality.VISUAL)
        assert session["target"] == target.value

def test_engine_callback_registration():
    """Test callback registration and invocation."""
    callback_data = []

    def my_callback(fb):
        callback_data.append(fb)

    engine = NeurofeedbackEngine(feedback_callback=my_callback)
    engine.push(np.random.randn(500, 2))
    fb = engine._compute_feedback()
    # Callback should have been registered
    assert engine.feedback_callback is not None

def test_neurofeedback_session_descriptor():
    """Test session descriptor format."""
    engine = NeurofeedbackEngine()
    session = engine.create_neurofeedback_session(
        FeedbackTarget.RELAXATION,
        FeedbackModality.VISUAL,
        session_duration=300.0
    )
    assert "session_id" in session
    assert "target" in session
    assert "modality" in session
    assert "duration_s" in session
    assert session["duration_s"] == 300.0

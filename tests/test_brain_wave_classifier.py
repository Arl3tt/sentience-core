from core.tools import classify_brainwave_bands, classify_cognitive_state, classify_multi_channel


def test_bandpowers_and_ratios(sample_signal):
    res = classify_brainwave_bands(sample_signal, fs=250.0)
    assert isinstance(res, dict)
    # check some expected keys
    assert "alpha_power" in res
    assert "alpha_power_ratio" in res


def test_cognitive_state_output(sample_signal):
    out = classify_cognitive_state(sample_signal, fs=250.0)
    assert "predicted_state" in out
    assert "state_scores" in out


def test_multi_channel_aggregate(sample_multichannel):
    out = classify_multi_channel(sample_multichannel, fs=250.0)
    assert "channels" in out and "aggregate" in out and "global_state" in out
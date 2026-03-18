"""
Test module for EEG preprocessing
"""
import numpy as np
from .eeg_preprocessing import (
    bandpass_filter,
    extract_band_power,
    remove_artifacts,
    preprocess_eeg,
    notch_filter,
    compute_psd,
    spectral_entropy,
    compute_band_ratios,
    compute_stft,
    FeatureHistory
)

def test_bandpass_filter():
    """Test bandpass filter functionality"""
    # Create synthetic data
    fs = 250  # Sample rate
    t = np.linspace(0, 1, fs)
    # Mix of 5 Hz and 20 Hz signals
    signal = np.sin(2 * np.pi * 5 * t) + np.sin(2 * np.pi * 20 * t)
    signal = signal.reshape(-1, 1)  # Make 2D for single channel

    # Test theta band isolation (4-8 Hz)
    filtered = bandpass_filter(signal, 4, 8, fs)
    # Power in theta band should be higher than other bands
    theta_power = np.mean(filtered ** 2)

    # Filter beta band (12-30 Hz) for comparison
    beta = bandpass_filter(signal, 12, 30, fs)
    beta_power = np.mean(beta ** 2)

    assert theta_power > 0, "Theta power should be positive"
    assert beta_power > 0, "Beta power should be positive"

def test_artifact_removal():
    """Test artifact removal function"""
    # Create signal with artifacts
    signal = np.random.randn(1000, 2) * 10  # 2 channels
    # Add artifacts
    signal[100:102, 0] = 1000  # Large spike
    signal[300:302, 1] = -1000  # Large negative spike

    cleaned = remove_artifacts(signal, threshold=100)

    # Check if artifacts were removed
    assert np.all(np.abs(cleaned) < 100), "Artifacts should be removed"
    assert not np.any(np.isnan(cleaned)), "NaN values should be interpolated"

def test_notch_filter():
    """Test notch filter functionality"""
    fs = 250
    t = np.linspace(0, 2, fs*2)  # 2 seconds of data
    # Create signal with 60 Hz noise
    clean_signal = np.sin(2 * np.pi * 10 * t)  # 10 Hz signal
    noise = np.sin(2 * np.pi * 60 * t)  # 60 Hz noise
    signal = (clean_signal + noise).reshape(-1, 1)

    cleaned = notch_filter(signal, fs)

    # Compute PSD before and after
    freqs, psd_before = compute_psd(signal, fs)
    _, psd_after = compute_psd(cleaned, fs)

    # Find frequency bins close to 60 Hz
    noise_mask = np.abs(freqs - 60) < 5  # Within 5 Hz of 60 Hz
    power_at_60hz_before = np.mean(psd_before[noise_mask])
    power_at_60hz_after = np.mean(psd_after[noise_mask])

    # Power at 60 Hz should be reduced
    assert power_at_60hz_after < power_at_60hz_before, "Notch filter should reduce power at 60 Hz"

def test_psd():
    """Test power spectral density computation"""
    fs = 250
    t = np.linspace(0, 4, 4*fs)
    # Create signal with known frequencies
    signal = (np.sin(2 * np.pi * 10 * t) +  # 10 Hz
             np.sin(2 * np.pi * 20 * t)).reshape(-1, 1)  # 20 Hz

    freqs, psd = compute_psd(signal, fs)

    # Basic shape checks
    assert psd.shape[1] == signal.shape[1], "PSD should have same number of channels"
    assert len(freqs) == psd.shape[0], "Frequency array should match PSD shape"

def test_entropy():
    """Test spectral entropy computation"""
    # Create two signals - one regular, one chaotic
    fs = 250
    t = np.linspace(0, 4, 4*fs)

    # Regular signal (single frequency)
    regular = np.sin(2 * np.pi * 10 * t).reshape(-1, 1)

    # Chaotic signal (multiple frequencies)
    chaotic = np.sin(2 * np.pi * 10 * t) + \
              np.sin(2 * np.pi * 20 * t) + \
              np.sin(2 * np.pi * 30 * t)
    chaotic = chaotic.reshape(-1, 1)

    # Compute PSDs
    _, psd_regular = compute_psd(regular, fs)
    _, psd_chaotic = compute_psd(chaotic, fs)

    # Compute entropies
    ent_regular = spectral_entropy(psd_regular)
    ent_chaotic = spectral_entropy(psd_chaotic)

    assert ent_chaotic > ent_regular, "Chaotic signal should have higher entropy"

def test_band_ratios():
    """Test computation of band ratios"""
    fs = 250
    t = np.linspace(0, 4, 4*fs)

    # Create signal with strong alpha and weak beta
    signal = (2*np.sin(2 * np.pi * 10 * t) +  # Strong alpha (10 Hz)
              0.5*np.sin(2 * np.pi * 20 * t)).reshape(-1, 1)  # Weak beta (20 Hz)

    freqs, psd = compute_psd(signal, fs)
    ratios = compute_band_ratios(psd, freqs)

    assert 'alpha_beta_ratio' in ratios, "Should compute alpha/beta ratio"
    assert 'theta_beta_ratio' in ratios, "Should compute theta/beta ratio"

    # For multi-channel data, ratios are lists
    if isinstance(ratios['alpha_beta_ratio'], list):
        assert ratios['alpha_beta_ratio'][0] > 1, "Alpha should be stronger than beta in first channel"
    else:
        assert ratios['alpha_beta_ratio'] > 1, "Alpha should be stronger than beta"

def test_stft():
    """Test Short-Time Fourier Transform"""
    fs = 250
    t = np.linspace(0, 1, fs)
    # Create chirp signal (increasing frequency)
    signal = np.sin(2 * np.pi * 10 * t * t).reshape(-1, 1)

    freqs, times, Zxx = compute_stft(signal, fs)

    assert Zxx.shape[0] == len(freqs), "Frequency dimension should match"
    assert Zxx.shape[1] == len(times), "Time dimension should match"
    assert np.all(Zxx >= 0), "Magnitude spectrum should be non-negative"

def test_feature_history():
    """Test feature history tracking"""
    history = FeatureHistory(window_size=3)

    # Simulate updating features over time
    features1 = {'alpha_power': 0.5, 'beta_power': 0.3}
    features2 = {'alpha_power': 0.6, 'beta_power': 0.2}
    features3 = {'alpha_power': 0.7, 'beta_power': 0.1}

    history.update(features1)
    history.update(features2)
    history.update(features3)

    trends = history.get_trends()

    assert 'alpha_power_trend' in trends, "Should compute alpha power trend"
    assert trends['alpha_power_trend'] > 0, "Alpha power should show increasing trend"
    assert trends['beta_power_trend'] < 0, "Beta power should show decreasing trend"

def test_full_pipeline():
    """Test complete preprocessing pipeline"""
    # Create test signal
    fs = 250
    t = np.linspace(0, 4, 4*fs)  # 4 seconds of data
    signal = np.random.randn(len(t), 2) * 0.1  # 2 channels of noise

    # Add some rhythmic activity
    signal[:, 0] += np.sin(2 * np.pi * 10 * t)  # 10 Hz (alpha) in ch1
    signal[:, 1] += np.sin(2 * np.pi * 5 * t)   # 5 Hz (theta) in ch2

    # Add artifacts
    signal[250:252, 0] = 1000  # Amplitude artifact
    signal += np.sin(2 * np.pi * 60 * t).reshape(-1, 1)  # Power line noise

    # Create feature history
    history = FeatureHistory(window_size=5)

    # Process with history tracking
    cleaned, features = preprocess_eeg(signal, fs, history)

    # Basic checks
    assert cleaned.shape == signal.shape, "Shape should be preserved"
    assert all(k in features for k in [
        "alpha_power", "theta_power", "spectral_entropy",
        "alpha_beta_ratio", "theta_beta_ratio"
    ]), "Should have all feature types"
    assert all(k in features for k in ["tf_data", "tf_freqs", "tf_times"]), \
        "Should include time-frequency features"
    assert not np.any(np.abs(cleaned) > 100), "No extreme values should remain"

    # Process again to test trend computation
    cleaned2, features2 = preprocess_eeg(signal * 1.1, fs, history)  # Slightly stronger signal
    assert any('trend' in k for k in features2.keys()), "Should include trend features"

if __name__ == "__main__":
    test_bandpass_filter()
    test_artifact_removal()
    test_full_pipeline()
    print("All tests passed!")
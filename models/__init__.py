"""
Models package for EEG processing and analysis
"""
from .eeg_preprocessing import (
    bandpass_filter,
    extract_band_power,
    remove_artifacts,
    preprocess_eeg,
    notch_filter,
    compute_psd,
    spectral_entropy,
    remove_artifacts_ica,
    normalize_signal,
    compute_band_ratios,
    compute_stft,
    FeatureHistory
)

__all__ = [
    'bandpass_filter',
    'extract_band_power',
    'remove_artifacts',
    'preprocess_eeg',
    'notch_filter',
    'compute_psd',
    'spectral_entropy',
    'remove_artifacts_ica',
    'normalize_signal',
    'compute_band_ratios',
    'compute_stft',
    'FeatureHistory'
]

# Note: Advanced BCI tools are available in core.tools:
# - brain_wave_classifier: EEG brain wave classification
# - motor_imagery_cnn: Motor imagery CNN classification
# - p300_speller: P300-based brain-computer interface
# - neurofeedback_loop: Real-time neurofeedback system
# - hybrid_bci: Multi-modal BCI combining paradigms
# - asd_attention_analysis: ASD attention pattern analysis

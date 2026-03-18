"""
EEG preprocessing pipeline for filtering and feature extraction
"""
import numpy as np
from pathlib import Path
from scipy.signal import (
    butter, sosfilt, iirnotch, filtfilt,
    welch, stft
)
from scipy.stats import entropy
from sklearn.decomposition import FastICA, PCA
from .embedding_model import compute_embedding
from collections import deque

# Band definitions
BANDS = {
    "delta": (1, 4),
    "theta": (4, 8),
    "alpha": (8, 12),
    "beta": (12, 30),
    "gamma": (30, 80)
}

def butter_bandpass(low: float, high: float, fs: float, order: int = 4):
    """Create a bandpass filter"""
    return butter(order, [low / (fs/2), high / (fs/2)], btype='band', output='sos')

def bandpass_filter(data: np.ndarray, low: float, high: float, fs: float) -> np.ndarray:
    """Apply bandpass filter to EEG data"""
    sos = butter_bandpass(low, high, fs)
    # Ensure result is a numpy array (sosfilt may return array-like)
    return np.asarray(sosfilt(sos, data))

def extract_band_power(eeg: np.ndarray, fs: float) -> dict:
    """Extract power in each frequency band"""
    features = {}
    for band, (low, high) in BANDS.items():
        filtered = bandpass_filter(eeg, low, high, fs)
        power = np.mean(filtered ** 2, axis=0)
        features[f"{band}_power"] = power.tolist()
    return features

# Additional utility functions for preprocessing
def remove_artifacts(eeg: np.ndarray, threshold: float = 100) -> np.ndarray:
    """Simple artifact removal by amplitude thresholding"""
    clean = np.copy(eeg)
    mask = np.abs(clean) > threshold
    clean[mask] = np.nan
    # Interpolate NaN values
    for ch in range(clean.shape[1]):
        nan_mask = np.isnan(clean[:, ch])
        if np.any(nan_mask):
            clean[nan_mask, ch] = np.interp(
                np.flatnonzero(nan_mask),
                np.flatnonzero(~nan_mask),
                clean[~nan_mask, ch]
            )
    return clean

def notch_filter(data: np.ndarray, fs: float, freq: float = 60.0, quality: float = 30.0) -> np.ndarray:
    """Remove power line noise using notch filter"""
    b, a = iirnotch(freq / (fs / 2), quality)
    return filtfilt(b, a, data, axis=0)

def remove_artifacts_ica(signals: np.ndarray, n_components: int | None = None, rel_eig_thresh: float = 1e-6) -> np.ndarray:
    """Remove artifacts using ICA with PCA pre-whitening and degeneracy checks.

    - Centers and replaces NaNs.
    - Runs PCA (whitening) and inspects eigenvalues.
    - Reduces the number of ICA components if a subset have negligible variance.
    - If data is degenerate (too few valid components) ICA is skipped and the
      (whitened) signal is returned to avoid numerical failures.

    Args:
        signals: EEG data of shape (samples, channels)
        n_components: Desired number of ICA components. Defaults to number of channels.
        rel_eig_thresh: Relative threshold for selecting PCA components (fraction of max eigenvalue).

    Returns:
        Reconstructed signal of shape (samples, channels). If ICA is applied, returns
        the ICA-cleaned and inverse-transformed signal back in sensor space. If skipped,
        returns the input signals with NaNs replaced and centered.
    """
    # Defensive copy and NaN/inf cleanup
    signals = np.nan_to_num(np.asarray(signals, dtype=float), nan=0.0, posinf=0.0, neginf=0.0)

    n_samples, n_channels = signals.shape
    if n_samples < 2 or n_channels < 2:
        return signals

    # Center the data
    X = signals - np.mean(signals, axis=0)

    # PCA whitening
    pca_n = min(n_samples, n_channels)
    pca = PCA(n_components=pca_n, whiten=True)
    try:
        X_pca = pca.fit_transform(X)
    except Exception:
        # If PCA fails for any reason, return original cleaned signals
        return signals

    eigs = pca.explained_variance_
    if eigs.size == 0:
        return signals

    max_eig = np.max(eigs)
    # Select components with eigenvalue > rel_eig_thresh * max_eig
    keep_mask = eigs > (max_eig * rel_eig_thresh)
    keep = int(np.sum(keep_mask))

    # Decide number of ICA components
    if n_components is None:
        desired_ica_components = keep
    else:
        desired_ica_components = max(1, min(keep, int(n_components)))

    # If not enough components to run ICA robustly, skip ICA and return centered signals
    if keep < 2 or desired_ica_components < 2:
        # inverse-transform PCA whitened data back to sensor space for continuity
        try:
            X_recon = pca.inverse_transform(X_pca)
            return X_recon + np.mean(signals, axis=0)
        except Exception:
            return signals

    # Run ICA on the retained PCA components
    try:
        # Use only the retained PCA components for ICA
        X_pca_reduced = X_pca[:, :desired_ica_components]
        ica = FastICA(n_components=desired_ica_components, whiten=False, random_state=0)
        S = ica.fit_transform(X_pca_reduced)

        # Reconstruct PCA-space representation from ICA inverse (pad remaining components with zeros)
        try:
            X_pca_recon_reduced = ica.inverse_transform(S)
        except Exception:
            # If inverse_transform not available or fails, fall back to using transformed sources
            X_pca_recon_reduced = X_pca_reduced

        # Build full PCA-space reconstruction (pad zeros for components we didn't touch)
        X_pca_recon = np.zeros_like(X_pca)
        X_pca_recon[:, :desired_ica_components] = X_pca_recon_reduced

        # Inverse PCA to sensor space
        X_recon = pca.inverse_transform(X_pca_recon)
        # Add back mean
        X_recon = X_recon + np.mean(signals, axis=0)
        return X_recon
    except Exception:
        # On any ICA numerical issue, return PCA-reconstructed signal
        try:
            X_recon = pca.inverse_transform(X_pca)
            return X_recon + np.mean(signals, axis=0)
        except Exception:
            return signals

def compute_psd(signals: np.ndarray, fs: float) -> tuple[np.ndarray, np.ndarray]:
    """Compute power spectral density using Welch's method"""
    nperseg = min(256, signals.shape[0])  # Adjust segment size based on signal length
    if signals.ndim == 1:
        signals = signals.reshape(-1, 1)
    
    freqs = []
    psd_list = []
    
    for ch in range(signals.shape[1]):
        f, p = welch(signals[:, ch], fs, nperseg=nperseg)
        freqs.append(f)
        psd_list.append(p)
    
    # All frequencies should be the same for each channel
    freqs = freqs[0]
    psd = np.stack(psd_list, axis=-1)
    return freqs, psd

def spectral_entropy(psd: np.ndarray) -> np.ndarray:
    """Compute spectral entropy from PSD
    
    Higher values indicate more complex/chaotic signals
    Lower values suggest more regular/predictable patterns
    """
    # Defensive handling: replace invalid values and avoid zero columns
    eps = 1e-12
    # Convert to array and mask invalid values
    psd_arr = np.asarray(psd, dtype=float)
    psd_arr = np.nan_to_num(psd_arr, nan=0.0, posinf=0.0, neginf=0.0)

    # Add tiny epsilon to all entries to avoid all-zero columns
    psd_arr += eps

    # Normalize PSD to get probability distributions per channel
    col_sums = np.sum(psd_arr, axis=0)
    # Prevent division by zero
    col_sums = np.where(col_sums <= 0, eps, col_sums)
    psd_norm = psd_arr / col_sums

    entr = entropy(psd_norm, axis=0)
    # Ensure ndarray return type
    return np.atleast_1d(np.array(entr, dtype=float))

def normalize_signal(data: np.ndarray) -> np.ndarray:
    """Z-score normalization of EEG signal"""
    mean = np.mean(data, axis=0)
    std = np.std(data, axis=0)
    # Avoid division by zero by setting std to 1 if it's zero
    std[std == 0] = 1
    return (data - mean) / std

def compute_band_ratios(psd: np.ndarray, freqs: np.ndarray) -> dict:
    """Compute clinically relevant band ratios
    
    Returns:
        dict: Contains ratios like alpha/beta, theta/beta
        These ratios are used in ADHD research and neurofeedback
    """
    def get_band_power(low: float, high: float) -> np.ndarray:
        mask = (freqs >= low) & (freqs <= high)
        if psd.ndim == 1:
            band_psd = psd[mask]
        else:
            band_psd = psd[mask]
            if band_psd.ndim == 1:
                band_psd = band_psd.reshape(-1, 1)
        return np.mean(band_psd, axis=0)
    
    # Add small constant to avoid division by zero
    alpha = get_band_power(8, 12) + 1e-10
    beta = get_band_power(12, 30) + 1e-10
    theta = get_band_power(4, 8) + 1e-10
    
    # Convert to float for single channel or list for multiple channels
    if isinstance(alpha, np.ndarray):
        ratios = {
            'alpha_beta_ratio': (alpha / beta).tolist(),
            'theta_beta_ratio': (theta / beta).tolist(),
            'theta_alpha_ratio': (theta / alpha).tolist()
        }
    else:
        ratios = {
            'alpha_beta_ratio': float(alpha / beta),
            'theta_beta_ratio': float(theta / beta),
            'theta_alpha_ratio': float(theta / alpha)
        }
    return ratios

def compute_stft(signal: np.ndarray, fs: float, window: int | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute Short-Time Fourier Transform
    
    Args:
        signal: EEG signal
        fs: Sampling frequency
        window: Window size for STFT. If None, will be automatically calculated.
        
    Returns:
        tuple: (frequencies, times, Zxx)
        - frequencies: Frequency points
        - times: Time points
        - Zxx: STFT of the signal (complex values)
    """
    if window is None:
        # Use 1/4 of signal length or 256, whichever is smaller
        window = min(256, signal.shape[0] // 4)
        # Ensure window is even
        window = window if window % 2 == 0 else window - 1
        
    # Ensure window is not larger than signal
    window = min(window, signal.shape[0])
    
    if signal.ndim == 1:
        signal = signal.reshape(-1, 1)
    
    freqs_list = []
    times_list = []
    Zxx_list = []
    
    # Process each channel
    for ch in range(signal.shape[1]):
        f, t, Z = stft(signal[:, ch], fs=fs, nperseg=window)
        freqs_list.append(f)
        times_list.append(t)
        Zxx_list.append(np.abs(Z))
    
    # All frequencies and times should be the same for each channel
    freqs = freqs_list[0]
    times = times_list[0]
    # Stack spectrograms along the last axis
    Zxx = np.stack(Zxx_list, axis=-1)
    
    return freqs, times, Zxx

class FeatureHistory:
    """Maintains a rolling window of brain state features"""
    
    def __init__(self, window_size: int = 10):
        """Initialize feature history
        
        Args:
            window_size: Number of time points to keep in history
        """
        self.window_size = window_size
        self.history = {}
        
    def update(self, features: dict) -> None:
        """Add new features to history
        
        Args:
            features: Dictionary of new features to add
        """
        for name, value in features.items():
            if name not in self.history:
                self.history[name] = deque(maxlen=self.window_size)
            # Skip complex features like PSD and time-frequency data
            if isinstance(value, (float, int)) or (
                isinstance(value, (list, np.ndarray)) and 
                np.array(value).ndim == 1
            ):
                self.history[name].append(value)
    
    def get_trends(self) -> dict:
        """Compute trends in feature history
        
        Returns:
            dict: Contains trend metrics for each feature
        """
        trends = {}
        for name, values in self.history.items():
            if len(values) >= 2:  # Need at least 2 points for trend
                try:
                    values_array = np.array(values)
                    if values_array.ndim == 1:
                        x = np.arange(len(values_array))
                        slope = np.polyfit(x, values_array, deg=1)[0]
                        trends[f"{name}_trend"] = float(slope)
                    elif values_array.ndim == 2:
                        # Compute trend for each channel
                        x = np.arange(values_array.shape[0])
                        slopes = [np.polyfit(x, values_array[:, i], deg=1)[0] 
                                for i in range(values_array.shape[1])]
                        trends[f"{name}_trend"] = [float(s) for s in slopes]
                except (ValueError, np.linalg.LinAlgError):
                    # Skip features that can't be fit
                    continue
        return trends

def preprocess_eeg(eeg: np.ndarray, fs: float, feature_history: FeatureHistory | None = None) -> tuple[np.ndarray, dict]:
    """Full preprocessing pipeline
    
    Args:
        eeg: Raw EEG signal
        fs: Sampling frequency
        feature_history: Optional FeatureHistory object for temporal tracking
        
    Returns:
        tuple: (preprocessed_eeg, features)
        - preprocessed_eeg: Cleaned and filtered EEG signal
        - features: Dictionary containing extracted features
    """
    # 1. Remove large artifacts
    clean = remove_artifacts(eeg)
    
    # 2. Apply notch filter (remove power line noise)
    clean = notch_filter(clean, fs)
    
    # 3. Normalize signal
    clean = normalize_signal(clean)
    
    # 4. Apply bandpass filter
    filtered = bandpass_filter(clean, 1, 80, fs)
    
    # 5. Try to apply ICA for advanced artifact removal
    try:
        clean_ica = remove_artifacts_ica(filtered)
    except (ValueError, np.linalg.LinAlgError):
        # If ICA fails, use filtered data directly
        clean_ica = filtered
    
    # Extract features
    features = {}
    
    # Band power features
    band_power = extract_band_power(clean_ica, fs)
    features.update(band_power)
    
    # PSD features
    freqs, psd = compute_psd(clean_ica, fs)
    features['psd'] = psd.tolist()
    features['psd_freqs'] = freqs.tolist()
    
    # Complexity measures
    features['spectral_entropy'] = spectral_entropy(psd).tolist()
    
    # Band ratios (ADHD biomarkers)
    ratios = compute_band_ratios(psd, freqs)
    features.update(ratios)
    
    # Time-frequency analysis
    tf_freqs, tf_times, tf_data = compute_stft(clean_ica, fs)
    features['tf_data'] = tf_data.tolist()
    features['tf_freqs'] = tf_freqs.tolist()
    features['tf_times'] = tf_times.tolist()
    
    # Update feature history if provided
    if feature_history is not None:
        feature_history.update(features)
        # Add temporal trends to features
        features.update(feature_history.get_trends())

    # Compute a compact embedding for this session and save a copy to outputs
    try:
        out_dir = Path("data") / "outputs"
        out_dir.mkdir(parents=True, exist_ok=True)
        emb = compute_embedding(features, dim=16, save_path=str(out_dir / "embedding_vector.npy"))
        # attach embedding to features for callers
        features['embedding'] = emb.tolist()
    except Exception:
        # best-effort: do not fail the preprocessing pipeline on embedding errors
        features['embedding'] = []

    return clean_ica, features
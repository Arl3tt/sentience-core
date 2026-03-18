import numpy as np
from pathlib import Path
from .eeg_preprocessing import preprocess_eeg, FeatureHistory
import matplotlib.pyplot as plt

def load_simulated_data():
    """Load the simulated EEG data"""
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(project_root, 'data', 'simulated', 'sim_eeg_sample.npz')
    data = np.load(data_path)
    
    # Data is shaped (samples, channels, timepoints)
    # Need to reshape to (timepoints, channels)
    X = data['X']
    eeg = X[0]  # Take first sample
    eeg = np.transpose(eeg)  # Transpose to (timepoints, channels)
    return eeg

def visualize_processing_stages(raw_eeg, preprocessed_eeg, features):
    """Visualize the raw data, preprocessed data, and extracted features"""
    fig, axes = plt.subplots(3, 1, figsize=(15, 10))
    
    # Plot raw EEG
    axes[0].plot(raw_eeg[:1000, 0])  # First 1000 samples of first channel
    axes[0].set_title('Raw EEG')
    axes[0].set_xlabel('Samples')
    axes[0].set_ylabel('Amplitude')
    
    # Plot preprocessed EEG
    axes[1].plot(preprocessed_eeg[:1000, 0])
    axes[1].set_title('Preprocessed EEG')
    axes[1].set_xlabel('Samples')
    axes[1].set_ylabel('Amplitude')
    
    # Plot band powers
    band_names = ['delta', 'theta', 'alpha', 'beta', 'gamma']
    band_powers = [features[f'{band}_power'][0] for band in band_names]
    axes[2].bar(band_names, band_powers)
    axes[2].set_title('Band Power Features')
    axes[2].set_ylabel('Power')
    
    plt.tight_layout()
    plt.show()

def main():
    # Load simulated data
    print("Loading simulated EEG data...")
    eeg_data = load_simulated_data()
    print(f"Loaded EEG data shape: {eeg_data.shape}")
    
    # Initialize feature history tracker
    feature_history = FeatureHistory(window_size=10)
    
    # Process the EEG data
    print("\nPreprocessing EEG data and extracting features...")
    preprocessed_data, features = preprocess_eeg(eeg_data, fs=250, feature_history=feature_history)
    
    # Print feature summary
    print("\nExtracted features:")
    for feature_name, value in features.items():
        if isinstance(value, list):
            if len(value) > 0 and isinstance(value[0], (list, np.ndarray)):
                print(f"{feature_name}: shape={np.array(value).shape}")
            else:
                print(f"{feature_name}: length={len(value)}, mean={np.mean(value):.3f}")
        else:
            print(f"{feature_name}: {value}")
    
    # Visualize results
    print("\nGenerating visualization...")
    visualize_processing_stages(eeg_data, preprocessed_data, features)

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
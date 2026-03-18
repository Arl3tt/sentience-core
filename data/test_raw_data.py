"""
Test loading and preprocessing real OpenBCI data
"""
import numpy as np
from pathlib import Path
from openbci_reader import read_openbci_txt
from models.eeg_preprocessing import preprocess_eeg, FeatureHistory
from memory.memory_controller import save_neural_session
import matplotlib.pyplot as plt

def visualize_data(raw_data, preprocessed_data, features):
    """Visualize the raw and preprocessed data with features"""
    out_dir = Path('data') / 'outputs'
    out_dir.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(15, 12))

    # Plot 1: Raw EEG signals
    ax1 = plt.subplot(311)
    for ch in range(raw_data.shape[1]):
        plt.plot(raw_data[:1000, ch], label=f'Ch{ch+1}')
    plt.title('Raw EEG')
    plt.legend()
    plt.xlabel('Samples')
    plt.ylabel('Amplitude')

    # Plot 2: Preprocessed EEG signals
    ax2 = plt.subplot(312)
    for ch in range(preprocessed_data.shape[1]):
        plt.plot(preprocessed_data[:1000, ch], label=f'Ch{ch+1}')
    plt.title('Preprocessed EEG')
    plt.legend()
    plt.xlabel('Samples')
    plt.ylabel('Amplitude')

    # Plot 3: Power Spectral Density
    ax3 = plt.subplot(313)
    freqs = np.array(features['psd_freqs'])
    psd = np.array(features['psd'])
    for ch in range(psd.shape[1]):
        plt.semilogy(freqs, psd[:, ch], label=f'Ch{ch+1}')
    plt.title('Power Spectral Density')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Power')
    plt.legend()

    plt.tight_layout()
    fig_path = out_dir / 'raw_and_preprocessed.png'
    plt.savefig(fig_path)
    plt.close(fig)

    # Plot band powers
    plt.figure(figsize=(12, 6))
    bands = ['delta', 'theta', 'alpha', 'beta', 'gamma']
    band_powers = np.array([features[f'{band}_power'] for band in bands])

    channels = range(band_powers.shape[1])
    bar_width = 0.15

    for i, band in enumerate(bands):
        plt.bar([x + i*bar_width for x in channels], 
                band_powers[i], 
                bar_width,
                label=band.capitalize())

    plt.title('Band Powers by Channel')
    plt.xlabel('Channel')
    plt.ylabel('Power')
    plt.legend()
    plt.xticks([x + bar_width*2 for x in channels], [f'Ch{i+1}' for i in channels])
    band_path = out_dir / 'band_powers.png'
    plt.savefig(band_path)
    plt.close()

def main():
    # Load the OpenBCI data
    print("Loading OpenBCI meditation data...")
    signals, sample_rate, channel_names = read_openbci_txt('data/raw/openbci_meditation.txt')
    data = {
        'signals': signals,
        'sample_rate': sample_rate,
        'channel_names': channel_names
    }
    print(f"Loaded data shape: {signals.shape}")
    print(f"Channel names: {channel_names}")
    print(f"Sample rate: {sample_rate} Hz")
    
    # Initialize feature history tracker
    feature_history = FeatureHistory(window_size=10)
    
    # Process the data
    print("\nPreprocessing data...")
    preprocessed_data, features = preprocess_eeg(
        data['signals'], 
        fs=data['sample_rate'],
        feature_history=feature_history
    )
    
    # Print feature summary
    print("\nExtracted features:")
    for feature_name, value in features.items():
        if isinstance(value, list):
            arr = np.array(value)
            if arr.ndim == 1:
                print(f"{feature_name}: length={len(value)}, mean={np.mean(value):.3f}")
            else:
                print(f"{feature_name}: shape={arr.shape}")
        else:
            print(f"{feature_name}: {value}")
            
    # Visualize the results
    print("\nGenerating visualizations...")
    visualize_data(data['signals'], preprocessed_data, features)

    # --- persist a neural session (simple embedding + features) ---
    try:
        # Build a tiny embedding from mean band powers + mean spectral entropy
        bands = ['delta', 'theta', 'alpha', 'beta', 'gamma']
        band_means = [np.mean(features.get(f"{b}_power", [0])) for b in bands]
        spec_ent = np.mean(features.get('spectral_entropy', [0]))
        embedding = np.concatenate([np.array(band_means, dtype=float), np.array([spec_ent], dtype=float)])

        session_meta = {
            'source': 'data/raw/openbci_meditation.txt',
            'num_samples': int(signals.shape[0]),
            'sample_rate': int(sample_rate),
            'channel_count': int(signals.shape[1])
        }
        res = save_neural_session(session_meta, features, embedding)
        print("Saved neural session:", res.get('session_id'))
    except Exception as e:
        print("Failed to save neural session:", e)

if __name__ == "__main__":
    main()
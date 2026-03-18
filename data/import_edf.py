import mne
from pathlib import Path

def load_edf(file_path: str):
    raw = mne.io.read_raw_edf(file_path, preload=True)
    data, times = raw.get_data(return_times=True)

    return {
        "timestamps": times,
        "signals": data.T,  # (samples x channels)
        "channel_names": raw.ch_names,
        "sample_rate": raw.info["sfreq"]
    }

if __name__ == "__main__":
    eeg = load_edf("data/raw/eeg_sample.edf")
    print(f"Channels: {len(eeg['channel_names'])}, samples: {len(eeg['signals'])}")
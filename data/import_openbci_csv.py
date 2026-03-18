import pandas as pd
import numpy as np
from pathlib import Path

def load_openbci_csv(file_path: str):
    df = pd.read_csv(file_path, skiprows=5)  # OpenBCI has metadata rows
    eeg_channels = [col for col in df.columns if "EXG" in col or "EEG" in col]

    data = df[eeg_channels].values
    timestamps = df["Timestamp"].values if "Timestamp" in df.columns else np.arange(len(data))

    return {
        "timestamps": timestamps,
        "signals": data,
        "channel_names": eeg_channels,
        "sample_rate": 250  # default OpenBCI
    }

if __name__ == "__main__":
    file = "data/raw/openbci_sample.csv"
    eeg = load_openbci_csv(file)
    print(f"Loaded {len(eeg['signals'])} samples from {file}")
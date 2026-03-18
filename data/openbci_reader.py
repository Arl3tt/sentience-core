import pandas as pd
import numpy as np

def read_openbci_txt(file_path):
    """
    Read OpenBCI GUI generated text file and return EEG data as numpy array.
    
    Args:
        file_path (str): Path to the OpenBCI text file
        
    Returns:
        tuple: (data, sample_rate, channels)
            - data: numpy array of shape (n_samples, n_channels) containing EEG data
            - sample_rate: sampling rate in Hz
            - channels: list of channel names
    """
    # Read metadata from header
    with open(file_path, 'r') as f:
        header = [f.readline() for _ in range(4)]
        
    # Extract sampling rate
    sample_rate = int(header[2].split('=')[1].split('Hz')[0].strip())
    
    # Read data using pandas
    data = pd.read_csv(file_path, skiprows=4)
    
    # Get EEG channel columns (first 8 columns after Sample Index)
    eeg_cols = [col for col in data.columns if 'EXG Channel' in col]
    
    # Extract EEG data
    eeg_data = data[eeg_cols].values
    
    # Verify dimensions
    n_samples, n_channels = eeg_data.shape
    assert n_channels == 8, f"Expected 8 EEG channels but found {n_channels}"
    
    return eeg_data, sample_rate, eeg_cols
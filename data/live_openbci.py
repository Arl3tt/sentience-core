from pyOpenBCI import OpenBCICyton
import numpy as np

def handle_sample(sample):
    eeg = np.array(sample.channels_data)
    print("EEG sample:", eeg)

def stream():
    board = OpenBCICyton(port="COM3")  # Windows default
    board.start_stream(handle_sample)

if __name__ == "__main__":
    stream()
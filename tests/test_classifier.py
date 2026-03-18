"""Test script for neural session persistence with classifier."""
import os
import numpy as np
import json
from memory.memory_controller import save_neural_session

# Create some sample session data
meta = {"session_id": "test_session_" + str(int(os.urandom(4).hex(), 16)),}

features = {"delta_power": [0.1, 0.2, 0.3],
    "theta_power": [0.2, 0.3, 0.4],
    "alpha_power": [0.3, 0.4, 0.5],
    "beta_power": [0.4, 0.5, 0.6],
    "gamma_power": [0.5, 0.6, 0.7],
    "spectral_entropy": [0.8, 0.9, 1.0],
    "alpha_beta_ratio": [0.75],
    "theta_beta_ratio": [0.5],
    "theta_alpha_ratio": [0.67]}

embedding = np.random.randn(32)  # example embedding

# Save session
result = save_neural_session(meta, features, embedding)
print("Saved session:", result)

# Read back features to check predictions
with open(result['features_path'], 'r', encoding='utf-8') as f:
    saved = json.load(f)
    print("\nSaved predictions:", saved.get('predicted_tags'))

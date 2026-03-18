"""Debug classifier prediction issues."""
import os
from models.neuro_classifier import predict_tags

# Sample features
features = {
    "delta_power": [0.1, 0.2, 0.3],
    "theta_power": [0.2, 0.3, 0.4],
    "alpha_power": [0.3, 0.4, 0.5],
    "beta_power": [0.4, 0.5, 0.6],
    "gamma_power": [0.5, 0.6, 0.7],
    "spectral_entropy": [0.8, 0.9, 1.0]
}

print("Looking for classifier in:")
paths = [
    os.path.join('memory', 'neural_state', 'neuro_classifier.joblib'),
    os.path.join('models', 'neuro_classifier.joblib')
]
for p in paths:
    print(f"- {os.path.abspath(p)}: {os.path.exists(p)}")

print("\nTrying prediction...")
tags = predict_tags(features)
print("Predicted tags:", tags)
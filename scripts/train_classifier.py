"""Simple script to train neuro state classifier.

Usage:
  python scripts/train_classifier.py --state-dir memory/neural_state
"""
import os
import argparse
import os
from models.neuro_classifier import train_classifier


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--state-dir', default='memory/neural_state')
    args = p.parse_args()

    # Train classifier
    out_path = os.path.join('models', 'neuro_classifier.joblib')
    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    train_classifier(args.state_dir, out_path)
    print(f"Trained classifier saved to {out_path}")

    # Also copy to memory module for accessibility
    memory_models = os.path.join('memory', 'neural_state', 'neuro_classifier.joblib')
    os.makedirs(os.path.dirname(memory_models) or '.', exist_ok=True)
    import shutil
    shutil.copy2(out_path, memory_models)
    print(f"Classifier copied to {memory_models}")


if __name__ == '__main__':
    main()
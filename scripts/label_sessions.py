"""Quick utility to label neural state sessions for classifier training.

Usage:
  python scripts/label_sessions.py --state-dir memory/neural_state

This will prompt for labels for any unlabeled session data. Labels can be:
focus, fatigue, stress, flow, drowsy, relaxed
"""
import os
import json
import argparse
from pathlib import Path


VALID_LABELS = ['focus', 'fatigue', 'stress', 'flow', 'drowsy', 'relaxed']


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--state-dir', default='memory/neural_state')
    p.add_argument('--yes', '-y', action='store_true', help='Skip confirmation')
    args = p.parse_args()

    state_dir = Path(args.state_dir)
    if not state_dir.exists():
        print(f"State directory {state_dir} not found")
        return 1

    # Find all feature files
    feature_files = []
    for f in state_dir.glob('*.features.json'):
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
                # Skip if already labeled
                if data.get('label') or data.get('tags'):
                    continue
                feature_files.append(f)
        except Exception as e:
            print(f"Error reading {f}: {e}")
            continue

    if not feature_files:
        print("No unlabeled feature files found")
        return 0

    print(f"Found {len(feature_files)} unlabeled files")
    if not args.yes:
        resp = input("Continue with labeling? [y/N] ")
        if not resp.lower().startswith('y'):
            return 0

    print("\nValid labels:", ', '.join(VALID_LABELS))
    print("Enter 'skip' to skip a file, 'quit' to stop\n")

    for f in feature_files:
        print(f"\nFile: {f.name}")
        while True:
            label = input("Enter label: ").strip().lower()
            if label == 'quit':
                return 0
            if label == 'skip':
                break
            if label in VALID_LABELS:
                try:
                    with open(f, 'r', encoding='utf-8') as fp:
                        data = json.load(fp)
                    data['label'] = label
                    with open(f, 'w', encoding='utf-8') as fp:
                        json.dump(data, fp, indent=2)
                    print(f"Labeled as '{label}'")
                    break
                except Exception as e:
                    print(f"Error saving label: {e}")
                    break
            else:
                print(f"Invalid label. Must be one of: {', '.join(VALID_LABELS)}")

    print("\nDone!")
    return 0


if __name__ == '__main__':
    exit(main())
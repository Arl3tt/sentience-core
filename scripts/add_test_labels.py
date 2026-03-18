"""Quick script to add test labels to feature files."""
import os
import json
import codecs

LABELS = ['focus', 'fatigue', 'stress', 'flow', 'drowsy', 'relaxed']
STATE_DIR = 'memory/neural_state'

def main():
    i = 0
    for fname in os.listdir(STATE_DIR):
        if not fname.endswith('.features.json'):
            continue
            
        path = os.path.join(STATE_DIR, fname)
        try:
            with codecs.open(path, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading {fname}: {e}")
            continue
            
        if not isinstance(data, dict):
            print(f"Warning: {fname} contains non-dict data")
            continue
            
        data['label'] = LABELS[i % len(LABELS)]
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f"Labeled {fname} as {data['label']}")
            i += 1
        except Exception as e:
            print(f"Error writing {fname}: {e}")
            
    print(f"\nLabeled {i} files")

if __name__ == '__main__':
    main()
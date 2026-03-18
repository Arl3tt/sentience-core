"""
Extended memory controller for handling EEG data with hybrid embeddings
"""
import numpy as np
from typing import Dict, List, Any, Optional
from memory.memory_controller import store_memory, semantic_search

class EEGMemoryController:
    def __init__(self):
        pass

    def store_eeg_record(self, record: Dict[str, Any], source: str = "OpenBCI"):
        """Store EEG record with both text summary and numeric embedding"""
        signals = record["signals"]
        text = f"EEG record from {source}, {len(signals)} samples, channels={record['channel_names']}"

        # Generate temporal embedding: mean / variance per channel
        features = np.hstack([signals.mean(axis=0), signals.std(axis=0)])

        # Store in memory system
        store_memory(
            text=text,
            meta={
                "type": "eeg",
                "source": source,
                "sample_rate": record["sample_rate"],
                "num_channels": len(record["channel_names"]),
                "num_samples": len(signals),
                "features": features.tolist()  # numeric embedding
            }
        )

    def search_eeg_records(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for EEG records using text query"""
        results = semantic_search(query, top_k=top_k)
        return [r for r in results if r.get("meta", {}).get("type") == "eeg"]

    def similarity_search(self, features: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Find similar EEG records using feature vector similarity"""
        query = f"Find EEG records with similar features to: {features}"
        results = semantic_search(query, top_k=top_k)
        return [r for r in results if r.get("meta", {}).get("type") == "eeg"]

# Example usage
if __name__ == "__main__":
    from data.import_openbci_csv import load_openbci_csv

    mc = EEGMemoryController()

    # Load and store example
    eeg = load_openbci_csv("data/raw/openbci_sample.csv")
    mc.store_eeg_record(eeg, source="OpenBCI-Test")

    # Search examples
    print("\nText search:")
    results = mc.search_eeg_records("OpenBCI recordings with high sample rate")
    for r in results:
        print(f"- {r['text']}")
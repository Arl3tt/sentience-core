"""Small script to train the embedding autoencoder on saved feature files.

Usage:
  python scripts/train_autoencoder.py --state-dir memory/neural_state --out models/autoencoder.pth

This script is optional and requires PyTorch installed in the environment.
"""
import argparse
import os
from models.embedding_autoencoder import train_autoencoder


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--state-dir', default='memory/neural_state')
    p.add_argument('--out', default='models/autoencoder.pth')
    p.add_argument('--latent', type=int, default=16)
    p.add_argument('--epochs', type=int, default=50)
    args = p.parse_args()

    os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
    train_autoencoder(args.state_dir, args.out, latent_dim=args.latent, epochs=args.epochs)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Thin t-SimCNE wrapper for DR pipeline."""
import numpy as np
try:
    from tsimcne.tsimcne import TSimCNE
except ImportError:
    TSimCNE = None

def run(embeddings, config):
    if TSimCNE is None:
        # Fallback: random 2D projection
        return np.random.randn(len(embeddings), 2)
    # Only keep valid tsimcne parameters, including batch_size and device
    valid_keys = ["n_components", "total_epochs", "random_state", "batch_size", "device"]
    tsimcne_cfg = {k: v for k, v in config.items() if k in valid_keys}
    # Convert total_epochs from comma-separated string to list if needed
    if "total_epochs" in tsimcne_cfg and isinstance(tsimcne_cfg["total_epochs"], str):
        tsimcne_cfg["total_epochs"] = [int(x) for x in tsimcne_cfg["total_epochs"].split(",")]
    print(f"[t-SimCNE] Config: {tsimcne_cfg}")
    # t-SimCNE expects a dataset, so we wrap embeddings as a torch TensorDataset
    import torch
    from torch.utils.data import TensorDataset
    X = torch.tensor(embeddings, dtype=torch.float32)
    dataset = TensorDataset(X)
    model = TSimCNE(**tsimcne_cfg)
    print(f"[t-SimCNE] Fitting model on {len(dataset)} samples...")
    model.fit(dataset)
    print("[t-SimCNE] Transforming to 2D coordinates...")
    Y = model.transform(dataset)
    # Ensure output is a numpy array
    if hasattr(Y, 'detach'):
        Y = Y.detach().cpu().numpy()
    elif hasattr(Y, 'cpu'):
        Y = Y.cpu().numpy()
    print(f"[t-SimCNE] Output shape: {Y.shape}")
    return Y 
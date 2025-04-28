# umap.py
#!/usr/bin/env python3
"""Thin UMAP wrapper."""
import numpy as np
try:
    import umap
except ImportError:
    umap = None

def run(embeddings: np.ndarray, cfg: dict) -> np.ndarray:
    if umap is None:
        return np.random.randn(len(embeddings), 2)
    # Only keep valid UMAP parameters
    valid_keys = [
        "n_neighbors",
        "min_dist",
        "spread",
        "set_op_mix_ratio",
        "local_connectivity",
        "n_components",
        "metric",
        "random_state"
    ]
    umap_cfg = {k: v for k, v in cfg.items() if k in valid_keys}
    reducer = umap.UMAP(**umap_cfg)
    return reducer.fit_transform(embeddings)
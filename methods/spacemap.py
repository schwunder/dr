#!/usr/bin/env python3
"""Thin SpaceMAP wrapper for DR pipeline."""
import numpy as np
try:
    from spacemap._spacemap import SpaceMAP
except ImportError:
    SpaceMAP = None

def run(embeddings: np.ndarray, cfg: dict) -> np.ndarray:
    if SpaceMAP is None:
        return np.random.randn(len(embeddings), 2)
    # Only keep valid SpaceMAP parameters
    valid_keys = [
        "n_components",
        "n_near_field",
        "n_middle_field",
        "d_local",
        "d_global",
        "eta",
        "n_epochs",
        "init",
        "metric",
        "verbose",
        "plot_results",
        "num_plots"
    ]
    spacemap_cfg = {k: v for k, v in cfg.items() if k in valid_keys}
    reducer = SpaceMAP(**spacemap_cfg)
    return reducer.fit_transform(embeddings) 
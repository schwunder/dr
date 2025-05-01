# PaCMAP integration for DR pipeline
# This file provides a run() function to interface with the pipeline.
# It expects embeddings (numpy array) and config (dict) as input.

import pacmap
import numpy as np
from sklearn.decomposition import PCA

def run(embeddings, config):
    """
    Run PaCMAP dimensionality reduction with optional PCA preprocessing.
    Args:
        embeddings (np.ndarray): Input data, shape (n_samples, n_features)
        config (dict): Configuration parameters matching PARAM_COLS["pacmap"]
    Returns:
        np.ndarray: 2D projection, shape (n_samples, 2)
    """
    # Optional PCA preprocessing
    preprocess_pca = config.get("preprocess_pca", 50)
    if preprocess_pca and preprocess_pca > 0 and embeddings.shape[1] > preprocess_pca:
        print(f"[PaCMAP] Preprocessing with PCA to {preprocess_pca}D...")
        embeddings = PCA(n_components=preprocess_pca, random_state=config.get("random_state", None)).fit_transform(embeddings)
        print(f"[PaCMAP] Embeddings after PCA: {embeddings.shape}")
    # Map config keys to PaCMAP arguments
    kwargs = dict(config)
    backend = config.get('backend', 'annoy')
    for k in ["subset_strategy", "subset_size", "runtime", "config_id", "name", "init", "preprocess_pca", "backend"]:
        kwargs.pop(k, None)
    kwargs["n_components"] = 2
    if "random_state" in config:
        np.random.seed(config["random_state"])
    print(f"[PaCMAP] embeddings shape: {embeddings.shape}, dtype: {embeddings.dtype}")
    print(f"[PaCMAP] min: {embeddings.min()}, max: {embeddings.max()}, any NaN: {np.isnan(embeddings).any()}, any inf: {np.isinf(embeddings).any()}")
    print(f"[PaCMAP] kwargs: {kwargs}")
    reducer = pacmap.PaCMAP(**kwargs)
    init_val = config.get("init", "pca")
    Y = reducer.fit_transform(embeddings, init=init_val)
    # Use backend for neighbor search
    if backend == 'hnswlib':
        print('[PaCMAP] Using HNSWlib for neighbor search')
        from methods.knn_hnswlib import knn_hnswlib
        pair_neighbors = knn_hnswlib(embeddings, k=config.get('n_neighbors', 10))
        # ... pass pair_neighbors to reducer or use as needed ...
    else:
        print('[PaCMAP] Using Annoy for neighbor search')
    return Y 
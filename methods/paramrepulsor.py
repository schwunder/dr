# ParamRepulsor integration for DR pipeline
# This file provides a run() function to interface with the pipeline.
# It expects embeddings (numpy array) and config (dict) as input.

from parampacmap import ParamPaCMAP
import numpy as np


def run(embeddings, config):
    """
    Run ParamRepulsor (ParamPaCMAP) dimensionality reduction.
    Args:
        embeddings (np.ndarray): Input data, shape (n_samples, n_features)
        config (dict): Configuration parameters matching PARAM_COLS["paramrepulsor"]
    Returns:
        np.ndarray: 2D projection, shape (n_samples, 2)
    """
    # Map config keys to ParamPaCMAP arguments
    kwargs = dict(config)
    # Remove keys not accepted by ParamPaCMAP if present
    for k in ["subset_strategy", "subset_size", "runtime", "config_id", "name", "spread", "repulsion_strength"]:
        kwargs.pop(k, None)
    # Force 2D output for pipeline consistency
    kwargs["n_components"] = 2
    # Always run on CPU for reproducibility
    import os
    os.environ["TORCH_DEVICE"] = "cpu"
    # Optionally set random seed for determinism
    if "random_state" in kwargs:
        import torch
        torch.manual_seed(kwargs["random_state"])
    # Map n_epochs to num_epochs for ParamPaCMAP compatibility
    if "n_epochs" in kwargs:
        kwargs["num_epochs"] = kwargs.pop("n_epochs")
    # Map init to embedding_init for ParamPaCMAP compatibility
    if "init" in kwargs:
        kwargs["embedding_init"] = kwargs.pop("init")
    print(f"[ParamRepulsor] embeddings shape: {embeddings.shape}, dtype: {embeddings.dtype}")
    print(f"[ParamRepulsor] min: {embeddings.min()}, max: {embeddings.max()}, any NaN: {np.isnan(embeddings).any()}, any inf: {np.isinf(embeddings).any()}")
    print(f"[ParamRepulsor] kwargs: {kwargs}")
    # Initialize and run ParamPaCMAP
    reducer = ParamPaCMAP(**kwargs)
    Y = reducer.fit_transform(embeddings)
    return Y 
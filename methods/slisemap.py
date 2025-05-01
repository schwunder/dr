"""
SLISEMAP/SLIPMAP integration for DR pipeline.
This wrapper allows using SLISEMAP or SLIPMAP as a dimensionality reduction method.
"""
import numpy as np

# Try to import slisemap and slipmap
try:
    from slisemap import Slisemap, Slipmap
except ImportError:
    Slisemap = None
    Slipmap = None

def run(embeddings, config):
    """
    Run SLISEMAP or SLIPMAP dimensionality reduction.
    Args:
        embeddings (np.ndarray): Input data, shape (n_samples, n_features)
        config (dict): Configuration parameters for SLISEMAP/SLIPMAP
    Returns:
        np.ndarray: 2D projection, shape (n_samples, 2)
    """
    if Slisemap is None:
        raise ImportError("slisemap is not installed. Please install it with 'pip install slisemap'.")
    # Choose which class to use
    use_slipmap = config.get("use_slipmap", False)
    radius = config.get("radius", 3.5)
    lasso = config.get("lasso", 0.01)
    y = config.get("y", None)
    # y must be provided in config or as a global variable
    if y is None:
        raise ValueError("'y' (target values) must be provided in config for SLISEMAP/SLIPMAP.")
    # Create the SLISEMAP/SLIPMAP object
    if use_slipmap:
        sm = Slipmap(embeddings, y, radius=radius, lasso=lasso)
    else:
        sm = Slisemap(embeddings, y, radius=radius, lasso=lasso)
    # Optimise the projection
    sm.optimise()
    # Return the 2D coordinates
    coords = sm._Z  # SLISEMAP/SLIPMAP embedding is stored in the '_Z' attribute
    # Ensure output is (n_samples, 2) numpy array
    coords = np.asarray(coords)
    if coords.shape[1] != 2:
        raise ValueError(f"SLISEMAP output shape {coords.shape} is not 2D")
    return coords 
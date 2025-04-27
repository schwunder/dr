#!/usr/bin/env python3
"""
Isomap implementation for dimensionality reduction.
"""
import numpy as np

def run(embeddings, config):
    """Run Isomap dimensionality reduction
    
    Args:
        embeddings: numpy array of shape (n_samples, n_features)
        config: dictionary with Isomap parameters
    
    Returns:
        numpy array of shape (n_samples, 2) with x,y coordinates
    """
    print(f"ISOMAP_START: Running Isomap on {embeddings.shape[0]} embeddings ({embeddings.shape[1]} dimensions)")
    
    try:
        # Import here to avoid startup cost if not used
        from sklearn.manifold import Isomap
        
        # Extract Isomap-specific parameters from config
        isomap_params = {
            'n_components': config.get('n_components', 2),
            'n_neighbors': config.get('n_neighbors', 5),
            'metric': config.get('metric', 'minkowski'),
        }
        
        # Add any other Isomap parameters that might be in the config
        for param in ['eigen_solver', 'tol', 'max_iter', 'path_method', 'neighbors_algorithm',
                     'p', 'metric_params', 'n_jobs']:
            if param in config:
                isomap_params[param] = config[param]
        
        print(f"ISOMAP_CONFIG: {isomap_params}")
        
        # Initialize and fit Isomap
        print("ISOMAP_PROCESS: Initializing Isomap...")
        isomap = Isomap(**isomap_params)
        
        print("ISOMAP_PROCESS: Fitting and transforming data...")
        embedding = isomap.fit_transform(embeddings)
        
        print(f"ISOMAP_COMPLETE: Produced output shape {embedding.shape}")
        
        # Sanity check on output
        if embedding.shape[0] != embeddings.shape[0]:
            print(f"ISOMAP_WARNING: Output size ({embedding.shape[0]}) doesn't match input size ({embeddings.shape[0]})")
        
        if embedding.shape[1] != 2:
            print(f"ISOMAP_WARNING: Output dimensions ({embedding.shape[1]}) is not 2")
        
        return embedding
        
    except Exception as e:
        import traceback
        print(f"ISOMAP_ERROR: {str(e)}")
        print(traceback.format_exc())
        raise

#!/usr/bin/env python3
"""
Locally Linear Embedding (LLE) implementation for dimensionality reduction.
"""
import numpy as np

def run(embeddings, config):
    """Run LLE dimensionality reduction
    
    Args:
        embeddings: numpy array of shape (n_samples, n_features)
        config: dictionary with LLE parameters
    
    Returns:
        numpy array of shape (n_samples, 2) with x,y coordinates
    """
    print(f"LLE_START: Running LLE on {embeddings.shape[0]} embeddings ({embeddings.shape[1]} dimensions)")
    
    try:
        # Import here to avoid startup cost if not used
        from sklearn.manifold import LocallyLinearEmbedding
        
        # Extract LLE-specific parameters from config
        lle_params = {
            'n_components': config.get('n_components', 2),
            'n_neighbors': config.get('n_neighbors', 15),
            'method': config.get('method', 'standard'),
            'reg': config.get('reg', 0.001),
        }
        
        # Add random_state if present
        if 'random_state' in config:
            lle_params['random_state'] = config['random_state']
        
        # Add any other LLE parameters that might be in the config
        for param in ['eigen_solver', 'tol', 'max_iter', 'hessian_tol', 
                     'modified_tol', 'neighbors_algorithm', 'n_jobs']:
            if param in config:
                lle_params[param] = config[param]
        
        print(f"LLE_CONFIG: {lle_params}")
        
        # Initialize and fit LLE
        print("LLE_PROCESS: Initializing LLE...")
        lle = LocallyLinearEmbedding(**lle_params)
        
        print("LLE_PROCESS: Fitting and transforming data...")
        embedding = lle.fit_transform(embeddings)
        
        print(f"LLE_COMPLETE: Produced output shape {embedding.shape}")
        
        # Sanity check on output
        if embedding.shape[0] != embeddings.shape[0]:
            print(f"LLE_WARNING: Output size ({embedding.shape[0]}) doesn't match input size ({embeddings.shape[0]})")
        
        if embedding.shape[1] != 2:
            print(f"LLE_WARNING: Output dimensions ({embedding.shape[1]}) is not 2")
        
        return embedding
        
    except Exception as e:
        import traceback
        print(f"LLE_ERROR: {str(e)}")
        print(traceback.format_exc())
        raise

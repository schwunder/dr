#!/usr/bin/env python3
"""
Multidimensional Scaling (MDS) implementation for dimensionality reduction.
"""
import numpy as np

def run(embeddings, config):
    """Run MDS dimensionality reduction
    
    Args:
        embeddings: numpy array of shape (n_samples, n_features)
        config: dictionary with MDS parameters
    
    Returns:
        numpy array of shape (n_samples, 2) with x,y coordinates
    """
    print(f"MDS_START: Running MDS on {embeddings.shape[0]} embeddings ({embeddings.shape[1]} dimensions)")
    
    try:
        # Import here to avoid startup cost if not used
        from sklearn.manifold import MDS
        
        # Extract MDS-specific parameters from config
        mds_params = {
            'n_components': config.get('n_components', 2),
            'metric': config.get('metric', True),
            'n_init': config.get('n_init', 4),
            'max_iter': config.get('max_iter', 300),
            'eps': config.get('eps', 1e-3),
            'dissimilarity': config.get('dissimilarity', 'euclidean'),
        }
        
        # Add random_state if present
        if 'random_state' in config:
            mds_params['random_state'] = config['random_state']
        
        # Add any other MDS parameters that might be in the config
        for param in ['n_jobs', 'normalized_stress']:
            if param in config:
                mds_params[param] = config[param]
        
        print(f"MDS_CONFIG: {mds_params}")
        
        # Initialize and fit MDS
        print("MDS_PROCESS: Initializing MDS...")
        mds = MDS(**mds_params)
        
        print("MDS_PROCESS: Fitting and transforming data...")
        embedding = mds.fit_transform(embeddings)
        
        print(f"MDS_COMPLETE: Produced output shape {embedding.shape}")
        
        # Sanity check on output
        if embedding.shape[0] != embeddings.shape[0]:
            print(f"MDS_WARNING: Output size ({embedding.shape[0]}) doesn't match input size ({embeddings.shape[0]})")
        
        if embedding.shape[1] != 2:
            print(f"MDS_WARNING: Output dimensions ({embedding.shape[1]}) is not 2")
        
        return embedding
        
    except Exception as e:
        import traceback
        print(f"MDS_ERROR: {str(e)}")
        print(traceback.format_exc())
        raise

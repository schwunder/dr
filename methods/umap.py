#!/usr/bin/env python3
"""
UMAP implementation for dimensionality reduction.
"""
import numpy as np

def run(embeddings, config):
    """Run UMAP dimensionality reduction
    
    Args:
        embeddings: numpy array of shape (n_samples, n_features)
        config: dictionary with UMAP parameters
    
    Returns:
        numpy array of shape (n_samples, 2) with x,y coordinates
    """
    print(f"UMAP_START: Running UMAP on {embeddings.shape[0]} embeddings ({embeddings.shape[1]} dimensions)")
    
    try:
        # Import here to avoid startup cost if not used
        import umap
        
        # Extract UMAP-specific parameters from config
        umap_params = {
            'n_neighbors': config.get('n_neighbors', 15),
            'min_dist': config.get('min_dist', 0.1),
            'n_components': config.get('n_components', 2),
            'metric': config.get('metric', 'euclidean'),
        }
        
        # Add random_state if present
        if 'random_state' in config:
            umap_params['random_state'] = config['random_state']
        
        # Add any other UMAP parameters that might be in the config
        for param in ['spread', 'set_op_mix_ratio', 'local_connectivity',
                     'repulsion_strength', 'negative_sample_rate',
                     'transform_queue_size', 'a', 'b', 'init', 'target_n_neighbors',
                     'target_weight', 'transform_seed', 'metric_kwds', 
                     'angular_rp_forest', 'verbose']:
            if param in config:
                umap_params[param] = config[param]
        
        print(f"UMAP_CONFIG: {umap_params}")
        
        # Initialize and fit UMAP
        print("UMAP_PROCESS: Initializing UMAP...")
        reducer = umap.UMAP(**umap_params)
        
        print("UMAP_PROCESS: Fitting and transforming data...")
        embedding = reducer.fit_transform(embeddings)
        
        print(f"UMAP_COMPLETE: Produced output shape {embedding.shape}")
        
        # Sanity check on output
        if embedding.shape[0] != embeddings.shape[0]:
            print(f"UMAP_WARNING: Output size ({embedding.shape[0]}) doesn't match input size ({embeddings.shape[0]})")
        
        if embedding.shape[1] != 2:
            print(f"UMAP_WARNING: Output dimensions ({embedding.shape[1]}) is not 2")
        
        return embedding
        
    except Exception as e:
        import traceback
        print(f"UMAP_ERROR: {str(e)}")
        print(traceback.format_exc())
        raise

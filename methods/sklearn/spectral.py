#!/usr/bin/env python3
"""
Spectral Embedding implementation for dimensionality reduction.
"""
import numpy as np

def run(embeddings, config):
    """Run Spectral Embedding dimensionality reduction
    
    Args:
        embeddings: numpy array of shape (n_samples, n_features)
        config: dictionary with Spectral Embedding parameters
    
    Returns:
        numpy array of shape (n_samples, 2) with x,y coordinates
    """
    print(f"SPECTRAL_START: Running Spectral Embedding on {embeddings.shape[0]} embeddings ({embeddings.shape[1]} dimensions)")
    
    try:
        # Import here to avoid startup cost if not used
        from sklearn.manifold import SpectralEmbedding
        
        # Extract Spectral-specific parameters from config
        spectral_params = {
            'n_components': config.get('n_components', 2),
            'affinity': config.get('affinity', 'nearest_neighbors'),
        }
        
        # Handle nearest neighbors parameters
        if spectral_params['affinity'] == 'nearest_neighbors':
            spectral_params['n_neighbors'] = config.get('n_neighbors', 10)
        
        # Add random_state if present
        if 'random_state' in config:
            spectral_params['random_state'] = config['random_state']
        
        # Add any other Spectral parameters that might be in the config
        for param in ['gamma', 'eigen_solver', 'eigen_tol', 'drop_first', 'norm_laplacian', 
                     'n_jobs']:
            if param in config:
                spectral_params[param] = config[param]
        
        print(f"SPECTRAL_CONFIG: {spectral_params}")
        
        # Initialize and fit Spectral Embedding
        print("SPECTRAL_PROCESS: Initializing Spectral Embedding...")
        spectral = SpectralEmbedding(**spectral_params)
        
        print("SPECTRAL_PROCESS: Fitting and transforming data...")
        embedding = spectral.fit_transform(embeddings)
        
        print(f"SPECTRAL_COMPLETE: Produced output shape {embedding.shape}")
        
        # Sanity check on output
        if embedding.shape[0] != embeddings.shape[0]:
            print(f"SPECTRAL_WARNING: Output size ({embedding.shape[0]}) doesn't match input size ({embeddings.shape[0]})")
        
        if embedding.shape[1] != 2:
            print(f"SPECTRAL_WARNING: Output dimensions ({embedding.shape[1]}) is not 2")
        
        return embedding
        
    except Exception as e:
        import traceback
        print(f"SPECTRAL_ERROR: {str(e)}")
        print(traceback.format_exc())
        raise

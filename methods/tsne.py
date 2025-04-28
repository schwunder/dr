#!/usr/bin/env python3
"""
t-SNE implementation for dimensionality reduction.
"""
import numpy as np

def run(embeddings, config):
    """Run t-SNE dimensionality reduction
    
    Args:
        embeddings: numpy array of shape (n_samples, n_features)
        config: dictionary with t-SNE parameters
    
    Returns:
        numpy array of shape (n_samples, 2) with x,y coordinates
    """
    print(f"TSNE_START: Running t-SNE on {embeddings.shape[0]} embeddings ({embeddings.shape[1]} dimensions)")
    
    try:
        # Import here to avoid startup cost if not used
        from openTSNE import TSNE
        
        # Extract t-SNE-specific parameters from config
        tsne_params = {
            'n_components': config.get('n_components', 2),
            'perplexity': config.get('perplexity', 30),
            'learning_rate': config.get('learning_rate', 200),  # openTSNE default
            'n_iter': config.get('n_iter', 1000),
            'metric': config.get('metric', 'euclidean'),
        }
        
        # openTSNE uses 'random_state'
        if 'random_state' in config:
            tsne_params['random_state'] = config['random_state']
        
        # openTSNE-specific params
        for param in ['early_exaggeration_iter', 'early_exaggeration', 'theta', 'negative_gradient_method', 'initialization', 'verbose', 'n_jobs']:
            if param in config:
                tsne_params[param] = config[param]
        
        print(f"TSNE_CONFIG: {tsne_params}")
        
        # Initialize and fit t-SNE
        print("TSNE_PROCESS: Initializing t-SNE...")
        tsne = TSNE(**tsne_params)
        
        print("TSNE_PROCESS: Fitting and transforming data...")
        embedding = tsne.fit(embeddings)
        
        print(f"TSNE_COMPLETE: Produced output shape {embedding.shape}")
        
        # Sanity check on output
        if embedding.shape[0] != embeddings.shape[0]:
            print(f"TSNE_WARNING: Output size ({embedding.shape[0]}) doesn't match input size ({embeddings.shape[0]})")
        
        if embedding.shape[1] != 2:
            print(f"TSNE_WARNING: Output dimensions ({embedding.shape[1]}) is not 2")
        
        return embedding
        
    except Exception as e:
        import traceback
        print(f"TSNE_ERROR: {str(e)}")
        print(traceback.format_exc())
        raise

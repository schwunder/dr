#!/usr/bin/env python3
"""
tsne_pso.py – t-SNE with Particle Swarm Optimization for dimensionality reduction.
"""
import numpy as np

def run(embeddings, config):
    """Run TSNE-PSO dimensionality reduction
    
    Args:
        embeddings: numpy array of shape (n_samples, n_features)
        config: dictionary with TSNE-PSO parameters
    
    Returns:
        numpy array of shape (n_samples, 2) with x,y coordinates
    """
    # Valid TSNEPSO arguments (from __init__):
    # n_components, perplexity, early_exaggeration, learning_rate, n_iter, n_particles, inertia_weight,
    # cognitive_weight, social_weight, use_hybrid, degrees_of_freedom, init, verbose, random_state, method,
    # angle, n_jobs, metric, metric_params, h, f
    print(f"TSNE_PSO_START: Running TSNE-PSO on {embeddings.shape[0]} embeddings ({embeddings.shape[1]} dimensions)")
    try:
        # Import here to avoid startup cost if not used
        from tsne_pso import TSNEPSO
        # Map config keys to TSNEPSO arguments
        tsne_pso_params = {
            'n_components': config.get('n_components', 2),
            'perplexity': config.get('perplexity', 30.0),
            'early_exaggeration': config.get('early_exaggeration', 12.0),
            'learning_rate': config.get('learning_rate', 200.0),
            'n_iter': config.get('n_iter', 500),
            'n_particles': config.get('n_particles', 10),
            'inertia_weight': config.get('inertia_weight', 0.7),
            'cognitive_weight': config.get('cognitive_weight', 1.0),
            'social_weight': config.get('social_weight', 1.0),
            'use_hybrid': config.get('use_hybrid', True),
            'degrees_of_freedom': config.get('degrees_of_freedom', 1.0),
            'init': config.get('init', 'pca'),
            'verbose': config.get('verbose', 0),
            'random_state': config.get('random_state', 42),
            'method': config.get('method', 'pso'),
            'angle': config.get('angle', 0.5),
            'n_jobs': config.get('n_jobs', None),
            'metric': config.get('metric', 'euclidean'),
            'metric_params': config.get('metric_params', None),
            'h': config.get('h', 1e-20),
            'f': config.get('f', 1e-21),
        }
        # Remove keys with value None to avoid passing them if not set
        tsne_pso_params = {k: v for k, v in tsne_pso_params.items() if v is not None}
        print(f"TSNE_PSO_CONFIG: {tsne_pso_params}")
        # Ensure correct types for numeric parameters (robust to YAML string/number ambiguity)
        float_keys = [
            'perplexity', 'early_exaggeration', 'learning_rate', 'inertia_weight',
            'cognitive_weight', 'social_weight', 'degrees_of_freedom', 'angle', 'h', 'f'
        ]
        int_keys = ['n_components', 'n_iter', 'n_particles', 'verbose', 'random_state', 'n_jobs']
        for k in float_keys:
            if k in tsne_pso_params and tsne_pso_params[k] is not None:
                try:
                    tsne_pso_params[k] = float(tsne_pso_params[k])
                except Exception:
                    pass  # If already correct type or not convertible, leave as is
        for k in int_keys:
            if k in tsne_pso_params and tsne_pso_params[k] is not None:
                try:
                    tsne_pso_params[k] = int(tsne_pso_params[k])
                except Exception:
                    pass
        # Initialize and fit TSNE-PSO
        print("TSNE_PSO_PROCESS: Initializing TSNE-PSO...")
        tsne_pso = TSNEPSO(**tsne_pso_params)
        print("TSNE_PSO_PROCESS: Fitting and transforming data...")
        embedding = tsne_pso.fit_transform(embeddings)
        print(f"TSNE_PSO_COMPLETE: Produced output shape {embedding.shape}")
        # Sanity check on output
        if embedding.shape[0] != embeddings.shape[0]:
            print(f"TSNE_PSO_WARNING: Output size ({embedding.shape[0]}) doesn't match input size ({embeddings.shape[0]})")
        if embedding.shape[1] != 2:
            print(f"TSNE_PSO_WARNING: Output dimensions ({embedding.shape[1]}) is not 2")
        return embedding
    except Exception as e:
        import traceback
        print(f"TSNE_PSO_ERROR: {str(e)}")
        print(traceback.format_exc())
        raise 
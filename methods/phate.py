import numpy as np

def run(embeddings, config):
    """
    Run PHATE dimensionality reduction.

    Args:
        embeddings: numpy array of shape (n_samples, n_features)
        config: dictionary with PHATE parameters

    Returns:
        list of (x, y) tuples for each sample
    """
    import phate

    # Prepare PHATE parameters, using only those present in config
    phate_params = {
        'n_components': config.get('n_components', 2),
        'knn': config.get('knn', 5),
        'decay': config.get('decay', 40),
        't': config.get('t', 'auto'),
        'gamma': config.get('gamma', 1),
        'random_state': config.get('random_state', 42)
    }

    phate_op = phate.PHATE(**phate_params)
    embedding = phate_op.fit_transform(embeddings)

    # Ensure output is a list of (x, y) tuples
    return [(float(x), float(y)) for x, y in embedding] 
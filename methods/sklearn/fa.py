import numpy as np

def run(embeddings, config):
    """
    Run FactorAnalysis dimensionality reduction.

    Args:
        embeddings: numpy array of shape (n_samples, n_features)
        config: dictionary with FA parameters

    Returns:
        numpy array of shape (n_samples, 2) with x, y coordinates
    """
    from sklearn.decomposition import FactorAnalysis

    fa_params = {
        'n_components': config.get('n_components', 2)
    }
    if 'random_state' in config:
        fa_params['random_state'] = config['random_state']

    fa = FactorAnalysis(**fa_params)
    embedding = fa.fit_transform(embeddings)
    return embedding 
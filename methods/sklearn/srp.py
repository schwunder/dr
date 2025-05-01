import numpy as np

def run(embeddings, config):
    """
    Run SparseRandomProjection dimensionality reduction.

    Args:
        embeddings: numpy array of shape (n_samples, n_features)
        config: dictionary with SRP parameters

    Returns:
        numpy array of shape (n_samples, 2) with x, y coordinates
    """
    from sklearn.random_projection import SparseRandomProjection

    srp_params = {
        'n_components': config.get('n_components', 2)
    }
    if config.get('density', 'auto') != 'auto':
        srp_params['density'] = config['density']
    if config.get('eps') is not None:
        srp_params['eps'] = config['eps']
    if 'random_state' in config:
        srp_params['random_state'] = config['random_state']

    srp = SparseRandomProjection(**srp_params)
    embedding = srp.fit_transform(embeddings)
    return embedding 
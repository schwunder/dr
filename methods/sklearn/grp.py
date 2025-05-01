import numpy as np

def run(embeddings, config):
    """
    Run GaussianRandomProjection dimensionality reduction.

    Args:
        embeddings: numpy array of shape (n_samples, n_features)
        config: dictionary with GRP parameters

    Returns:
        numpy array of shape (n_samples, 2) with x, y coordinates
    """
    from sklearn.random_projection import GaussianRandomProjection

    grp_params = {
        'n_components': config.get('n_components', 2)
    }
    if config.get('eps') is not None:
        grp_params['eps'] = config['eps']
    if 'random_state' in config:
        grp_params['random_state'] = config['random_state']

    grp = GaussianRandomProjection(**grp_params)
    embedding = grp.fit_transform(embeddings)
    return embedding 
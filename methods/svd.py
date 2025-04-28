import numpy as np

def run(embeddings, config):
    """
    Run TruncatedSVD dimensionality reduction.

    Args:
        embeddings: numpy array of shape (n_samples, n_features)
        config: dictionary with SVD parameters

    Returns:
        numpy array of shape (n_samples, 2) with x, y coordinates
    """
    from sklearn.decomposition import TruncatedSVD

    svd_params = {
        'n_components': config.get('n_components', 2)
    }
    if 'random_state' in config:
        svd_params['random_state'] = config['random_state']

    svd = TruncatedSVD(**svd_params)
    embedding = svd.fit_transform(embeddings)
    return embedding 
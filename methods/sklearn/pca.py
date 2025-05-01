import numpy as np

def run(embeddings, config):
    """
    Run PCA dimensionality reduction.

    Args:
        embeddings: numpy array of shape (n_samples, n_features)
        config: dictionary with PCA parameters

    Returns:
        numpy array of shape (n_samples, 2) with x, y coordinates
    """
    from sklearn.decomposition import PCA

    pca_params = {
        'n_components': config.get('n_components', 2)
    }
    if 'random_state' in config:
        pca_params['random_state'] = config['random_state']

    pca = PCA(**pca_params)
    embedding = pca.fit_transform(embeddings)
    return embedding 
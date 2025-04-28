import numpy as np

def run(embeddings, config):
    """
    Run KernelPCA dimensionality reduction.

    Args:
        embeddings: numpy array of shape (n_samples, n_features)
        config: dictionary with KernelPCA parameters

    Returns:
        numpy array of shape (n_samples, 2) with x, y coordinates
    """
    from sklearn.decomposition import KernelPCA

    kpca_params = {
        'n_components': config.get('n_components', 2),
        'kernel': config.get('kernel', 'rbf'),
        'gamma': config.get('gamma', 1.0),
        'fit_inverse_transform': config.get('fit_inverse_transform', True)
    }
    if 'random_state' in config:
        kpca_params['random_state'] = config['random_state']

    kpca = KernelPCA(**kpca_params)
    embedding = kpca.fit_transform(embeddings)
    return embedding 
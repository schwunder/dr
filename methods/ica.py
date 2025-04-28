import numpy as np

def run(embeddings, config):
    """
    Run FastICA dimensionality reduction.

    Args:
        embeddings: numpy array of shape (n_samples, n_features)
        config: dictionary with ICA parameters

    Returns:
        numpy array of shape (n_samples, 2) with x, y coordinates
    """
    from sklearn.decomposition import FastICA

    ica_params = {
        'n_components': config.get('n_components', 2),
        'max_iter': config.get('max_iter', 500)
    }
    if 'random_state' in config:
        ica_params['random_state'] = config['random_state']

    ica = FastICA(**ica_params)
    embedding = ica.fit_transform(embeddings)
    return embedding 
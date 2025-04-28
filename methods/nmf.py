import numpy as np

def run(embeddings, config):
    """
    Run Non-negative Matrix Factorization (NMF) dimensionality reduction.

    Args:
        embeddings: numpy array of shape (n_samples, n_features)
        config: dictionary with NMF parameters

    Returns:
        numpy array of shape (n_samples, 2) with x, y coordinates
    """
    from sklearn.decomposition import NMF

    # NMF requires non-negative data. Shift so min is zero.
    embeddings_nmf = embeddings - embeddings.min()

    nmf_params = {
        'n_components': config.get('n_components', 2),
        'init': config.get('init', 'nndsvda')
    }
    if 'random_state' in config:
        nmf_params['random_state'] = config['random_state']

    nmf = NMF(**nmf_params)
    embedding = nmf.fit_transform(embeddings_nmf)
    return embedding 
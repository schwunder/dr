import numpy as np

def run(embeddings, config):
    """
    Run IncrementalPCA dimensionality reduction.

    Args:
        embeddings: numpy array of shape (n_samples, n_features)
        config: dictionary with IPCA parameters

    Returns:
        numpy array of shape (n_samples, 2) with x, y coordinates
    """
    from sklearn.decomposition import IncrementalPCA

    ipca_params = {
        'n_components': config.get('n_components', 2),
        'batch_size': config.get('batch_size', None)
    }
    # random_state is not a valid parameter for IncrementalPCA

    ipca = IncrementalPCA(**ipca_params)
    embedding = ipca.fit_transform(embeddings)
    return embedding 
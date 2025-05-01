import numpy as np

def run(embeddings, config):
    """
    Run Nystroem + PCA pipeline for approximate kernel DR.

    Args:
        embeddings: numpy array of shape (n_samples, n_features)
        config: dictionary with Nystroem and PCA parameters

    Returns:
        numpy array of shape (n_samples, 2) with x, y coordinates
    """
    from sklearn.kernel_approximation import Nystroem
    from sklearn.decomposition import PCA
    from sklearn.pipeline import make_pipeline

    nystroem_params = {
        'kernel': config.get('kernel', 'rbf'),
        'gamma': config.get('gamma', 1.0),
        'n_components': config.get('nystroem_components', 200),
        'random_state': config.get('random_state', None)
    }
    pca_params = {
        'n_components': config.get('n_components', 2),
        'random_state': config.get('random_state', None)
    }

    feat_map = Nystroem(**nystroem_params)
    pca = PCA(**pca_params)
    pipe = make_pipeline(feat_map, pca)
    embedding = pipe.fit_transform(embeddings)
    return embedding 
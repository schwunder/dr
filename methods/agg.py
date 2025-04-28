import numpy as np

def run(embeddings, config):
    """
    Run FeatureAgglomeration dimensionality reduction.

    Args:
        embeddings: numpy array of shape (n_samples, n_features)
        config: dictionary with agglomeration parameters

    Returns:
        numpy array of shape (n_samples, 2) with x, y coordinates
    """
    from sklearn.cluster import FeatureAgglomeration

    agg_params = {
        'n_clusters': config.get('n_clusters', 2)
    }

    agg = FeatureAgglomeration(**agg_params)
    embedding = agg.fit_transform(embeddings)
    return embedding 
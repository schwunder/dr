import numpy as np

def run(embeddings, config):
    """
    Run DictionaryLearning dimensionality reduction.

    Args:
        embeddings: numpy array of shape (n_samples, n_features)
        config: dictionary with DictionaryLearning parameters

    Returns:
        numpy array of shape (n_samples, 2) with x, y coordinates
    """
    from sklearn.decomposition import DictionaryLearning

    dict_params = {
        'n_components': config.get('n_components', 2)
    }
    if 'random_state' in config:
        dict_params['random_state'] = config['random_state']

    dictlearn = DictionaryLearning(**dict_params)
    embedding = dictlearn.fit_transform(embeddings)
    return embedding 
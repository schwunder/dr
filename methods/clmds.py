# methods/clmds.py
# Integration of cl-MDS into the DR pipeline
# Requires cl-MDS to be built and available in PYTHONPATH

import sys
import os
import numpy as np

# Add cl-MDS to the path if not already present
clmds_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../cl-MDS'))
if clmds_path not in sys.path:
    sys.path.append(clmds_path)

# Import the main cl-MDS class
from cluster_mds import clMDS

def run(embeddings, config):
    """
    Run cl-MDS on the given embeddings with the provided config.
    Returns: 2D numpy array of shape (n_samples, 2)
    """
    # Map config dict to cl-MDS parameters as needed
    n_clusters = config.get('n_clusters', 5)
    max_iter = config.get('max_iter', 300)
    # random_state is not supported by cluster_MDS directly

    # cl-MDS expects a distance matrix; compute it from embeddings
    X = np.asarray(embeddings)
    from scipy.spatial.distance import pdist, squareform
    dist_matrix = squareform(pdist(X, metric='euclidean'))

    # Initialize clMDS class
    clmds = clMDS(dist_matrix=dist_matrix, verbose=True)

    # Run cluster_MDS (hierarchy is a list, e.g., [n_clusters, 1])
    clmds.cluster_MDS(hierarchy=[n_clusters, 1], max_iter_cluster=max_iter)

    # The 2D embedding is in clmds.local_sparse_coordinates
    embedding_2d = clmds.local_sparse_coordinates
    # Ensure result is (n_samples, 2)
    return embedding_2d 
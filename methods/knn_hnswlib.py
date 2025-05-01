import numpy as np
import hnswlib

def knn_hnswlib(embeddings, k=10, ef=50, M=32):
    """
    Compute k-nearest neighbors using HNSWlib.
    Args:
        embeddings (np.ndarray): shape (n_samples, n_features)
        k (int): number of neighbors
        ef (int): size of the dynamic list for the nearest neighbors (higher = more accurate)
        M (int): number of bi-directional links created for every new element during construction
    Returns:
        np.ndarray: neighbor indices, shape (n_samples, k)
    """
    n, d = embeddings.shape
    index = hnswlib.Index(space='l2', dim=d)
    index.init_index(max_elements=n, ef_construction=200, M=M)
    index.add_items(embeddings.astype(np.float32))
    index.set_ef(ef)
    labels, distances = index.knn_query(embeddings, k=k)
    return labels

if __name__ == "__main__":
    # Example/test: load 100 embeddings from art.sqlite and print neighbors
    import sqlite3
    conn = sqlite3.connect('art.sqlite')
    c = conn.cursor()
    c.execute('SELECT embedding FROM embeddings LIMIT 100')
    rows = c.fetchall()
    embeddings = [np.frombuffer(blob, dtype=np.float32) for (blob,) in rows]
    embeddings = np.stack(embeddings)
    print('Loaded embeddings shape:', embeddings.shape)
    from sklearn.decomposition import PCA
    X_pca = PCA(n_components=50).fit_transform(embeddings)
    neighbors = knn_hnswlib(X_pca, k=6)
    for i in range(5):
        print(f'HNSWlib neighbors for point {i}:', neighbors[i].tolist()) 
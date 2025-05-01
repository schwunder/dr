import sqlite3
import numpy as np
from annoy import AnnoyIndex
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler, Normalizer
from sklearn.random_projection import GaussianRandomProjection
import faiss

# Try to import hnswlib and nmslib
try:
    import hnswlib
    HNSWLIB_AVAILABLE = True
except ImportError:
    HNSWLIB_AVAILABLE = False
try:
    import nmslib
    NMSLIB_AVAILABLE = True
except ImportError:
    NMSLIB_AVAILABLE = False

# Load a few embeddings from the database
conn = sqlite3.connect('art.sqlite')
c = conn.cursor()
c.execute('SELECT embedding FROM embeddings LIMIT 100')
rows = c.fetchall()
embeddings = [np.frombuffer(blob, dtype=np.float32) for (blob,) in rows]
embeddings = np.stack(embeddings)
print('Loaded embeddings shape:', embeddings.shape)
print('First embedding, first 10 values:', embeddings[0][:10])

def test_annoy(X, label):
    print(f'\n--- Annoy test: {label} ---')
    dims = X.shape[1]
    try:
        index = AnnoyIndex(dims, 'euclidean')
        for i, v in enumerate(X):
            index.add_item(i, v.tolist())
        index.build(200)
        for i in range(5):
            neighbors = index.get_nns_by_item(i, 6, search_k=50000)
            print(f'Annoy neighbors for point {i}:', neighbors)
    except Exception as e:
        print(f'[ERROR] {label}: {e}')

def test_faiss(X, label):
    print(f'\n--- FAISS test: {label} ---')
    dims = X.shape[1]
    try:
        index = faiss.IndexFlatL2(dims)
        X32 = X.astype(np.float32)
        index.add(X32)
        D, I = index.search(X32[:5], 6)
        for i, neighbors in enumerate(I):
            print(f'FAISS neighbors for point {i}:', neighbors.tolist())
    except Exception as e:
        print(f'[ERROR] FAISS {label}: {e}')

def test_hnswlib(X, label):
    if not HNSWLIB_AVAILABLE:
        print(f'\n--- HNSWlib not available: {label} ---')
        return
    print(f'\n--- HNSWlib test: {label} ---')
    dims = X.shape[1]
    try:
        p = hnswlib.Index(space='l2', dim=dims)
        p.init_index(max_elements=X.shape[0], ef_construction=200, M=32)
        p.add_items(X.astype(np.float32))
        p.set_ef(50)
        labels, distances = p.knn_query(X[:5], k=6)
        for i, neighbors in enumerate(labels):
            print(f'HNSWlib neighbors for point {i}:', neighbors.tolist())
    except Exception as e:
        print(f'[ERROR] HNSWlib {label}: {e}')

def test_nmslib(X, label):
    if not NMSLIB_AVAILABLE:
        print(f'\n--- nmslib not available: {label} ---')
        return
    print(f'\n--- nmslib test: {label} ---')
    dims = X.shape[1]
    try:
        index = nmslib.init(method='hnsw', space='l2')
        index.addDataPointBatch(X.astype(np.float32))
        index.createIndex({'post': 2}, print_progress=False)
        neighbors = index.knnQueryBatch(X[:5], k=6, num_threads=1)
        for i, (nbrs, dists) in enumerate(neighbors):
            print(f'nmslib neighbors for point {i}:', nbrs.tolist())
    except Exception as e:
        print(f'[ERROR] nmslib {label}: {e}')

# PCA 50D
pca = PCA(n_components=50)
X_pca = pca.fit_transform(embeddings)
test_annoy(X_pca, 'PCA 50D')
test_faiss(X_pca, 'PCA 50D')
test_hnswlib(X_pca, 'PCA 50D')
test_nmslib(X_pca, 'PCA 50D')

# PCA 10D
pca10 = PCA(n_components=10)
X_pca10 = pca10.fit_transform(embeddings)
test_annoy(X_pca10, 'PCA 10D')
# Gaussian Random Projection 50D
grp = GaussianRandomProjection(n_components=50)
X_grp = grp.fit_transform(embeddings)
test_annoy(X_grp, 'GaussianRandomProjection 50D')
# PCA 50D + StandardScaler
scaler = StandardScaler()
X_pca_scaled = scaler.fit_transform(X_pca)
test_annoy(X_pca_scaled, 'PCA 50D + StandardScaler')
# PCA 50D + StandardScaler + L2 norm
normalizer = Normalizer(norm='l2')
X_pca_scaled_norm = normalizer.fit_transform(X_pca_scaled)
test_annoy(X_pca_scaled_norm, 'PCA 50D + StandardScaler + L2 norm') 
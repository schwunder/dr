import numpy as np
from annoy import AnnoyIndex
import sqlite3
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors

# Fetch a subset from the embeddings table
conn = sqlite3.connect('art.sqlite')
cursor = conn.cursor()
rows = cursor.execute("SELECT embedding FROM embeddings ORDER BY random() LIMIT 500").fetchall()
embeddings = np.vstack([np.frombuffer(r[0], np.float32) for r in rows])
conn.close()

n, d = embeddings.shape
n_neighbors = 5
n_neighbors_extra = min(n_neighbors + 50, n - 1)

print(f"Embeddings shape: {embeddings.shape}")

# --- PCA Step ---
pca = PCA(n_components=50)
embeddings_pca = pca.fit_transform(embeddings)
print(f"After PCA: {embeddings_pca.shape}")

# Build Annoy index on PCA-reduced data
index = AnnoyIndex(50, 'euclidean')
for i in range(n):
    index.add_item(i, embeddings_pca[i])
index.build(20)

# Check neighbors for each point (Annoy + PCA)
empty_count = 0
for i in range(n):
    nbrs_ = index.get_nns_by_item(i, n_neighbors_extra + 1)
    if len(nbrs_[1:]) == 0:
        print(f"[Annoy+PCA] Point {i}: No neighbors found (excluding self)")
        empty_count += 1
    else:
        print(f"[Annoy+PCA] Point {i}: {len(nbrs_[1:])} neighbors found")
print(f"[Annoy+PCA] Total points with no neighbors (excluding self): {empty_count} / {n}")

# --- Brute-force NearestNeighbors ---
brute = NearestNeighbors(n_neighbors=n_neighbors+1, algorithm='brute', metric='euclidean')
brute.fit(embeddings)
brute_neighbors = brute.kneighbors(embeddings, return_distance=False)
brute_empty_count = 0
for i, nbrs_ in enumerate(brute_neighbors):
    # Exclude self (first neighbor)
    if len(nbrs_[1:]) == 0:
        print(f"[Brute] Point {i}: No neighbors found (excluding self)")
        brute_empty_count += 1
    else:
        print(f"[Brute] Point {i}: {len(nbrs_[1:])} neighbors found")
print(f"[Brute] Total points with no neighbors (excluding self): {brute_empty_count} / {n}") 
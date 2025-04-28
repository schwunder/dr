import numpy as np

try:
    from sammon import sammon
    sammon_func = sammon.sammon  # The function is an attribute of the submodule
except (ImportError, AttributeError):
    try:
        from sammon.sammon import sammon as sammon_func  # Direct import from submodule
    except ImportError:
        raise ImportError(
            "Could not import the 'sammon' function from the 'sammon-mapping' package. "
            "Please check your installation and package version."
        )

def run(embeddings, config):
    # embeddings: 2D numpy array, shape (n_samples, n_features)
    params = {k: config[k] for k in [
        "n", "display", "inputdist", "maxhalves", "maxiter", "tolfun", "init"
    ] if k in config}
    y, stress = sammon.sammon(embeddings, **params)
    # Return list of (filename, artist, x, y) -- meta is not passed here, so just return coordinates
    return [(None, None, float(y[i, 0]), float(y[i, 1])) for i in range(len(embeddings))]

    # embeddings: list of (filename, artist, embedding)
    emb_bytes = embeddings[0][2]
    print("Length of first embedding bytes:", len(emb_bytes))
    print("First 10 bytes of first embedding:", emb_bytes[:10])
    first_emb = np.frombuffer(emb_bytes, dtype=np.float32)
    print("Shape of first embedding:", first_emb.shape)
    print("First 10 values of first embedding:", first_emb[:10])
    if first_emb.shape != (1536,):
        print("Warning: Each embedding should be shape (1536,)")
    X = np.vstack([np.frombuffer(e[2], dtype=np.float32) for e in embeddings])  # shape (n_samples, n_features)
    print("Shape of X:", X.shape)
    print("Number of embeddings:", len(embeddings))
    # Prepare parameters for sammon
    params = {k: config[k] for k in [
        "n", "display", "inputdist", "maxhalves", "maxiter", "tolfun", "init"
    ] if k in config}
    # Run Sammon mapping
    try:
        y, stress = sammon_func(X, **params)
    except Exception as err:
        print(f"Error running Sammon: {err}")
        print(f"Shape of X: {X.shape}, dtype: {X.dtype}")
        raise
    # Return list of (filename, artist, x, y)
    return [
        (embeddings[i][0], embeddings[i][1], float(y[i, 0]), float(y[i, 1]))
        for i in range(len(embeddings))
    ] 
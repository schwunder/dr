import trimap
import numpy as np

def run(embeddings, config):
    # Set numpy random seed for reproducibility if random_state is provided
    if config.get("random_state") is not None:
        np.random.seed(config["random_state"])
    reducer = trimap.TRIMAP(
        n_dims=config.get("n_dims", 2),
        n_inliers=config.get("n_inliers", 12),
        n_outliers=config.get("n_outliers", 4),
        n_random=config.get("n_random", 3),
        distance=config.get("distance", "euclidean"),
        weight_temp=config.get("weight_temp", 0.5),
        lr=config.get("lr", 0.1),
        n_iters=config.get("n_iters", 400),
        opt_method=config.get("opt_method", "dbd"),
        apply_pca=config.get("apply_pca", True),
        verbose=False
    )
    return reducer.fit_transform(embeddings) 
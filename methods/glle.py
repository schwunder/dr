from GLLE.functions.my_GLLE import My_GLLE
from GLLE.functions.my_GLLE_DirectSampling import My_GLLE_DirectSampling
import numpy as np

def run(embeddings: np.ndarray, cfg: dict) -> np.ndarray:
    print("[GLLE wrapper] embeddings.shape:", embeddings.shape)
    print("[GLLE wrapper] embeddings.dtype:", embeddings.dtype)
    print("[GLLE wrapper] embeddings has NaN:", np.isnan(embeddings).any())
    print("[GLLE wrapper] embeddings has inf:", np.isinf(embeddings).any())
    print("[GLLE wrapper] config:", cfg)
    # 1) enforce 2D
    if cfg.get("n_components", 2) != 2:
        raise ValueError("GLLE supports only n_components=2")

    X = embeddings.T  # GLLE expects features x samples
    method = cfg["method"]
    if method == "GLLE":
        model = My_GLLE(
            X,
            n_neighbors=cfg["k_neighbors"],
            n_components=cfg["n_components"],
            path_save="./",  # or a temp dir if you want to use the save/load features
            max_itr_reconstruction=cfg["max_iterations"],
            verbosity=cfg.get("verbosity", 1)
        )
        Y = model.fit_transform(calculate_again=True)
    elif method == "GLLE_DirectSampling":
        model = My_GLLE_DirectSampling(
            X,
            n_neighbors=cfg["k_neighbors"],
            n_components=cfg["n_components"],
            path_save="./",
            verbosity=cfg.get("verbosity", 1)
        )
        Y = model.fit_transform(calculate_again=True)
    else:
        raise ValueError(f"Unknown GLLE method: {method}")
    return Y.T  # Return as samples x features (n x 2) 
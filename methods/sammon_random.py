def run(embeddings, config):
    import numpy as np
    np.random.seed(42)  # Set random seed for reproducibility
    try:
        # evomap does not expose Sammon at the top level; import from internal module
        from evomap.mapping._sammon import Sammon  # type: ignore[import]
    except ImportError:
        raise ImportError("evomap is not installed. Please install it with 'pip install evomap'.")
    params = {k: config[k] for k in [
        "n_dims", "n_iter", "tol", "input_type"
    ] if k in config}
    if "tol" in params:
        try:
            params["tol"] = float(params["tol"])
        except Exception:
            pass
    print("Params passed to evomap Sammon:")
    for k, v in params.items():
        print(f"  {k}: {v} (type: {type(v)})")
    sammon = Sammon(**params)
    y = sammon.fit_transform(embeddings)
    return [(float(y[i, 0]), float(y[i, 1])) for i in range(len(embeddings))] 
# run.py
#!/usr/bin/env python3
"""CLI runner for any DR method defined in configs.yaml."""
import argparse, importlib, time, yaml, sys
import db

def load_configs() -> dict:
    with open("configs.yaml", "r") as f:
        return yaml.safe_load(f)

def main(argv=None):
    cfgs = load_configs()
    p = argparse.ArgumentParser()
    p.add_argument("--method", required=True, choices=cfgs.keys())
    p.add_argument("--config", required=True)
    args = p.parse_args(argv)

    cfg = next((c.copy() for c in cfgs[args.method]
                if c["name"] == args.config), None)
    if cfg is None:
        sys.exit(f"No config “{args.config}” for {args.method}")

    subset = cfg.pop("subset_strategy", "artist_first5")
    size   = cfg.pop("subset_size", 250)

    embeddings, meta = db.fetch_subset(subset, size)
    sklearn_methods = {
        'agg', 'dictlearn', 'fa', 'grp', 'ica', 'ipca', 'isomap', 'kpca', 'lle', 'mds',
        'nmf', 'nystroem_pca', 'pca', 'spectral', 'srp', 'svd'
    }
    if args.method in sklearn_methods:
        mod = importlib.import_module(f"methods.sklearn.{args.method}")
    else:
        mod = importlib.import_module(f"methods.{args.method}")

    if args.method == "slisemap":
        # Encode 'artist' field from meta as integer labels for y
        artists = [m["artist"] for m in meta]
        unique_artists = {name: idx for idx, name in enumerate(sorted(set(artists)))}
        # Store y separately from config to avoid database issues
        y = [unique_artists[name] for name in artists]
        cfg["y"] = y  # Used by SLISEMAP
        cfg_for_db = cfg.copy()
        del cfg_for_db["y"]  # Remove y before storing in database
    elif args.method == "tsimcne":
        cfg_for_db = cfg.copy()
        # Convert total_epochs to comma-separated string for DB if it's a list
        if isinstance(cfg_for_db.get("total_epochs"), list):
            cfg_for_db["total_epochs"] = ",".join(str(x) for x in cfg_for_db["total_epochs"])
    else:
        cfg_for_db = cfg

    start  = time.time()
    coords = mod.run(embeddings, cfg)
    runtime = time.time() - start

    # Use the database-safe config for storage
    cfg_id = db.upsert_config(args.method, cfg_for_db, subset, size, runtime)
    db.save_points(args.method, cfg_id, meta, coords)
    print(
        f"✅ {args.method}:{args.config}  "
        f"cfg_id={cfg_id}  pts={len(coords)}  time={runtime:.2f}s"
    )

if __name__ == "__main__":
    main()
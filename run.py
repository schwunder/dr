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
    mod = importlib.import_module(f"methods.{args.method}")

    start  = time.time()
    coords = mod.run(embeddings, cfg)
    runtime = time.time() - start

    cfg_id = db.upsert_config(args.method, cfg, subset, size, runtime)
    db.save_points(args.method, cfg_id, meta, coords)
    print(
        f"✅ {args.method}:{args.config}  "
        f"cfg_id={cfg_id}  pts={len(coords)}  time={runtime:.2f}s"
    )

if __name__ == "__main__":
    main()
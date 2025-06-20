#!/usr/bin/env python3
# viz.py  –  build a 16 384 × 16 384 mosaic from DR projection points
#
# Usage:  python viz.py --method umap --config 42
#
# Requires: pyvips  +  pillow-avif-plugin
#           pip install pyvips pillow-avif-plugin

import argparse, os, math, struct, time, yaml  # added yaml
from pathlib import Path

import pyvips                           # libvips bindings
import db                               # your db.py module
import pillow_avif                      # registers AVIF support in Pillow
from PIL import Image
import numpy as np

# --- Pillow AVIF loader helper ---
def load_thumb(path):
    """Read AVIF with Pillow and return a 3-band pyvips image."""
    pil = Image.open(path).convert("RGB")          # Pillow decodes AVIF
    arr = np.asarray(pil)                          # H×W×3 uint8
    return pyvips.Image.new_from_memory(
        arr.tobytes(), arr.shape[1], arr.shape[0], 3, format="uchar"
    )

# ----------------------------------------------------------------------
# Parameters
CANVAS_W = CANVAS_H = 16_384
THUMB_DIR = Path("assets/thumbnails")
OUT_DIR   = Path("assets/visualizations")          # will hold final AVIF files
MAX_IMAGES_BEFORE_SHRINK = 4_000
TEXT_PAD  = 40                          # px from top/right edge
FONT_SIZE = 60                          # for annotation text
# ----------------------------------------------------------------------

def normalise(points):
    """Map raw (x,y) to integer canvas coords in [0, 16383]."""
    xs = [p["x"] for p in points]
    ys = [p["y"] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    span_x = max_x - min_x or 1.0
    span_y = max_y - min_y or 1.0

    normed = []
    for p in points:
        nx = int(round(((p["x"] - min_x) / span_x) * (CANVAS_W - 1)))
        ny = int(round(((p["y"] - min_y) / span_y) * (CANVAS_H - 1)))
        normed.append({**p, "viz_x": nx, "viz_y": ny})
    return normed

def build_mosaic(normed, scale_factor, out_path, label):
    """Paste every thumbnail onto a huge blank canvas and save."""
    canvas = pyvips.Image.black(CANVAS_W, CANVAS_H, bands=3)

    for p in normed:
        thumb_path = THUMB_DIR / p["filename"]
        if not thumb_path.exists():
            print(f"WARNING: missing thumbnail {thumb_path}")
            continue

        thumb = load_thumb(str(thumb_path))

        if scale_factor < 1.0:                      # shrink if necessary
            thumb = thumb.resize(scale_factor)      # Lanczos, good default

        canvas = canvas.insert(thumb, p["viz_x"], p["viz_y"])

    # ── overlay annotation text in the top-right corner ──────────────────
    text = pyvips.Image.text(label, width=2000, height=FONT_SIZE + 10,
                             dpi=72, font=f"Sans {FONT_SIZE}")\
                        .ifthenelse([255,255,255], [0,0,0])  # white on black
    tx = CANVAS_W - text.width - TEXT_PAD
    ty = TEXT_PAD
    canvas = canvas.insert(text, tx, ty)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── export the Vips canvas to raw RGB bytes ────────────────────
    raw = canvas.write_to_memory()  # raw interleaved RGB, uchar
    arr = np.frombuffer(raw, dtype=np.uint8)
    arr = arr.reshape((CANVAS_H, CANVAS_W, 3))

    # ── convert to PIL and save as AVIF ─────────────────────────────
    img = Image.fromarray(arr, mode="RGB")
    img.save(str(out_path), format="AVIF", quality=80)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--method", help="DR method name (e.g. umap)")
    ap.add_argument("--config", type=int, help="config_id to visualise")
    ap.add_argument("--viz-config", type=str, default="viz_configs.yaml", help="YAML file listing visualizations to generate")
    args = ap.parse_args()

    def run_one(method, config_id):
        method = method.lower()
        # 1️⃣  Fetch raw points + DR parameters
        raw_pts = db.get_projection_points(method, config_id)   # list of tuples
        if not raw_pts:
            print(f"No points for method={method}, config_id={config_id}")
            return
        # convert to dicts expected by normalise()
        points = [
            dict(point_id=r[0], filename=r[1], artist=r[2], x=r[3], y=r[4],
                 method=method, config_id=config_id)
            for r in raw_pts
        ]
        # ── fetch DR hyperparameters and build an annotation string ────────────────
        cfg_params = db.get_dr_config(method, config_id)
        param_items = [
            f"{key}={val}"
            for key, val in cfg_params.items()
            if key != "config_id"
        ]
        params_str = ", ".join(param_items)
        label = f"{method.upper()} (config {config_id}): {params_str}"
        # 2️⃣  Normalise coordinates
        normed = normalise(points)
        # 3️⃣  Decide thumbnail scaling
        scale = 1.0
        if len(normed) > MAX_IMAGES_BEFORE_SHRINK:
            scale = math.sqrt(MAX_IMAGES_BEFORE_SHRINK / len(normed))
            print(f"Shrinking thumbnails by factor {scale:.3f} ...")
        # 4️⃣  Build mosaic
        SCRIPT_DIR = Path(__file__).resolve().parent
        OUT_DIR = SCRIPT_DIR / "assets" / "visualizations"
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        out_file = OUT_DIR / f"{method}_{config_id}_{int(time.time())}.avif"
        build_mosaic(normed, scale, out_file, label)
        print(f"Wrote {out_file}")
        # 5️⃣  Insert into viz_config and viz_points
        point_id_blob = struct.pack(f"{len(points)}I", *(p["point_id"] for p in points))
        viz_id = db.insert_viz_config(method, out_file.name, config_id, point_id_blob)
        db.insert_viz_points(viz_id, normed)
        print(f"Inserted viz_id={viz_id} with {len(normed)} points into DB.")

    # Batch mode: if --viz-config is provided and exists, process all entries
    if args.viz_config and os.path.exists(args.viz_config):
        with open(args.viz_config, "r") as f:
            viz_list = yaml.safe_load(f)
        for entry in viz_list:
            method = entry.get("method")
            config_id = entry.get("config_id")
            if not method or config_id is None:
                print(f"Skipping invalid entry: {entry}")
                continue
            print(f"\n=== Visualizing: method={method}, config_id={config_id} ===")
            run_one(method, config_id)
    elif args.method and args.config is not None:
        run_one(args.method, args.config)
    else:
        print("Specify either --method and --config, or provide a viz config YAML file.")

if __name__ == "__main__":
    main()
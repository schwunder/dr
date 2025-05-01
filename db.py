# db.py
#!/usr/bin/env python3
"""SQLite helpers – one config table per DR method, explicit cols, no JSON."""
import os, sqlite3, numpy as np
from contextlib import contextmanager
from typing import Dict, Any, List

DB_PATH = os.getenv("DR_DB", "art.sqlite")

# Columns relevant to each method (UMAP has 3 new ones)
PARAM_COLS: Dict[str, List[str]] = {
    "umap":     [
        "n_neighbors",
        "min_dist",
        "spread",
        "set_op_mix_ratio",
        "local_connectivity",
        "n_components",
        "metric",
        "random_state"
    ],
    "tsne":     [
        "perplexity",
        "n_components",
        "random_state",
        "learning_rate",
        "n_iter",
        "early_exaggeration",
        "n_iter_without_progress",
        "min_grad_norm",
        "metric",
        "early_exaggeration_iter",
        "theta",
        "negative_gradient_method",
        "initialization",
        "n_jobs"
    ],
    "isomap":   ["n_neighbors", "n_components"],
    "lle":      ["n_neighbors", "n_components", "random_state"],
    "spectral": ["n_neighbors", "n_components", "random_state"],
    "mds":      ["n_components", "random_state"],
    "sammon_random": [
        "n_dims", "n_iter", "tol", "input_type", "random_state"
    ],
    "pca": [
        "n_components",
        "random_state"
    ],
    "ipca": [
        "n_components",
        "batch_size",
        "random_state"
    ],
    "svd": [
        "n_components",
        "random_state"
    ],
    "fa": [
        "n_components",
        "random_state"
    ],
    "ica": [
        "n_components",
        "max_iter",
        "random_state"
    ],
    "agg": [
        "n_clusters"
    ],
    "kpca": [
        "n_components",
        "kernel",
        "gamma",
        "fit_inverse_transform",
        "random_state"
    ],
    "nystroem_pca": [
        "n_components",
        "nystroem_components",
        "kernel",
        "gamma",
        "random_state"
    ],
    "grp": [
        "n_components",
        "eps",
        "random_state"
    ],
    "srp": [
        "n_components",
        "density",
        "eps",
        "random_state"
    ],
    "nmf": [
        "n_components",
        "init",
        "random_state"
    ],
    "dictlearn": [
        "n_components",
        "random_state"
    ],
    "phate": [
        "n_components",
        "knn",
        "decay",
        "t",
        "gamma",
        "random_state"
    ],
    "trimap": [
        "n_dims",
        "n_inliers",
        "n_outliers",
        "n_random",
        "distance",
        "weight_temp",
        "lr",
        "n_iters",
        "random_state",
        "opt_method",
        "apply_pca"
    ],
    "spacemap": [
        "n_components", "n_near_field", "n_middle_field", "d_local", "d_global",
        "eta", "n_epochs", "init", "metric", "verbose", "plot_results", "num_plots"
    ],
    "glle": [
        "method",
        "k_neighbors",
        "max_iterations",
        "n_components",
        "n_generation_of_embedding",
        "verbosity"
    ],
    "paramrepulsor": [
        "n_components",
        "n_neighbors",
        "n_epochs",
        "lr",
        "spread",
        "repulsion_strength",
        "apply_pca",      # stored as INTEGER (0 or 1)
        "init",           # e.g. 'pca', 'random'
        "verbose"         # optional for debugging
    ],
}

@contextmanager
def conn():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()

def _sql_type(col: str) -> str:
    if col in ("metric", "subset_strategy"):
        return "TEXT"
    if col.endswith("_components") or col in (
        "n_neighbors", "random_state", "n_iter",
        "n_iter_without_progress", "subset_size"
    ):
        return "INTEGER"
    return "REAL"

def init_schema() -> None:
    common = "subset_strategy TEXT, subset_size INTEGER, runtime REAL"
    stmts = [
        "PRAGMA foreign_keys=ON;",
        """
        CREATE TABLE IF NOT EXISTS embeddings(
            filename TEXT PRIMARY KEY,
            artist   TEXT,
            embedding BLOB
        );"""
    ]
    # Method-specific config tables
    for m, cols in PARAM_COLS.items():
        cols_sql = ",\n            ".join(f"{c} {_sql_type(c)}" for c in cols)
        stmts.append(f"""
        CREATE TABLE IF NOT EXISTS {m}_configs(
            config_id INTEGER PRIMARY KEY,
            {common},
            {cols_sql}
        );""")
    # Projection points
    stmts.append("""
        CREATE TABLE IF NOT EXISTS projection_points(
            point_id INTEGER PRIMARY KEY,
            method TEXT,
            config_id INTEGER,
            filename TEXT,
            artist TEXT,
            x REAL, y REAL
        );""")
    with conn() as c:
        c.executescript("\n".join(stmts))
    # Add viz_config and viz_points tables and indexes
    with conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS viz_config (
            viz_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            method      TEXT    NOT NULL,
            config_id   INTEGER NOT NULL,
            low_res     TEXT    NOT NULL,
            point_ids   BLOB    NOT NULL,
            created_at  TEXT    DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS viz_points (
            viz_id      INTEGER  NOT NULL,
            point_id    INTEGER  NOT NULL,
            viz_x       INTEGER  NOT NULL,
            viz_y       INTEGER  NOT NULL,
            PRIMARY KEY (viz_id, point_id),
            FOREIGN KEY (viz_id)   REFERENCES viz_config(viz_id),
            FOREIGN KEY (point_id) REFERENCES projection_points(point_id)
        );
        CREATE INDEX IF NOT EXISTS idx_viz_config_method 
            ON viz_config(method, config_id);
        CREATE INDEX IF NOT EXISTS idx_viz_points_viz
            ON viz_points(viz_id);
        """)

def table_counts() -> dict:
    with conn() as c:
        return {
            t[0]: c.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0]
            for t in c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }

def fetch_subset(strategy: str, size: int):
    with conn() as c:
        if strategy == "artist_first5":
            rows = c.execute("""
                WITH ranked AS (
                    SELECT filename, artist, embedding,
                           ROW_NUMBER() OVER (
                             PARTITION BY artist ORDER BY filename
                           ) rn
                    FROM embeddings
                )
                SELECT * FROM ranked WHERE rn <= 5;
            """).fetchall()
        else:
            rows = c.execute(
                "SELECT * FROM embeddings ORDER BY random() LIMIT ?",
                (size,)
            ).fetchall()
    embeds = np.vstack([np.frombuffer(r["embedding"], np.float32) for r in rows])
    meta   = [dict(r) for r in rows]
    return embeds, meta

def _identity_cols(method: str) -> List[str]:
    # treat all hyperparams except random_state as identity
    return [c for c in PARAM_COLS[method] if c != "random_state"]

def upsert_config(
    method: str,
    params: Dict[str, Any],
    strat: str,
    size: int,
    runtime: float
) -> int:
    tbl = f"{method}_configs"
    id_cols = _identity_cols(method)
    with conn() as c:
        where = " AND ".join(
            ["subset_strategy=?", "subset_size=?"] +
            [f"{col}=?" for col in id_cols]
        )
        values = [strat, size] + [params.get(col) for col in id_cols]
        row = c.execute(f"SELECT config_id FROM {tbl} WHERE {where}", values).fetchone()

        if row:
            cfg_id = row["config_id"]
            # update runtime & random_state, then wipe old points
            if "random_state" in PARAM_COLS[method]:
                c.execute(
                    f"UPDATE {tbl} SET runtime=?, random_state=? WHERE config_id=?",
                    (runtime, params.get("random_state"), cfg_id)
                )
            else:
                c.execute(
                    f"UPDATE {tbl} SET runtime=? WHERE config_id=?",
                    (runtime, cfg_id)
                )
            c.execute(
                "DELETE FROM projection_points WHERE method=? AND config_id=?",
                (method, cfg_id)
            )
        else:
            cols = ["subset_strategy", "subset_size", "runtime"] + PARAM_COLS[method]
            placeholders = ",".join("?" for _ in cols)
            vals = [strat, size, runtime] + [params.get(col) for col in PARAM_COLS[method]]
            cur = c.execute(
                f"INSERT INTO {tbl}({','.join(cols)}) VALUES({placeholders})",
                vals
            )
            cfg_id = cur.lastrowid
    return cfg_id

def save_points(method: str, cfg_id: int, meta: list, coords) -> None:
    with conn() as c:
        c.executemany(
            "INSERT INTO projection_points("
            "method, config_id, filename, artist, x, y) VALUES(?,?,?,?,?,?)",
            [
                (method, cfg_id, m["filename"], m["artist"],
                 float(x), float(y))
                for m, (x, y) in zip(meta, coords)
            ]
        )

# Fetches the config parameters for a given method and config_id.
def get_dr_config(method: str, config_id: int) -> dict:
    table = f"{method}_configs"
    with conn() as c:
        row = c.execute(
            f"SELECT * FROM {table} WHERE config_id = ?", (config_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f"No config found for method={method}, config_id={config_id}")
        return dict(row)

# Fetches all projection points (point_id, filename, artist, x, y) for a given method and config_id.
def get_projection_points(method: str, config_id: int) -> list:
    with conn() as c:
        rows = c.execute(
            "SELECT point_id, filename, artist, x, y FROM projection_points WHERE method = ? AND config_id = ?",
            (method, config_id)
        ).fetchall()
        return [tuple(r) for r in rows]  # Each row is (point_id, filename, artist, x, y)

# Inserts a new viz_config row and returns the new viz_id.
def insert_viz_config(method: str, low_res: str, config_id: int, point_ids_blob: bytes) -> int:
    with conn() as c:
        cur = c.execute(
            "INSERT INTO viz_config (method, low_res, config_id, point_ids) VALUES (?, ?, ?, ?)",
            (method, low_res, config_id, point_ids_blob)
        )
        return cur.lastrowid

# Updates the low_res image path for a given viz_id.
def update_viz_config_image(viz_id: int, low_res: str) -> None:
    with conn() as c:
        c.execute(
            "UPDATE viz_config SET low_res = ? WHERE viz_id = ?",
            (low_res, viz_id)
        )

# Fetches all metadata for a given viz_id from viz_config.
def get_viz_config(viz_id: int) -> dict:
    with conn() as c:
        row = c.execute(
            "SELECT * FROM viz_config WHERE viz_id = ?",
            (viz_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f"No viz_config found for viz_id={viz_id}")
        return dict(row)

# Bulk inserts normalized points for a visualization into viz_points.
def insert_viz_points(viz_id: int, points: list) -> None:
    with conn() as c:
        c.executemany(
            "INSERT INTO viz_points (viz_id, point_id, viz_x, viz_y) VALUES (?, ?, ?, ?)",
            [
                (
                    viz_id,
                    p["point_id"],
                    p["viz_x"],
                    p["viz_y"]
                )
                for p in points
            ]
        )

# Fetches all points (with normalized coordinates) for a given viz_id from viz_points.
def get_viz_points(viz_id: int) -> list:
    with conn() as c:
        rows = c.execute(
            "SELECT * FROM viz_points WHERE viz_id = ?",
            (viz_id,)
        ).fetchall()
        return [dict(r) for r in rows]

# auto-init
init_schema()
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
    "sammon": [
        "n", "display", "inputdist", "maxhalves", "maxiter", "tolfun", "init"
    ],
    "sammon_sammon_random": [
        "n", "display", "inputdist", "maxhalves", "maxiter", "tolfun", "init", "random_state"
    ],
    "sammon_random": [
        "n_dims", "n_iter", "tol", "input_type", "random_state"
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

# auto-init
init_schema()
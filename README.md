# DR Pipeline – Explicit Project Guide

## What is this?

A Python pipeline for running and tracking dimensionality reduction (DR) methods (UMAP, t-SNE, Isomap, LLE, Spectral, MDS) on high-dimensional embeddings, storing all results and configs in a SQLite database.

---

## Database Tables

### 1. `embeddings`

| Column    | Type | Notes                       |
| --------- | ---- | --------------------------- |
| filename  | TEXT | PRIMARY KEY, image filename |
| artist    | TEXT |                             |
| embedding | BLOB | 1536-dim float32 bytes      |

### 2. `[method]_configs` (one table per DR method, e.g. `umap_configs`)

| Column                        | Type      | Notes                          |
| ----------------------------- | --------- | ------------------------------ |
| config_id                     | INTEGER   | PRIMARY KEY                    |
| subset_strategy               | TEXT      | e.g. 'random', 'artist_first5' |
| subset_size                   | INTEGER   |                                |
| runtime                       | REAL      | seconds                        |
| ...method-specific columns... | see below |

#### Example: `umap_configs`

| Column             | Type    |
| ------------------ | ------- |
| n_neighbors        | INTEGER |
| min_dist           | REAL    |
| spread             | REAL    |
| set_op_mix_ratio   | REAL    |
| local_connectivity | REAL    |
| n_components       | INTEGER |
| metric             | TEXT    |
| random_state       | INTEGER |

#### Example: `tsne_configs` (openTSNE)

| Column                   | Type    |
| ------------------------ | ------- |
| perplexity               | REAL    |
| n_components             | INTEGER |
| random_state             | INTEGER |
| learning_rate            | REAL    |
| n_iter                   | INTEGER |
| early_exaggeration       | REAL    |
| n_iter_without_progress  | INTEGER |
| min_grad_norm            | REAL    |
| metric                   | TEXT    |
| early_exaggeration_iter  | INTEGER |
| theta                    | REAL    |
| negative_gradient_method | TEXT    |
| initialization           | TEXT    |
| n_jobs                   | INTEGER |

_(Other methods: see `db.py` PARAM_COLS for full list. All parameter names in configs.yaml and db.py match the underlying library APIs. For advanced/optional parameters, add them to both configs.yaml and db.py as needed.)_

### 3. `projection_points`

| Column    | Type    | Notes                           |
| --------- | ------- | ------------------------------- |
| point_id  | INTEGER | PRIMARY KEY                     |
| method    | TEXT    | e.g. 'umap', 'tsne'             |
| config_id | INTEGER | FOREIGN KEY → [method]\_configs |
| filename  | TEXT    |                                 |
| artist    | TEXT    |                                 |
| x         | REAL    | 2D projection coordinate        |
| y         | REAL    | 2D projection coordinate        |

---

## File Roles

- **db.py**: Handles all database schema, connections, and table creation. Defines table columns/types. Auto-initializes schema on import.
- **configs.yaml**: Stores all DR method configurations (hyperparameters, subset strategies, etc.) for each method.
- **methods/**: Contains one Python file per DR method (e.g., `umap.py`, `tsne.py`). Each file defines a `run(embeddings, config)` function that runs the reduction and returns 2D points.
- **run.py**: Main CLI entry point. Loads config, fetches embeddings, runs the selected DR method, saves results to DB.
- **validate.py**: Checks for duplicate filenames in `projection_points` for a given method/config.
- **agent.py**: Utility for status and table counts.

---

## General Workflow

1. **Initialize/Inspect DB**

   ```sh
   python -c "import db; print(db.table_counts())"
   ```

2. **Check Table Counts**

   ```sh
   python agent.py status
   ```

3. **Insert Embeddings** (if needed)

   ```python
   from db import conn
   import numpy as np
   v = np.random.rand(1536).astype(np.float32).tobytes()
   with conn() as c:
       c.execute(
         "INSERT OR IGNORE INTO embeddings(filename, artist, embedding) VALUES(?,?,?)",
         ("example.png", "artistX", v)
       )
   ```

4. **Run a Reduction**

   ```sh
   python run.py --method umap --config fast
   # method: one of umap, tsne, isomap, lle, spectral, mds
   # config: name from configs.yaml
   ```

5. **Inspect Configs**

   ```sh
   sqlite3 art.sqlite "SELECT * FROM umap_configs ORDER BY config_id DESC LIMIT 3;"
   ```

6. **Inspect Projection Points**

   ```sh
   sqlite3 art.sqlite "SELECT * FROM projection_points WHERE method='umap' AND config_id=1 LIMIT 5;"
   ```

7. **Validate Output**
   ```sh
   python validate.py umap 1
   # Output: umap cfg 1: 150/150 unique filenames
   ```

---

## Example Results for All DR Methods

Below are example outputs for each DR method after running the pipeline, including a sample config row, a sample projection point, and validation output.

### UMAP

- Config: | 1 | random | 150 | 2.96 | 10 | 0.1 | 1.0 | 1.0 | 1.0 | 2 | euclidean | 42 |
- Projection: | 1 | umap | 1 | Leonardo_da_Vinci_67.avif | Leonardo da Vinci | 10.477 | 7.693 |
- Validation: `umap cfg 1: 150/150 unique filenames`

### t-SNE

- Config: | 1 | artist_first5 | 250 | 1.17 | 25.0 | 2 | 42 | 200.0 | 500 | 12.0 | 300 | 1.0e-07 | euclidean |
- Projection: | 351 | tsne | 1 | Albrecht_Durer_1.avif | Albrecht Durer | 11.11 | 1.98 |
- Validation: `tsne cfg 1: 250/250 unique filenames`

### Isomap

- Config: | 1 | artist_first5 | 250 | 0.68 | 5 | 2 |
- Projection: | 601 | isomap | 1 | Albrecht_Durer_1.avif | Albrecht Durer | -0.36 | 0.61 |
- Validation: `isomap cfg 1: 250/250 unique filenames`

### LLE

- Config: | 1 | artist_first5 | 250 | 0.85 | 15 | 2 | 42 |
- Projection: | 851 | lle | 1 | Albrecht_Durer_1.avif | Albrecht Durer | 0.0372 | -0.0049 |
- Validation: `lle cfg 1: 250/250 unique filenames`

### MDS

- Config: | 1 | artist_first5 | 250 | 1.31 | 2 | 42 |
- Projection: | 1101 | mds | 1 | Albrecht_Durer_1.avif | Albrecht Durer | 0.1533 | 0.4432 |
- Validation: `mds cfg 1: 250/250 unique filenames`

### Spectral

- Config: | 1 | artist_first5 | 250 | 0.83 | 10 | 2 | 42 |
- Projection: | 1351 | spectral | 1 | Albrecht_Durer_1.avif | Albrecht Durer | -0.0088 | -0.0141 |
- Validation: `spectral cfg 1: 250/250 unique filenames`

---

## How to Extend

- **Add a new DR method:**

  1. Add a new entry to `PARAM_COLS` in `db.py` (columns for the method).
  2. Create a new file in `methods/` with a `run()` function.
  3. Add method configs to `configs.yaml`.
  4. (Re)initialize the DB if new columns are added.

+**Note:** When you add a new entry to `PARAM_COLS` in `db.py`, the schema initialization logic will automatically create a new `[method]_configs` table for your method (e.g., `sammon_configs` for Sammon Mapping) the next time you run or import `db.py`. This makes it easy to extend the pipeline with new DR methods—just update `PARAM_COLS` and the rest of the process will follow the same pattern as existing methods.

- **Add a new hyperparameter:**
  1. Add the column to the relevant method in `db.py`.
  2. Drop and re-init the table if needed.

---

## Troubleshooting

- **Schema errors (e.g., `no such column: ...`):**

  ```sh
  sqlite3 art.sqlite "DROP TABLE IF EXISTS <table>;"
  python -c "import db"
  # Then re-run your reduction
  ```

- **Validation:**  
  `validate.py <method> <config_id>` checks for duplicate filenames in projection points.  
  Output like `umap cfg 1: 150/150 unique filenames` means all points are unique.

---

## Where to find details

- **Full schema:** See `db.py` (PARAM_COLS and CREATE TABLE statements).
- **All configs:** See `configs.yaml`.
- **Method logic:** See `methods/` directory.

- **t-SNE now uses [openTSNE](https://opentsne.readthedocs.io/), and all t-SNE parameters in configs.yaml and db.py match openTSNE's API.**
- **All other methods (UMAP, Isomap, LLE, Spectral, MDS) use parameter names matching their respective library APIs.**

```

```

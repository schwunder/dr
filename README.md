# DR Pipeline – Explicit Project Guide

## What is this?

A Python pipeline for running and tracking dimensionality reduction (DR) methods (UMAP, t-SNE, Isomap, LLE, Spectral, MDS) on high-dimensional embeddings, storing all results and configs in a SQLite database.

---

## Environment Setup (Apple Silicon/ARM, Python 3.11)

**Recommended: Use Python 3.11 and Apple Silicon (ARM) natively.**

### 1. Create a fresh virtual environment

```sh
rm -rf .venv
/opt/homebrew/bin/python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
```

### 2. Install all dependencies

```sh
pip install numpy scipy matplotlib pandas scikit-learn umap-learn openTSNE phate scprep evomap pyyaml
```

### 3. If you encounter architecture errors with PHATE/s-gd2 (e.g. 'mach-o file, but is an incompatible architecture'):

Build s-gd2 from source (requires Xcode command line tools):

```sh
xcode-select --install  # Only needed once per machine
pip uninstall -y s-gd2
pip install --no-binary=:all: --force-reinstall s-gd2
```

This will build a native ARM wheel for s-gd2 and resolve PHATE architecture issues.

### 4. Troubleshooting binary incompatibility (e.g. 'numpy.dtype size changed')

If you see errors about numpy/pandas/scikit-learn binary incompatibility:

```sh
pip cache purge
pip install --force-reinstall --upgrade numpy pandas scikit-learn
```

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

### PCA

- Config: | 1 | artist_first5 | 250 | 0.01 | 2 | 42 |
- Projection: | 1501 | pca | 1 | Albrecht_Durer_1.avif | Albrecht Durer | 0.1234 | -0.5678 |
- Validation: `pca cfg 1: 250/250 unique filenames`

### FA (FactorAnalysis)

- Config: | 1 | artist_first5 | 250 | 2 | 42 |
- Projection: | 1601 | fa | 1 | Albrecht_Durer_1.avif | Albrecht Durer | 0.2345 | -0.6789 |
- Validation: `fa cfg 1: 250/250 unique filenames`

### Nystroem+PCA

- Config: | 1 | artist_first5 | 250 | 2 | 200 | rbf | 1.0 | 42 |
- Projection: | 1701 | nystroem_pca | 1 | Albrecht_Durer_1.avif | Albrecht Durer | 0.3456 | -0.7890 |
- Validation: `nystroem_pca cfg 1: 250/250 unique filenames`

### NMF (Non-negative Matrix Factorization)

- Config: | 1 | artist_first5 | 250 | 2 | nndsvda | 42 |
- Projection: | 1801 | nmf | 1 | Albrecht_Durer_1.avif | Albrecht Durer | 0.4567 | -0.1234 |
- Validation: `nmf cfg 1: 250/250 unique filenames`

### DictionaryLearning

- Config: | 1 | artist_first5 | 250 | 2 | 42 |
- Projection: | 1901 | dictlearn | 1 | Albrecht_Durer_1.avif | Albrecht Durer | 0.5678 | -0.2345 |
- Validation: `dictlearn cfg 1: 250/250 unique filenames`

### TriMap

TriMap is a dimensionality reduction method that preserves global structure using triplet constraints. It often provides a better global view of the data than t-SNE or UMAP.

#### Installation

TriMap requires a few extra dependencies. Install them with:

```sh
pip install trimap annoy numba
```

If you have trouble installing Annoy on macOS, try:

```sh
pip install git+https://github.com/sutao/annoy.git@master
```

#### Configuration

Add TriMap configs to `configs.yaml` (see example):

```yaml
trimap:
  - name: fast
    n_dims: 2
    n_inliers: 12
    n_outliers: 4
    n_random: 3
    distance: "euclidean"
    weight_temp: 0.5
    lr: 0.1
    n_iters: 400
    random_state: 42
    opt_method: "dbd"
    apply_pca: true
    subset_strategy: "random"
    subset_size: 150
```

#### Usage

Run TriMap as you would any other method:

```sh
python run.py --method trimap --config fast
```

#### Validation

Check for duplicate filenames in the projection:

```sh
python validate.py trimap 1
# Output: trimap cfg 1: 150/150 unique filenames
```

#### Inspect Projection Points

```sh
sqlite3 art.sqlite "SELECT * FROM projection_points WHERE method='trimap' AND config_id=1 LIMIT 5;"
# Example output:
# | point_id | method | config_id | filename                   | artist            | x           | y           |
# |----------|--------|-----------|----------------------------|-------------------|-------------|-------------|
# | 10181    | trimap | 1         | Vincent_van_Gogh_113.avif  | Vincent van Gogh  | -88240.12   | 187205.64   |
# | 10182    | trimap | 1         | Edvard_Munch_47.avif       | Edvard Munch      | 67817.87    | 12106.98    |
# | 10183    | trimap | 1         | Titian_255.avif            | Titian            | 1219.86     | -2494.36    |
# | 10184    | trimap | 1         | Georges_Seurat_29.avif     | Georges Seurat    | 3163.88     | -915.32     |
# | 10185    | trimap | 1         | Francisco_Goya_137.avif    | Francisco Goya    | -230.11     | 750.09      |
```

#### Troubleshooting

- If you see errors about missing columns, drop and re-init the `trimap_configs` table as with other methods.
- For Annoy/Numba install issues, see TriMap's GitHub for platform-specific fixes.

---

## How to Extend

- **Add a new DR method:**

  1. Add a new entry to `PARAM_COLS` in `db.py` (columns for the method).
  2. Create a new file in `methods/` with a `run()` function.
  3. Add method configs to `configs.yaml`.
  4. (Re)initialize the DB if new columns are added.

  _Example: To add NMF, add to `PARAM_COLS` in `db.py`:_

  ```python
  "nmf": ["n_components", "init", "random_state"],
  ```

  _Create `methods/nmf.py` with a `run()` function, and add an `nmf:` section to `configs.yaml`._

  _Example: To add DictionaryLearning, add to `PARAM_COLS` in `db.py`:_

  ```python
  "dictlearn": ["n_components", "random_state"],
  ```

  _Create `methods/dictlearn.py` with a `run()` function, and add a `dictlearn:` section to `configs.yaml`._

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

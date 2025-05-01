# DR Pipeline – Explicit Project Guide

## What is this?

A Python pipeline for running and tracking dimensionality reduction (DR) methods (UMAP, t-SNE, Isomap, LLE, Spectral, MDS, cl-MDS, and more) on high-dimensional embeddings, storing all results and configs in a SQLite database.

---

## Environment Setup (Apple Silicon/ARM, Python 3.11)

**Recommended: Use Python 3.11 and Apple Silicon (ARM) natively.**

### 1. Create a fresh virtual environment

```sh
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
```

### 2. Install all dependencies

```sh
pip install -r requirements.txt
```

- The `requirements.txt` is now fully synchronized with the working `.venv` and includes all necessary packages and versions for the pipeline, including advanced DR methods, visualization, and scientific stack. Editable installs and local packages are preserved.

### 3. cl-MDS: Prerequisites, Build, and Integration

#### a. Prerequisites

- Fortran compiler (e.g., `gfortran`)
- Python packages: numpy, scikit-learn, scipy, charset_normalizer (already in requirements.txt)

#### b. Clone and Build cl-MDS

```sh
git clone --recursive http://github.com/mcaroba/cl-MDS.git
cd cl-MDS/
./build_libraries.sh
cd ..
```

- The build script compiles Fortran code and creates Python-callable shared objects.
- If you see encoding errors, ensure `charset_normalizer` is installed in your venv.

#### c. Add cl-MDS to Python Path

```sh
export PYTHONPATH=$(pwd)/cl-MDS:$PYTHONPATH
```

- This ensures your pipeline can import cl-MDS modules at runtime.
- **VSCode/Pylance tip:** Add `"./cl-MDS"` to `python.analysis.extraPaths` in `.vscode/settings.json` for editor import resolution.

#### d. Usage in Pipeline

- cl-MDS is now available as a DR method via `methods/clmds.py`.
- Add or edit cl-MDS configs in `configs.yaml` under the `clmds:` section.
- Run cl-MDS as you would any other method:

```sh
python run.py --method clmds --config default
```

- Results are stored in the database and can be visualized or validated using the existing tools.

#### e. Example cl-MDS Config (in `configs.yaml`)

```yaml
clmds:
  - name: default
    n_clusters: 5
    max_iter: 300
    random_state: 42 # Not used by cl-MDS, but kept for provenance
    subset_strategy: "random"
    subset_size: 150
```

#### f. Troubleshooting cl-MDS and Fortran Builds

- If you see UnicodeDecodeError or encoding issues during build, ensure `charset_normalizer` is installed.
- If you see Fortran or compiler errors, check that `gfortran` is installed and available in your PATH.
- If VSCode/Pylance reports missing imports for `cluster_mds`, ensure `python.analysis.extraPaths` includes `./cl-MDS` and your interpreter is set to `.venv`.

### 4. If you encounter architecture errors with PHATE/s-gd2 (e.g. 'mach-o file, but is an incompatible architecture'):

Build s-gd2 from source (requires Xcode command line tools):

```sh
xcode-select --install  # Only needed once per machine
pip uninstall -y s-gd2
pip install --no-binary=:all: --force-reinstall s-gd2
```

This will build a native ARM wheel for s-gd2 and resolve PHATE architecture issues.

### 5. Troubleshooting binary incompatibility (e.g. 'numpy.dtype size changed')

If you see errors about numpy/pandas/scikit-learn binary incompatibility:

```sh
pip cache purge
pip install --force-reinstall --upgrade numpy pandas scikit-learn
```

### ⚠️ Important: Annoy and High-Dimensional Data

**Annoy (Approximate Nearest Neighbors) is not suitable for high-dimensional data (e.g., 100+ dimensions).**

- In high-dimensional spaces, Annoy often fails to find any meaningful neighbors, returning only the query point itself or none at all.
- This is due to the "curse of dimensionality": all points become nearly equidistant, and tree-based or hashing-based ANN algorithms (like Annoy) cannot distinguish neighbors.
- This can cause methods that rely on Annoy (such as ParamRepulsor, TriMap, or any custom DR using Annoy) to fail or produce empty neighbor lists.

**What to do instead:**

- For high-dimensional data, use brute-force neighbor search (e.g., `sklearn.neighbors.NearestNeighbors` with `algorithm='brute'`).
- For datasets with <10,000 points, brute-force is fast and robust.
- If you must use an approximate method, reduce dimensionality first (e.g., PCA to 20–50D), but brute-force is still recommended for reliability.

**If you see errors like:**

- `ValueError: could not broadcast input array from shape (0,) into shape (N,)` in neighbor search code
- Or, all neighbor queries return empty results

**Check your neighbor search backend and switch to brute-force for high-dimensional data.**

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

### 4. `viz_config`

| Column     | Type    | Notes                                         |
| ---------- | ------- | --------------------------------------------- |
| viz_id     | INTEGER | PRIMARY KEY, unique ID for each visualization |
| method     | TEXT    | DR method name (e.g., 'umap', 'tsne')         |
| config_id  | INTEGER | FOREIGN KEY → [method]\_configs               |
| low_res    | TEXT    | Path to the generated low-res/thumbnail image |
| point_ids  | BLOB    | Serialized list of point_id's (int32 array)   |
| created_at | TEXT    | Timestamp (auto-filled)                       |

- Stores one row per visualization/collage, including provenance and output image path.
- point_ids is a binary blob (int32 array) for fast lookup/export.

### 5. `viz_points`

| Column   | Type    | Notes                                     |
| -------- | ------- | ----------------------------------------- |
| viz_id   | INTEGER | FOREIGN KEY → viz_config(viz_id)          |
| point_id | INTEGER | FOREIGN KEY → projection_points(point_id) |
| viz_x    | INTEGER | Integer pixel coordinate (canvas X)       |
| viz_y    | INTEGER | Integer pixel coordinate (canvas Y)       |

- Stores one row per point in each visualization, with its final canvas coordinates.
- Use viz_id to look up all points for a given visualization.

#### Indexes

- `CREATE INDEX IF NOT EXISTS idx_viz_config_method ON viz_config(method, config_id);`
- `CREATE INDEX IF NOT EXISTS idx_viz_points_viz ON viz_points(viz_id);`

#### Usage in Workflow

- When a visualization is created, insert a row into viz_config and bulk insert rows into viz_points for each point.
- Use viz_config to track provenance, method, config, and output image.
- Use viz_points to quickly retrieve all points and their canvas coordinates for a given visualization.

---

## File Roles

- **db.py**: Handles all database schema, connections, and table creation. Defines table columns/types. Auto-initializes schema on import.
- **configs.yaml**: Stores all DR method configurations (hyperparameters, subset strategies, etc.) for each method.
- **methods/**: Contains all DR method implementations. Most methods are top-level (e.g., `umap.py`, `tsne.py`), but all scikit-learn-based methods are grouped in the `methods/sklearn/` subfolder (e.g., `methods/sklearn/isomap.py`, `methods/sklearn/pca.py`). Each file defines a `run(embeddings, config)` function that runs the reduction and returns 2D points.
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
   # method: one of umap, tsne, isomap, lle, spectral, mds, pca, etc.
   # config: name from configs.yaml
   #
   # Note: All scikit-learn-based methods (e.g., isomap, lle, mds, pca, etc.) are now in the
   # methods/sklearn/ subfolder. The CLI will automatically import them from there.
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

### SpaceMAP

SpaceMAP is a dimensionality reduction method that utilizes local and global intrinsic dimensions to better alleviate the 'crowding problem' analytically. It is now fully integrated into this pipeline and can be used like any other DR method.

#### Usage

Run SpaceMAP as you would any other method:

```sh
python run.py --method spacemap --config fast
```

#### Example Config (in `configs.yaml`)

```yaml
spacemap:
  - name: fast
    n_components: 2
    n_near_field: 21
    n_middle_field: 50
    d_local: 0
    d_global: 4.5
    eta: 0.6
    n_epochs: 200
    init: spectral
    metric: euclidean
    verbose: true
    plot_results: false
    num_plots: 50
    subset_strategy: artist_first5
    subset_size: 250
```

#### Inspect Results

- Config table: `spacemap_configs`
- Projection points: `projection_points` (where `method='spacemap'`)

#### Validation

Check for duplicate filenames in the projection:

```sh
python validate.py spacemap <config_id>
```

#### Troubleshooting

- If you see import errors for FAISS, ensure `faiss-cpu` is installed in your venv.
- If Pylance reports missing imports for FAISS, see the troubleshooting section above for C-extension modules.

#### References

- [SpaceMAP Paper (ICML 2022)](https://proceedings.mlr.press/v162/zu22a.html)
- [Original SpaceMAP repo](https://github.com/zuxinrui/SpaceMAP)

---

## ⚠️ Important Limitations and Warnings

- **Only 2D projections are supported:**
  - All DR configs must use `n_components: 2` (or `n_dims: 2` for methods like TriMap and Sammon). If you set `n_components` or `n_dims` to a value greater than 2, the pipeline will fail with a `ValueError: too many values to unpack (expected 2)`.
  - If you need higher-dimensional projections, you must modify the pipeline to support them.
- **Sammon mapping support:**
  - Only the `sammon_random` method is supported and implemented. sammon and sammon_sammon_random are not implemented and should not be present in configs.yaml or db.py.

---

## How to Extend

- **Add a new DR method:**

  1. Add a new entry to `PARAM_COLS` in `db.py` (columns for the method).
  2. Create a new file in `methods/` with a `run()` function.
  3. Add method configs to `configs.yaml`.
  4. (Re)initialize the DB if new columns are added.

  _Note: Only 2D output is supported. All configs must use `n_components: 2` or `n_dims: 2`._

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

- **2D output only:**

  - If you see `ValueError: too many values to unpack (expected 2)`, check your config for `n_components: 3` or similar. Only 2D output is supported.

- **Sammon mapping:**
  - Only `sammon_random` is supported. If you see `ModuleNotFoundError: No module named 'methods.sammon_sammon_random'`, remove or ignore any configs or schema entries for `sammon` or `sammon_sammon_random`.

---

## Where to find details

- **Full schema:** See `db.py` (PARAM_COLS and CREATE TABLE statements).
- **All configs:** See `configs.yaml`.
- **Method logic:** See `methods/` directory.

- **t-SNE now uses [openTSNE](https://opentsne.readthedocs.io/), and all t-SNE parameters in configs.yaml and db.py match openTSNE's API.**
- **All other methods (UMAP, Isomap, LLE, Spectral, MDS) use parameter names matching their respective library APIs.**

---

## Visualization Workflow

A stand-alone Python script (viz.py) that, given a DR method and config_id, builds a 16 384 × 16 384 AVIF collage of all your thumbnails, records the output and per-point provenance in the database, and annotates the result with the method name and hyperparameters.

**Note:** As of the latest update, `viz.py` writes true AVIF files using Pillow (with the `pillow-avif-plugin`). The mosaic is built using pyvips for efficient image composition, but the final AVIF encoding is handled by Pillow:

- The raw RGB pixel buffer is extracted from the pyvips canvas.
- This buffer is reshaped into a NumPy array and converted to a PIL Image.
- The image is saved as `.avif` using Pillow's AVIF plugin.
- No pyvips `write_to_file` or `heifsave` is used for AVIF output.

The output files are now named like `umap_2_<timestamp>.avif` in `assets/visualizations/`.

### Batch Mode with viz_configs.yaml

You can now specify a list of visualizations to generate in a YAML file (default: viz_configs.yaml):

```yaml
- method: tsne
  config_id: 1
- method: lle
  config_id: 1
- method: umap
  config_id: 2
# Add more as needed (only pairs with projection points in the DB will work)
```

Run all visualizations in the file with:

```sh
python viz.py --viz-config viz_configs.yaml
```

Each entry should specify a DR method and a config_id (from your DR pipeline). The script will process all listed visualizations in sequence. The YAML file must be a flat list of dicts, each with 'method' and 'config_id'.

If you see output like:

    No points for method=tsne, config_id=2

it means there are no projection points in the database for that method/config_id pair. Only use pairs that exist in your DB (see above for how to query them).

### Single Visualization (legacy mode)

You can still run a single visualization as before:

```sh
python viz.py --method umap --config 1
```

### Notes

- The config file must be a flat YAML list of dicts, each with 'method' and 'config_id'.
- If --viz-config is provided and exists, it takes precedence over --method/--config.
- This makes it easy to batch-generate many visualizations in one run.

---

## Neighbor Search Backends: Annoy, HNSWlib, FAISS, and More

### Background & Motivation

- **Annoy** (default in PaCMAP) fails to find real neighbors in high-dimensional (e.g., 256D) continuous data, often returning only trivial/self neighbors. This is due to the curse of dimensionality and Annoy's random-projection tree limitations.
- **FAISS** and **HNSWlib** are robust alternatives that reliably find true nearest neighbors in high-D data, and are now integrated into the pipeline.
- **nmslib** is another option, but may fail to build on ARM/Mac platforms due to C++/SSE/pragma issues.

### How to Use Alternative Backends

- The pipeline now supports selecting the neighbor search backend via the config YAML:
  - `backend: annoy` (default)
  - `backend: hnswlib` (recommended for high-D data)
  - (FAISS integration is available for custom scripts; see below)

#### Example PaCMAP Config Using HNSWlib

```yaml
pacmap:
  - name: hnswlib
    n_components: 2
    n_neighbors: 10
    MN_ratio: 0.5
    FP_ratio: 2.0
    num_iters: 450
    lr: 1.0
    apply_pca: true
    init: "pca"
    random_state: 42
    verbose: false
    subset_strategy: "artist_first5"
    subset_size: 250
    preprocess_pca: 50
    backend: hnswlib
```

### New Utility: `methods/knn_hnswlib.py`

- Provides a simple function to compute k-nearest neighbors using HNSWlib.
- Used internally by the pipeline when `backend: hnswlib` is set.
- Can be used standalone for custom neighbor search needs.

### Troubleshooting & Platform Notes

- **Annoy**: If you see only self-neighbors or trivial results, switch to HNSWlib or FAISS.
- **nmslib**: May not build on ARM/Mac. Try `pip install --no-binary :all: nmslib` or use Docker/conda if needed.
- **FAISS**: Works out of the box for most platforms; see `annoy_debug.py` for example usage.
- **HNSWlib**: Now the recommended backend for high-D data; fast, robust, and easy to install.

### Troubleshooting Flowchart for Neighbor Search

1. **Are you using Annoy and seeing only self-neighbors or empty neighbor lists?**
   - Yes: Try switching to HNSWlib or FAISS (see config example above).
   - No: Proceed to next step.
2. **Is HNSWlib installed and importable?**
   - Yes: Use `backend: hnswlib` in your config.
   - No: Install with `pip install hnswlib`.
3. **Is FAISS available?**
   - Yes: Use FAISS for custom scripts or add as a backend (see below).
   - No: Install with `pip install faiss-cpu` (or `faiss-gpu` for CUDA).
4. **Is nmslib needed?**
   - If you need nmslib and it fails to build, try `pip install --no-binary :all: nmslib`, or use Docker/conda-forge.
5. **Still having issues?**
   - Use brute-force kNN (`sklearn.neighbors.NearestNeighbors(algorithm='brute')`) for up to ~10,000 points.
   - Check your data for NaNs, all-zeros, or duplicates.
   - See `annoy_debug.py` for advanced diagnostics and backend comparison.

### Debugging Steps & Findings (Project Summary)

- **Annoy failures:** Only self-neighbors found in 256D, regardless of n_trees, search_k, or metric. Segfaults with some metrics (manhattan, angular) in high-D.
- **Parameter sweeps:** Lowering n_neighbors, subset_size, and PCA dims did not help Annoy.
- **PCA/Preprocessing:** Reducing to 50D, 20D, 10D, scaling, and normalization did not fix Annoy neighbor search.
- **Brute-force:** Always finds real neighbors, but is slower for large N.
- **FAISS:** Finds real neighbors, robust and fast, works on ARM/Mac and Linux.
- **HNSWlib:** Finds real neighbors, robust and fast, easy to install, works on ARM/Mac and Linux.
- **nmslib:** Fails to build on ARM/Mac due to C++/SSE/pragma errors; may work on Linux/x86.
- **Integration:** Pipeline now supports backend selection via config; HNSWlib is recommended for high-D.

### Backend Tradeoffs Table

| Backend | Speed      | Memory | Reliability (High-D) | Platform Support      | Notes                      |
| ------- | ---------- | ------ | -------------------- | --------------------- | -------------------------- |
| Annoy   | Fast       | Low    | Poor                 | All                   | Fails in high-D, segfaults |
| HNSWlib | Fast       | Medium | Excellent            | All (easy pip)        | Recommended                |
| FAISS   | Fast (CPU) | Medium | Excellent            | Linux, Mac, Windows   | GPU support, robust        |
| nmslib  | Fast       | Medium | Good                 | Linux/x86 (build req) | Build issues on ARM/Mac    |
| Brute   | Slow (N^2) | High   | Perfect              | All                   | Use for N < 10,000         |

### How to Add a New Backend (e.g., FAISS)

1. Create a utility in `methods/` (e.g., `knn_faiss.py`) with a function to compute kNN indices.
2. Patch `pacmap.py` (or your DR method) to accept a `backend` config and call the new utility.
3. Add a config option (e.g., `backend: faiss`) in `configs.yaml`.
4. Test with your data and compare results.

### Platform-Specific Notes

- **Apple Silicon/ARM:**
  - Annoy and HNSWlib work via pip. nmslib may fail to build; try Docker or conda-forge.
  - FAISS works via `faiss-cpu` (no GPU on ARM Macs).
- **Linux/x86:**
  - All backends work; nmslib builds easily.
- **Windows:**
  - Annoy, HNSWlib, and FAISS (CPU) work. nmslib may require WSL or conda.

### Advanced Diagnostics: `annoy_debug.py`

- Use this script to compare neighbor search results across Annoy, HNSWlib, FAISS, brute-force, and more.
- Helps diagnose backend issues, data quirks, and performance tradeoffs.
- Example usage and output included in the script.

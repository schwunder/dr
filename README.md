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

#### Visualization Example

You can visualize the t-SimCNE results using matplotlib. For example, to plot the 2D embedding and color by artist or label:

```python
import sqlite3
import numpy as np
import matplotlib.pyplot as plt

# Load projection points for t-SimCNE config 1
con = sqlite3.connect('art.sqlite')
cur = con.cursor()
rows = cur.execute("""
    SELECT x, y, artist FROM projection_points
    WHERE method='tsimcne' AND config_id=1
""").fetchall()
con.close()

X = np.array([[r[0], r[1]] for r in rows])
artists = [r[2] for r in rows]

# Assign a color to each artist
unique_artists = sorted(set(artists))
color_map = {name: i for i, name in enumerate(unique_artists)}
colors = [color_map[a] for a in artists]

plt.figure(figsize=(8, 8))
plt.scatter(X[:, 0], X[:, 1], c=colors, cmap='tab20', s=10, alpha=0.8)
plt.title('t-SimCNE 2D Visualization (colored by artist)')
plt.xlabel('x')
plt.ylabel('y')
plt.tight_layout()
plt.show()
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

### TSNE-PSO: Particle Swarm Optimized t-SNE

TSNE-PSO is an enhanced version of t-SNE that uses Particle Swarm Optimization (PSO) for the optimization step, offering improved convergence and cluster definition. It supports hybrid optimization, dynamic parameter adaptation, and multiple initialization strategies. See the [tsne-pso PyPI page](https://pypi.org/project/tsne-pso/) for details.

### Installation

```
pip install tsne-pso umap-learn tqdm
```

### Example Config (in `configs.yaml`)

```yaml
tsne_pso:
  - name: default
    n_components: 2
    perplexity: 30.0
    n_particles: 10
    n_iter: 500
    random_state: 42
    inertia_weight: 0.7
    h: 1e-20 # dynamic cognitive weight param
    f: 1e-21 # dynamic social weight param
    use_hybrid: true
    learning_rate: 200.0
    init: "pca"
    metric: "euclidean"
    early_exaggeration: 12.0
    subset_strategy: "artist_first5"
    subset_size: 250
```

### Usage in Pipeline

Run TSNE-PSO as you would any other method:

```sh
python run.py --method tsne_pso --config default
```

- Results are stored in the database and can be visualized or validated using the existing tools.
- All numeric parameters are automatically cast to the correct type (float/int) from YAML.

### Example Results

- Config: | 1 | artist_first5 | 250 | 1.23 | 2 | 30.0 | 10 | 500 | 42 | 0.7 | 1e-20 | 1e-21 | true | 200.0 | pca | euclidean | 12.0 |
- Projection: | 2001 | tsne_pso | 1 | Albrecht_Durer_1.avif | Albrecht Durer | 15.234 | -8.567 |
- Validation: `tsne_pso cfg 1: 250/250 unique filenames`

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

### SLISEMAP & SLIPMAP

SLISEMAP is a supervised dimensionality reduction method that combines local explanations with global visualization. It takes high-dimensional data and predictions (e.g., class labels) from a "black box" model, and produces a 2D embedding where points with similar local explanations are projected nearby. SLIPMAP is a faster variant using prototypes for linear time/memory complexity.

#### Installation

```
pip install slisemap
```

- Requires: numpy, torch, scikit-learn, matplotlib, seaborn (all installed automatically with slisemap)
- [SLISEMAP on PyPI](https://pypi.org/project/slisemap/)
- [Official repo & docs](https://github.com/edahelsinki/slisemap)

#### Example Configs (in `configs.yaml`)

```yaml
slisemap:
  - name: default
    radius: 3.5
    lasso: 0.01
    use_slipmap: false # Set to true to use the faster SLIPMAP variant
    y: null # Will be set automatically by the pipeline
    subset_strategy: "artist_first5"
    subset_size: 250
    # Add more parameters as needed for your use case

  - name: slipmap
    radius: 2.0
    lasso: 0.01
    use_slipmap: true # Use the faster SLIPMAP variant
    y: null # Will be set automatically by the pipeline
    subset_strategy: "artist_first5"
    subset_size: 250
    # Add more parameters as needed for your use case
```

#### Usage in Pipeline

Run SLISEMAP or SLIPMAP as you would any other method:

```sh
python run.py --method slisemap --config default
python run.py --method slisemap --config slipmap  # for the fast variant
```

- The pipeline will automatically encode the `artist` field from your metadata as integer labels and inject it as `y` for SLISEMAP/SLIPMAP.
- The `y` parameter is not stored in the database (only used at runtime).
- Only 2D output is supported (the embedding is always shape `(n_samples, 2)`).
- Results are stored in the database and can be visualized or validated using the existing tools.

#### Implementation Details

- The wrapper is in `methods/slisemap.py` and supports both SLISEMAP and SLIPMAP via the `use_slipmap` flag.
- The pipeline logic for label encoding and config handling is in `run.py`.
- The embedding is extracted from the `_Z` attribute of the SLISEMAP/SLIPMAP object.

#### Troubleshooting

- If you see `ImportError: slisemap is not installed`, run `pip install slisemap` in your virtual environment.
- If you see `ValueError: 'y' (target values) must be provided`, ensure your config uses the pipeline's automatic injection (do not set y manually).
- If you see `ValueError: SLISEMAP output shape ... is not 2D`, check your config and data.

#### References

- [SLISEMAP Paper](https://arxiv.org/abs/2201.04455)
- [SLIPMAP Paper](https://github.com/edahelsinki/slisemap/tree/slipmap_experiments)
- [Official Documentation](https://edahelsinki.github.io/slisemap/slisemap/)

### t-SimCNE (Contrastive Learning Visualization)

t-SimCNE is a contrastive learning-based method for unsupervised 2D visualization of image datasets, as described in [Boehm et al., ICLR 2023](https://arxiv.org/abs/2210.09879). It is now fully integrated into this pipeline and can be used like any other DR method.

#### Installation

```
pip install tsimcne
```

#### Example Config (in `configs.yaml`)

```yaml
tsimcne:
  - name: default
    n_components: 2
    total_epochs: [500, 50, 250] # Will be stored as a comma-separated string in the DB
    random_state: 42
    batch_size: 128 # Optional, for large datasets
    device: "cuda" # Or "cpu"
    subset_strategy: "artist_first5"
    subset_size: 250
```

#### Usage in Pipeline

Run t-SimCNE as you would any other method:

```sh
python run.py --method tsimcne --config default
```

- Results are stored in the database and can be visualized or validated using the existing tools.
- The `total_epochs` parameter is stored as a comma-separated string in the database, but is handled as a list by the method.
- You can set `batch_size` and `device` in the config for large datasets or GPU acceleration.

#### Validation

Check for duplicate filenames in the projection:

```sh
python validate.py tsimcne 1
# Output: tsimcne cfg 1: 250/250 unique filenames
```

#### Inspect Projection Points

```sh
sqlite3 art.sqlite "SELECT * FROM projection_points WHERE method='tsimcne' AND config_id=1 LIMIT 5;"
```

#### References

- [t-SimCNE Paper (ICLR 2023)](https://arxiv.org/abs/2210.09879)
- [Official repo & docs](https://github.com/berenslab/t-simcne)

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
- **Method logic:** See `methods/` subfolder.

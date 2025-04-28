# DR Pipeline - AI Agent Context

This is a dimensionality reduction (DR) pipeline for processing high-dimensional art embeddings stored in a SQLite database. This README provides context for AI agents analyzing this project.

## Current State

- The database (`art.sqlite`) contains:

  - 8,446 art embeddings from 50 artists
  - Each embedding is stored as a BLOB in the `embeddings` table
  - Artist metadata in the `artists` table
  - Schema for all dimensionality reduction methods

- DR methods implemented:

  - UMAP
  - t-SNE
  - Isomap
  - LLE
  - Spectral Embedding
  - MDS

- Two subset strategies are available:
  - `artist_first5`: Retrieves 5 embeddings per artist (250 total for 50 artists), ignores subset_size parameter
  - `random`: Retrieves a random subset of the specified size

## Tools & Commands

- **Status & Analysis**:

  - `python agent.py status` - Shows current state of files, database, and configs
  - `python agent.py suggest` - Suggests DR methods to run next
  - `python validate.py` - Checks database consistency

- **Running Methods**:

  - `python run.py --method umap --config fast` - Run UMAP with fast config
  - `python run.py --method tsne --config fast` - Run t-SNE with fast config
  - `python run.py --method isomap --config basic` - Run Isomap with basic config
  - `python run.py --method lle --config basic` - Run LLE with basic config
  - `python run.py --method spectral --config basic` - Run Spectral with basic config
  - `python run.py --method mds --config basic` - Run MDS with basic config

  **Important**: Run methods individually rather than using the `--all` flag to ensure proper control over each method.

## Subset Strategies

The pipeline supports different strategies for selecting embeddings:

1. **artist_first5**:

   - Always selects the first 5 embeddings from each artist
   - Total of 250 embeddings for 50 artists
   - Ignores the subset_size parameter in configs
   - Ensures balanced representation across all artists

2. **random**:
   - Selects random embeddings from the entire dataset
   - Respects the subset_size parameter in configs
   - May result in uneven distribution across artists
   - Useful for testing with varying dataset sizes

Each unique parameter set creates a single database entry with a unique config_id.

## Configuration Management

This pipeline maintains a clear separation between configuration templates and database records:

### Configuration Templates (configs.yaml)

- Stored in the YAML file as templates for different DR methods
- Each method has named configurations (e.g., "fast", "detail") with specific parameters
- The YAML file is read-only and serves as a blueprint
- Changes to the YAML affect future runs but don't modify existing database records
- **Important**: All parameters should be explicitly defined in the YAML file, even those that might use default values in the underlying algorithms

### Configuration Records (Database)

- Each unique parameter set gets exactly one record in the database
- Database records include all parameters from YAML plus runtime information
- When running a configuration with identical parameters, the existing record is updated
- The `name` field is only used in the YAML file for identification and is not stored in the database
- Uniqueness is enforced by database constraints on the actual parameter values

This approach ensures:

1. Each unique configuration exists only once in the database
2. Running with identical parameters updates the existing record
3. Results are always fresh, as points are recalculated on each run

Run methods individually with appropriate parameters:

```bash
# First run: Creates a new database record
python run.py --method umap --config fast

# Run a different method
python run.py --method tsne --config fast

# Run with different parameters: Creates a new record
python run.py --method umap --config detail
```

## Workflow

A typical workflow for this pipeline:

1. Initialize the database schema: `python db.py`
2. Check available configurations: `python agent.py status`
3. Run a specific method: `python run.py --method umap --config fast`
4. Validate results: `python validate.py umap 1` (where 1 is the config_id)
5. Run additional methods one by one

The pipeline automatically:

- Fetches the appropriate subset of embeddings
- Runs the dimensionality reduction
- Saves results to the database
- Validates the run

## Database Setup

The database requires initialization before running methods:

```bash
python db.py
```

This will:

1. Drop all tables except embeddings and artists
2. Create method-specific config tables with uniqueness constraints
3. Create projection_points table for storing DR results

## Database Schema

- **Decoupled Tables**: Each DR method has its own configuration table with method-specific parameters

  - `umap_configs`: Includes UMAP-specific parameters like min_dist
  - `tsne_configs`: Includes t-SNE-specific parameters like perplexity, learning_rate, n_iter
  - `isomap_configs`: Includes ISOMAP-specific parameters
  - Other method tables similarly customized

- **Common Structure**: All config tables include:

  - `config_id`: Unique identifier
  - `subset_strategy` and `subset_size`: Data selection parameters
  - `runtime_seconds`: Performance tracking

- **The projection_points table** links to configs through config_id:
  - `config_id`: Links to the specific configuration in the appropriate method table
  - `filename`: Original art file name
  - `artist`: Artist name
  - `x, y`: 2D coordinates from the DR algorithms

## Configuration

`configs.yaml` defines parameters for 6 DR methods with various configurations, structured to match the database schema:

- Each method section (UMAP, t-SNE, etc.) contains named configurations
- Each configuration includes a `name` field for identification in the YAML
- Parameters map directly to database column names
- Method-specific parameters are only included in relevant sections
- **Parameter Explicitness**: Always define all parameters explicitly
  - For t-SNE, specify all possible parameters including: `early_exaggeration`, `n_iter_without_progress`, `min_grad_norm`, and `metric`
  - For numeric parameters like `min_grad_norm`, use proper numeric values (e.g., `0.0000001` instead of strings like `"1e-7"`)
  - Use the method implementation file (e.g., `methods/tsne.py`) as a reference for available parameters

## Known Issues

- **Duplicate Points in Config ID 1**:
  - Config ID 1 contains duplicate projection points (500 points for 250 unique files)
  - Each artwork appears exactly twice with different coordinates
  - This affects only the initial run and doesn't occur in subsequent configurations
  - When validating results, check the "unique_files" vs "points_total" counts

## Recent Changes

- Removed name field completely from database schema
- Methods should be run individually rather than using the --all flag
- Database structure simplified to focus on method parameters only
- Modified schema with comprehensive uniqueness constraints
- Updated t-SNE configurations to use explicit parameters for all fields
- Added guidance on explicit parameter definition to avoid NULL values in database

## For AI Agents

When working with this pipeline:

1. Use `python agent.py status` to check the current state
2. If tables are missing, run `python db.py` to initialize them
3. Use `python agent.py suggest` to get recommendations for next runs
4. Each method reduces embeddings to 2D coordinates
5. Remember that configs.yaml contains templates, while the database stores unique configuration records
6. Identical configurations are automatically updated rather than duplicated
7. **Parameter Definition**: Always define all parameters explicitly in configs.yaml, even those that use defaults in the underlying algorithms
8. **Database Integrity**: The database enforces uniqueness constraints on all configuration parameters to prevent duplicates

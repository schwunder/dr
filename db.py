import sqlite3
import json
import numpy as np
import time
import os

# Path to the SQLite database file
DB_PATH = "art.sqlite"

# AGENT_NOTE: Connection function with clear error states
def get_connection():
    """Get SQLite connection with proper settings"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        # Test connection with simple query
        conn.execute("SELECT 1").fetchone()
        return conn
    except sqlite3.Error as e:
        print(f"DB_ERROR: Failed to connect to database: {e}")
        raise

# AGENT_NOTE: Core subsetting functions below
def get_first_n_per_artist(n=5):
    """Get first n embeddings for each artist"""
    conn = get_connection()
    try:
        query = """
        WITH ranked AS (
            SELECT *, ROW_NUMBER() OVER(PARTITION BY artist ORDER BY filename) as rn
            FROM embeddings
        )
        SELECT filename, artist, embedding 
        FROM ranked
        WHERE rn <= ?
        """
        cursor = conn.execute(query, (n,))
        results = [dict(r) for r in cursor.fetchall()]
        
        # Convert embedding strings to numpy arrays
        for r in results:
            r['embedding'] = np.frombuffer(r['embedding'], dtype=np.float32)
        
        print(f"SUBSET_INFO: Retrieved {len(results)} embeddings ({len(set([r['artist'] for r in results]))} artists)")
        return results
    except Exception as e:
        print(f"SUBSET_ERROR: Failed to get first_n_per_artist: {e}")
        raise
    finally:
        conn.close()

def get_all_from_artist(artist_name):
    """Get all embeddings for a specific artist"""
    conn = get_connection()
    try:
        query = "SELECT filename, artist, embedding FROM embeddings WHERE artist = ?"
        cursor = conn.execute(query, (artist_name,))
        results = [dict(r) for r in cursor.fetchall()]
        
        # Convert embedding strings to numpy arrays
        for r in results:
            r['embedding'] = np.frombuffer(r['embedding'], dtype=np.float32)
        
        print(f"SUBSET_INFO: Retrieved {len(results)} embeddings for artist '{artist_name}'")
        return results
    except Exception as e:
        print(f"SUBSET_ERROR: Failed to get all_from_artist: {e}")
        raise
    finally:
        conn.close()

def get_random_subset(n=500, seed=42):
    """Get random subset of embeddings"""
    conn = get_connection()
    try:
        # First count total rows
        count = conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
        
        # Set random seed
        np.random.seed(seed)
        
        # Generate random indices
        n = min(n, count)  # Make sure we don't ask for more than exist
        indices = np.random.choice(count, size=n, replace=False)
        
        # Get rows one by one (inefficient but works with any SQLite setup)
        results = []
        for idx in indices:
            cursor = conn.execute(f"SELECT filename, artist, embedding FROM embeddings LIMIT 1 OFFSET {idx}")
            row = cursor.fetchone()
            if row:
                results.append(dict(row))
        
        # Convert embedding strings to numpy arrays
        for r in results:
            r['embedding'] = np.frombuffer(r['embedding'], dtype=np.float32)
        
        print(f"SUBSET_INFO: Retrieved {len(results)} random embeddings (seed={seed})")
        return results
    except Exception as e:
        print(f"SUBSET_ERROR: Failed to get random subset: {e}")
        raise
    finally:
        conn.close()

# AGENT_NOTE: Main subset dispatcher function
def get_subset(strategy, size=None, seed=42, artist=None):
    """Get a subset based on strategy"""
    print(f"SUBSET_START: Using strategy '{strategy}' (size={size}, seed={seed}, artist={artist})")
    
    if strategy == "artist_all" and artist:
        return get_all_from_artist(artist)
    elif strategy.startswith("artist_first"):
        # Parse number from strategy name if available
        if strategy.startswith("artist_first") and len(strategy) > len("artist_first"):
            try:
                n = int(strategy[len("artist_first"):])
            except ValueError:
                n = size or 5
        else:
            n = size or 5
        return get_first_n_per_artist(n)
    elif strategy == "random":
        return get_random_subset(size or 500, seed)
    else:
        print(f"SUBSET_ERROR: Unknown strategy '{strategy}'")
        raise ValueError(f"Unknown subset strategy: {strategy}")

def get_embeddings_as_array(subset_data):
    """Convert subset data to numpy array of embeddings"""
    if not subset_data:
        print("SUBSET_ERROR: Empty subset data")
        raise ValueError("Cannot convert empty subset to array")
    
    embedding_array = np.vstack([r['embedding'] for r in subset_data])
    print(f"ARRAY_INFO: Converted subset to array shape {embedding_array.shape}")
    return embedding_array

# AGENT_NOTE: Configuration and results persistence functions
def save_config(method, params):
    """Save or update configuration and return config_id
    
    If an identical configuration already exists, it will be updated
    with new runtime information. This is enforced by the UNIQUE constraints
    on the configuration tables.
    
    Args:
        method: The DR method name (umap, tsne, etc.)
        params: Parameters from YAML plus runtime information
                         
    Returns:
        config_id: The database ID for this configuration
    """
    conn = get_connection()
    try:
        # Copy params to avoid modifying the original
        params_copy = params.copy()
        
        # Extract info for logging
        subset_strategy = params_copy.get('subset_strategy', 'artist_first5')
        subset_size = params_copy.get('subset_size', 250)
        runtime = params_copy.get('runtime_seconds')
        
        # Extract the name field for logging but then remove it 
        # since it's not stored in the database
        config_name = params_copy.get('name', 'unnamed')
        if 'name' in params_copy:
            params_copy.pop('name')
        
        # Handle special fields that need JSON serialization
        for key in ['metric_kwds', 'densmap_kwds']:
            if key in params_copy and params_copy[key]:
                params_copy[key] = json.dumps(params_copy[key])
        
        # Define the config table
        config_table = f"{method}_configs"
        
        # First check if this exact configuration already exists
        # We'll build a query that matches all parameter values
        query = f"SELECT config_id FROM {config_table} WHERE "
        conditions = []
        values = []
        
        # Exclude runtime_seconds and timestamps from the uniqueness check
        for key, value in params_copy.items():
            if key not in ['runtime_seconds', 'created_at']:
                conditions.append(f"{key} = ?")
                values.append(value)
        
        query += " AND ".join(conditions)
        
        # Check for existing config
        cursor = conn.execute(query, values)
        result = cursor.fetchone()
        
        if result:
            # Configuration exists - update it
            config_id = result[0]
            
            # Update the runtime and timestamp
            if runtime is not None:
                conn.execute(
                    f"UPDATE {config_table} SET runtime_seconds = ?, created_at = CURRENT_TIMESTAMP WHERE config_id = ?", 
                    (runtime, config_id)
                )
                conn.commit()
            
            print(f"CONFIG_UPDATED: {method} config #{config_id} ({config_name}) updated with new runtime ({runtime:.2f}s)")
            
            # Delete old points
            points_deleted = conn.execute(
                "DELETE FROM projection_points WHERE config_id = ?", 
                (config_id,)
            ).rowcount
            
            conn.commit()
            if points_deleted > 0:
                print(f"POINTS_DELETED: {points_deleted} old points removed for config #{config_id}")
            
            return config_id
            
        else:
            # No existing config - create new one
            fields = []
            placeholders = []
            values = []
            
            for key, value in params_copy.items():
                fields.append(key)
                placeholders.append('?')
                values.append(value)
            
            # Create a new record
            sql = f"INSERT INTO {config_table} ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
            cursor = conn.execute(sql, values)
            config_id = cursor.lastrowid
            conn.commit()
            
            print(f"CONFIG_CREATED: New {method} config #{config_id} from '{config_name}' ({subset_strategy}, size={subset_size})")
            return config_id
            
    except sqlite3.IntegrityError as e:
        # This should only happen if there's a race condition - extremely unlikely
        print(f"CONFIG_INTEGRITY_ERROR: {e} - retrying with SELECT")
        conn.rollback()
        
        # Try again with just a SELECT
        query = f"SELECT config_id FROM {config_table} WHERE "
        conditions = []
        values = []
        
        for key, value in params_copy.items():
            if key not in ['runtime_seconds', 'created_at']:
                conditions.append(f"{key} = ?")
                values.append(value)
        
        query += " AND ".join(conditions)
        
        cursor = conn.execute(query, values)
        result = cursor.fetchone()
        
        if result:
            config_id = result[0]
            print(f"CONFIG_FOUND: Found existing {method} config #{config_id} after integrity error")
            return config_id
        else:
            raise
            
    except Exception as e:
        print(f"CONFIG_ERROR: Failed to save {method} config: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def save_points(config_id, points_data):
    """Save projection points in a transaction"""
    conn = get_connection()
    try:
        conn.execute("BEGIN TRANSACTION")
        
        count = 0
        for point in points_data:
            conn.execute("""
                INSERT INTO projection_points (config_id, filename, artist, x, y)
                VALUES (?, ?, ?, ?, ?)
            """, (
                config_id, 
                point['filename'],
                point['artist'],
                float(point['x']), 
                float(point['y'])
            ))
            count += 1
        
        conn.commit()
        print(f"POINTS_SAVED: {count} points for config #{config_id}")
        return True
    except Exception as e:
        conn.rollback()
        print(f"POINTS_ERROR: Failed to save points for config #{config_id}: {e}")
        return False
    finally:
        conn.close()

def record_runtime(method, config_id, runtime_seconds):
    """Update the config record with the runtime"""
    conn = get_connection()
    try:
        conn.execute(f"UPDATE {method}_configs SET runtime_seconds = ? WHERE config_id = ?", 
                    (runtime_seconds, config_id))
        conn.commit()
        print(f"RUNTIME_RECORDED: {method} config #{config_id} took {runtime_seconds:.2f}s")
    except Exception as e:
        print(f"RUNTIME_ERROR: Failed to record runtime for {method} config #{config_id}: {e}")
        conn.rollback()
    finally:
        conn.close()

# AGENT_NOTE: Database validation and inspection functions
def check_db_tables():
    """Check if all required tables exist"""
    conn = get_connection()
    try:
        # Query for all tables
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [t[0] for t in tables]
        
        # Check for required tables
        required_config_tables = [
            "umap_configs", "tsne_configs", "isomap_configs", 
            "lle_configs", "spectral_configs", "mds_configs"
        ]
        required_data_tables = ["embeddings", "projection_points"]
        
        missing_tables = []
        for table in required_config_tables:
            if table not in table_names:
                missing_tables.append(table)
                
        for table in required_data_tables:
            if table not in table_names:
                missing_tables.append(table)
        
        if missing_tables:
            print(f"DB_WARNING: Missing tables: {', '.join(missing_tables)}")
            return False
        else:
            print("DB_OK: All required tables exist")
            return True
    except Exception as e:
        print(f"DB_ERROR: Failed to check tables: {e}")
        return False
    finally:
        conn.close()

def drop_tables(exclude=None):
    """Drop all tables except those explicitly excluded"""
    if exclude is None:
        exclude = ['embeddings', 'artists']
    
    print("DB_DROP: Dropping tables...")
    conn = get_connection()
    try:
        # Get all tables
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [t[0] for t in tables]
        
        # Filter out excluded tables
        tables_to_drop = [table for table in table_names if table not in exclude]
        
        # Drop each table
        for table in tables_to_drop:
            print(f"DB_DROP: Dropping table {table}")
            conn.execute(f"DROP TABLE IF EXISTS {table}")
        
        conn.commit()
        print(f"DB_DROP: Successfully dropped {len(tables_to_drop)} tables")
        return True
    except Exception as e:
        conn.rollback()
        print(f"DB_DROP_ERROR: Failed to drop tables: {e}")
        return False
    finally:
        conn.close()

def init_projection_points_table():
    """Create projection points table"""
    print("DB_INIT: Creating projection_points table...")
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS projection_points (
                point_id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                artist TEXT NOT NULL, 
                x REAL NOT NULL,
                y REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("DB_INIT: projection_points table created successfully")
        return True
    except Exception as e:
        conn.rollback()
        print(f"DB_INIT_ERROR: Failed to create projection_points table: {e}")
        return False
    finally:
        conn.close()

def init_umap_table():
    """Create UMAP configuration table with uniqueness constraints"""
    print("DB_INIT: Creating umap_configs table...")
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS umap_configs (
                config_id INTEGER PRIMARY KEY AUTOINCREMENT,
                n_neighbors INTEGER,
                n_components INTEGER DEFAULT 2,
                min_dist REAL,
                metric TEXT,
                metric_kwds TEXT,  -- JSON string
                a REAL,
                b REAL,
                random_state INTEGER,
                subset_strategy TEXT,
                subset_size INTEGER,
                runtime_seconds REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Ensure uniqueness of configuration parameters
                UNIQUE(n_neighbors, n_components, min_dist, metric, random_state, subset_strategy, subset_size)
            )
        """)
        conn.commit()
        print("DB_INIT: umap_configs table created successfully")
        return True
    except Exception as e:
        conn.rollback()
        print(f"DB_INIT_ERROR: Failed to create umap_configs table: {e}")
        return False
    finally:
        conn.close()

def init_tsne_table():
    """Create t-SNE configuration table with uniqueness constraints"""
    print("DB_INIT: Creating tsne_configs table...")
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tsne_configs (
                config_id INTEGER PRIMARY KEY AUTOINCREMENT,
                n_components INTEGER DEFAULT 2,
                perplexity REAL,
                early_exaggeration REAL,
                learning_rate REAL,
                n_iter INTEGER,
                n_iter_without_progress INTEGER,
                min_grad_norm REAL,
                metric TEXT,
                random_state INTEGER,
                subset_strategy TEXT,
                subset_size INTEGER,
                runtime_seconds REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Ensure uniqueness of configuration parameters
                UNIQUE(n_components, perplexity, early_exaggeration, learning_rate, n_iter, 
                       n_iter_without_progress, min_grad_norm, metric, random_state, 
                       subset_strategy, subset_size)
            )
        """)
        conn.commit()
        print("DB_INIT: tsne_configs table created successfully")
        return True
    except Exception as e:
        conn.rollback()
        print(f"DB_INIT_ERROR: Failed to create tsne_configs table: {e}")
        return False
    finally:
        conn.close()

def init_isomap_table():
    """Create ISOMAP configuration table with uniqueness constraints"""
    print("DB_INIT: Creating isomap_configs table...")
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS isomap_configs (
                config_id INTEGER PRIMARY KEY AUTOINCREMENT,
                n_neighbors INTEGER,
                n_components INTEGER DEFAULT 2,
                subset_strategy TEXT,
                subset_size INTEGER,
                runtime_seconds REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Ensure uniqueness of configuration parameters
                UNIQUE(n_neighbors, n_components, subset_strategy, subset_size)
            )
        """)
        conn.commit()
        print("DB_INIT: isomap_configs table created successfully")
        return True
    except Exception as e:
        conn.rollback()
        print(f"DB_INIT_ERROR: Failed to create isomap_configs table: {e}")
        return False
    finally:
        conn.close()

def init_lle_table():
    """Create LLE configuration table with uniqueness constraints"""
    print("DB_INIT: Creating lle_configs table...")
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS lle_configs (
                config_id INTEGER PRIMARY KEY AUTOINCREMENT,
                n_neighbors INTEGER,
                n_components INTEGER DEFAULT 2,
                random_state INTEGER,
                subset_strategy TEXT,
                subset_size INTEGER,
                runtime_seconds REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Ensure uniqueness of configuration parameters
                UNIQUE(n_neighbors, n_components, random_state, subset_strategy, subset_size)
            )
        """)
        conn.commit()
        print("DB_INIT: lle_configs table created successfully")
        return True
    except Exception as e:
        conn.rollback()
        print(f"DB_INIT_ERROR: Failed to create lle_configs table: {e}")
        return False
    finally:
        conn.close()

def init_spectral_table():
    """Create Spectral configuration table with uniqueness constraints"""
    print("DB_INIT: Creating spectral_configs table...")
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS spectral_configs (
                config_id INTEGER PRIMARY KEY AUTOINCREMENT,
                n_neighbors INTEGER,
                n_components INTEGER DEFAULT 2,
                random_state INTEGER,
                subset_strategy TEXT,
                subset_size INTEGER,
                runtime_seconds REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Ensure uniqueness of configuration parameters
                UNIQUE(n_neighbors, n_components, random_state, subset_strategy, subset_size)
            )
        """)
        conn.commit()
        print("DB_INIT: spectral_configs table created successfully")
        return True
    except Exception as e:
        conn.rollback()
        print(f"DB_INIT_ERROR: Failed to create spectral_configs table: {e}")
        return False
    finally:
        conn.close()

def init_mds_table():
    """Create MDS configuration table with uniqueness constraints"""
    print("DB_INIT: Creating mds_configs table...")
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mds_configs (
                config_id INTEGER PRIMARY KEY AUTOINCREMENT,
                n_components INTEGER DEFAULT 2,
                random_state INTEGER,
                subset_strategy TEXT,
                subset_size INTEGER,
                runtime_seconds REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Ensure uniqueness of configuration parameters
                UNIQUE(n_components, random_state, subset_strategy, subset_size)
            )
        """)
        conn.commit()
        print("DB_INIT: mds_configs table created successfully")
        return True
    except Exception as e:
        conn.rollback()
        print(f"DB_INIT_ERROR: Failed to create mds_configs table: {e}")
        return False
    finally:
        conn.close()

def init_db():
    """Initialize all method-specific tables"""
    print("DB_INIT: Initializing database schema...")
    
    # Map of initialization functions
    init_functions = {
        "projection_points": init_projection_points_table,
        "umap": init_umap_table,
        "tsne": init_tsne_table,
        "isomap": init_isomap_table,
        "lle": init_lle_table,
        "spectral": init_spectral_table,
        "mds": init_mds_table
    }
    
    # Initialize each table
    success = True
    for name, func in init_functions.items():
        if not func():
            print(f"DB_INIT_ERROR: Failed to initialize {name} table")
            success = False
    
    if success:
        print("DB_INIT: All tables created successfully")
    else:
        print("DB_INIT_WARNING: Some tables failed to initialize")
    
    return success

def count_configs_and_points():
    """Count configurations and projection points in the database"""
    conn = get_connection()
    try:
        # Get all config tables
        config_tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_configs'"
        ).fetchall()
        
        counts = {}
        for table in config_tables:
            method = table[0].replace('_configs', '')
            
            # Count configs
            config_count = conn.execute(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
            
            # Count points for configs from this method
            points_query = f"""
                SELECT COUNT(*) FROM projection_points pp
                JOIN {table[0]} c ON pp.config_id = c.config_id
            """
            try:
                points_count = conn.execute(points_query).fetchone()[0]
            except sqlite3.OperationalError:
                # If no configs or points, set to 0
                points_count = 0
            
            counts[method] = {
                'configs': config_count,
                'points': points_count
            }
        
        # Print summary
        print("DB_COUNTS:")
        for method, count in counts.items():
            print(f"  {method}: {count['configs']} configs, {count['points']} points")
        
        return counts
    except Exception as e:
        print(f"DB_ERROR: Failed to count configs and points: {e}")
        return {}
    finally:
        conn.close()

# Initialize checks on module import
if __name__ != "__main__":
    if os.path.exists(DB_PATH):
        print(f"DB_INFO: Found database at {DB_PATH}")
        check_db_tables()
    else:
        print(f"DB_WARNING: Database file not found at {DB_PATH}")

# Run database initialization when executed directly
if __name__ == "__main__":
    if os.path.exists(DB_PATH):
        print(f"DB_INFO: Found database at {DB_PATH}")
        drop_tables()  # Drop all tables except embeddings and artists
        init_db()      # Create all tables with decoupled schemas
        check_db_tables()
    else:
        print(f"DB_ERROR: Database file not found at {DB_PATH}")

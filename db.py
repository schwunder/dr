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
    """Save configuration and return config_id"""
    conn = get_connection()
    try:
        # Copy params to avoid modifying the original
        params_copy = params.copy()
        
        # Extract subset info for logging
        subset_strategy = params_copy.get('subset_strategy', 'artist_first5')
        subset_size = params_copy.get('subset_size', 250)
        
        # Handle special fields that need JSON serialization
        for key in ['metric_kwds', 'densmap_kwds']:
            if key in params_copy and params_copy[key]:
                params_copy[key] = json.dumps(params_copy[key])
        
        # Extract fields for the config table and construct SQL parts
        config_table = f"{method}_configs"
        fields = []
        placeholders = []
        values = []
        
        for key, value in params_copy.items():
            fields.append(key)
            placeholders.append('?')
            values.append(value)
        
        # Construct and execute SQL
        sql = f"INSERT INTO {config_table} ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
        cursor = conn.execute(sql, values)
        config_id = cursor.lastrowid
        conn.commit()
        
        print(f"CONFIG_SAVED: {method} config #{config_id} (strategy={subset_strategy}, size={subset_size})")
        return config_id
    except Exception as e:
        print(f"CONFIG_ERROR: Failed to save {method} config: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def save_points(config_id, method, points_data):
    """Save projection points in a transaction"""
    conn = get_connection()
    try:
        conn.execute("BEGIN TRANSACTION")
        
        count = 0
        for point in points_data:
            conn.execute("""
                INSERT INTO projection_points (config_id, method, filename, artist, x, y)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                config_id, 
                method,
                point['filename'],
                point['artist'],
                float(point['x']), 
                float(point['y'])
            ))
            count += 1
        
        conn.commit()
        print(f"POINTS_SAVED: {count} points for {method} config #{config_id}")
        return True
    except Exception as e:
        conn.rollback()
        print(f"POINTS_ERROR: Failed to save points for {method} config #{config_id}: {e}")
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
            
            # Count points for this method
            points_count = conn.execute(
                "SELECT COUNT(*) FROM projection_points WHERE method = ?", 
                (method,)
            ).fetchone()[0]
            
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

#!/usr/bin/env python3
"""
Validation script for DR results.
Provides structured output for agent parsing.
"""
import sqlite3
import sys
import json
import traceback

def validate_run(method, config_id):
    """Validates that:
    1. Config entry exists with all hyperparams
    2. Points exist with x,y coordinates for each filename
    """
    print(f"VALIDATE_START: {method} config #{config_id}")
    
    conn = sqlite3.connect("art.sqlite")
    conn.row_factory = sqlite3.Row
    
    try:
        # Check config has all hyperparams
        config_table = f"{method}_configs"
        config = conn.execute(f"SELECT * FROM {config_table} WHERE config_id = ?", (config_id,)).fetchone()
        if not config:
            print(f"VALIDATE_ERROR: Missing config {method}[{config_id}]")
            return False
        
        # Get expected columns for this config table
        cursor = conn.execute(f"PRAGMA table_info({config_table})")
        columns = [row['name'] for row in cursor.fetchall()]
        
        # Check if any expected columns are NULL in the config
        null_columns = []
        for col in columns:
            if col != 'config_id' and config[col] is None:
                # Skip columns that are allowed to be NULL
                if col not in ['a', 'b', 'n_epochs', 'disconnection_distance', 'runtime_seconds', 
                              'created_at', 'target_n_neighbors', 'metric_kwds', 'densmap_kwds']:
                    null_columns.append(col)
        
        if null_columns:
            print(f"VALIDATE_WARNING: Config has NULL values for columns: {', '.join(null_columns)}")
            
        # Check points have x,y coordinates for filenames
        points_query = """
            SELECT COUNT(*) as total, 
                   SUM(CASE WHEN x IS NULL OR y IS NULL THEN 1 ELSE 0 END) as missing_coords,
                   COUNT(DISTINCT filename) as unique_files
            FROM projection_points 
            WHERE config_id = ?
        """
        points = conn.execute(points_query, (config_id,)).fetchone()
        
        # Get summary of points by artist
        artist_query = """
            SELECT artist, COUNT(*) as count
            FROM projection_points
            WHERE config_id = ?
            GROUP BY artist
        """
        artist_counts = conn.execute(artist_query, (config_id,)).fetchall()
        artist_summary = {row['artist']: row['count'] for row in artist_counts}
        
        validation_result = {
            "method": method,
            "config_id": config_id,
            "config_exists": config is not None,
            "null_columns": null_columns,
            "points_total": points['total'],
            "unique_files": points['unique_files'],
            "missing_coords": points['missing_coords'],
            "artists": len(artist_summary),
            "artist_counts": artist_summary,
            "success": config is not None and points['total'] > 0 and points['missing_coords'] == 0
        }
        
        # Print machine-readable result
        print(f"VALIDATE_RESULT: {json.dumps(validation_result)}")
        
        # Print human-readable summary
        print(f"VALIDATE_SUMMARY: {method}[{config_id}] → {points['total']} points ({points['unique_files']} files)")
        
        if points['missing_coords'] > 0:
            print(f"VALIDATE_ERROR: {points['missing_coords']} points missing coordinates")
            return False
            
        if points['total'] == 0:
            print(f"VALIDATE_ERROR: No points found for {method}[{config_id}]")
            return False
        
        print(f"VALIDATE_SUCCESS: {method}[{config_id}] validation passed")
        return True
        
    except Exception as e:
        print(f"VALIDATE_ERROR: {str(e)}")
        print(traceback.format_exc())
        return False
    finally:
        conn.close()

def check_db_consistency():
    """Check overall database consistency"""
    print("VALIDATE_DB_START: Checking database consistency")
    
    conn = sqlite3.connect("art.sqlite")
    conn.row_factory = sqlite3.Row
    
    try:
        # Check embeddings table
        try:
            embeddings_count = conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
            print(f"VALIDATE_DB: Found {embeddings_count} embeddings")
        except sqlite3.OperationalError:
            print("VALIDATE_DB_ERROR: embeddings table not found or has wrong schema")
            return False
        
        # Check config tables
        config_tables = []
        for method in ['umap', 'tsne', 'isomap', 'lle', 'spectral', 'mds']:
            try:
                config_count = conn.execute(f"SELECT COUNT(*) FROM {method}_configs").fetchone()[0]
                config_tables.append((method, config_count))
            except sqlite3.OperationalError:
                print(f"VALIDATE_DB_WARNING: {method}_configs table not found")
        
        for method, count in config_tables:
            print(f"VALIDATE_DB: {method}_configs has {count} configurations")
        
        # Check projection_points table
        try:
            # Count points per method
            points_query = """
                SELECT m.name as method_table, COUNT(pp.point_id) as count
                FROM projection_points pp
                JOIN (
                    SELECT 'umap_configs' as name, config_id FROM umap_configs
                    UNION SELECT 'tsne_configs' as name, config_id FROM tsne_configs
                    UNION SELECT 'isomap_configs' as name, config_id FROM isomap_configs
                    UNION SELECT 'lle_configs' as name, config_id FROM lle_configs
                    UNION SELECT 'spectral_configs' as name, config_id FROM spectral_configs
                    UNION SELECT 'mds_configs' as name, config_id FROM mds_configs
                ) m ON pp.config_id = m.config_id
                GROUP BY m.name
            """
            points_counts = conn.execute(points_query).fetchall()
            
            for row in points_counts:
                method = row['method_table'].replace('_configs', '')
                print(f"VALIDATE_DB: {method} has {row['count']} projection points")
                
            # Check for orphaned points
            orphaned_query = """
                SELECT pp.config_id, COUNT(*) as count
                FROM projection_points pp
                LEFT JOIN (
                    SELECT 'umap' as method, config_id FROM umap_configs
                    UNION SELECT 'tsne' as method, config_id FROM tsne_configs
                    UNION SELECT 'isomap' as method, config_id FROM isomap_configs
                    UNION SELECT 'lle' as method, config_id FROM lle_configs
                    UNION SELECT 'spectral' as method, config_id FROM spectral_configs
                    UNION SELECT 'mds' as method, config_id FROM mds_configs
                ) configs ON pp.config_id = configs.config_id
                WHERE configs.config_id IS NULL
                GROUP BY pp.config_id
            """
            orphaned = conn.execute(orphaned_query).fetchall()
            
            for row in orphaned:
                print(f"VALIDATE_DB_ERROR: {row['count']} orphaned points for config_id {row['config_id']}")
            
            return len(orphaned) == 0
            
        except sqlite3.OperationalError as e:
            print(f"VALIDATE_DB_ERROR: projection_points check failed: {e}")
            return False
            
    except Exception as e:
        print(f"VALIDATE_DB_ERROR: {str(e)}")
        print(traceback.format_exc())
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No args - check overall DB consistency
        success = check_db_consistency()
    else:
        # Validate specific run
        method, config_id = sys.argv[1], int(sys.argv[2])
        success = validate_run(method, config_id)
    
    sys.exit(0 if success else 1)

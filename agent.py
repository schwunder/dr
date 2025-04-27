#!/usr/bin/env python3
"""
Helper utilities for AI agents working with the DR pipeline.
This file provides structured information for agents to understand the project state.
"""
import os
import sqlite3
import sys
import json
import importlib
import yaml
from collections import defaultdict

def get_project_status():
    """Get overall project status for agent analysis"""
    status = {
        "files": check_files(),
        "database": check_database(),
        "configs": load_configs(),
        "runs": get_run_status()
    }
    
    print(json.dumps(status, indent=2))
    return status

def check_files():
    """Check presence of expected files"""
    expected_files = [
        "db.py",
        "run.py",
        "validate.py",
        "agent_helper.py",
        "configs/configs.yaml",
        "methods/umap.py",
        "methods/tsne.py",
        "methods/isomap.py",
        "methods/lle.py",
        "methods/spectral.py",
        "methods/mds.py"
    ]
    
    file_status = {}
    for file_path in expected_files:
        file_status[file_path] = os.path.exists(file_path)
    
    return file_status

def check_database():
    """Check database status"""
    try:
        import db
        db_path = db.DB_PATH
        
        # Check if DB file exists
        db_exists = os.path.exists(db_path)
        
        if not db_exists:
            return {
                "exists": False,
                "message": f"Database file not found at {db_path}"
            }
        
        # Test connection
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Count records
            table_counts = {}
            for table in tables:
                count_query = f"SELECT COUNT(*) FROM {table}"
                try:
                    cursor.execute(count_query)
                    count = cursor.fetchone()[0]
                    table_counts[table] = count
                except sqlite3.Error:
                    table_counts[table] = "error"
            
            return {
                "exists": True,
                "tables": tables,
                "record_counts": table_counts,
                "path": db_path
            }
            
        except sqlite3.Error as e:
            return {
                "exists": True,
                "error": str(e),
                "path": db_path
            }
            
    except ImportError:
        return {
            "exists": False,
            "error": "Could not import db.py"
        }

def load_configs():
    """Load DR configurations"""
    config_path = "configs/configs.yaml"
    
    if not os.path.exists(config_path):
        return {
            "exists": False,
            "message": f"Config file not found at {config_path}"
        }
    
    try:
        with open(config_path, 'r') as f:
            configs = yaml.safe_load(f)
            
        # Count configs per method
        method_counts = {method: len(configs[method]) for method in configs}
        
        return {
            "exists": True,
            "methods": list(configs.keys()),
            "config_counts": method_counts,
            "configs": configs
        }
    except Exception as e:
        return {
            "exists": True,
            "error": str(e)
        }

def get_run_status():
    """Get status of DR runs in the database"""
    try:
        import db
        db_path = db.DB_PATH
        
        if not os.path.exists(db_path):
            return {
                "error": "Database file not found"
            }
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Get methods with config and point counts
        methods = ['umap', 'tsne', 'isomap', 'lle', 'spectral', 'mds']
        method_status = {}
        
        for method in methods:
            config_table = f"{method}_configs"
            
            try:
                # Count configs
                configs = conn.execute(f"SELECT config_id, subset_strategy, subset_size, runtime_seconds FROM {config_table}").fetchall()
                
                # Get points for each config
                config_points = defaultdict(int)
                for config in configs:
                    config_id = config['config_id']
                    points_count = conn.execute(
                        "SELECT COUNT(*) FROM projection_points WHERE method = ? AND config_id = ?", 
                        (method, config_id)
                    ).fetchone()[0]
                    config_points[config_id] = points_count
                
                # Build status
                method_status[method] = {
                    "configs": len(configs),
                    "total_points": sum(config_points.values()),
                    "details": [{
                        "config_id": c['config_id'],
                        "subset_strategy": c['subset_strategy'],
                        "subset_size": c['subset_size'],
                        "runtime_seconds": c['runtime_seconds'],
                        "points": config_points[c['config_id']]
                    } for c in configs]
                }
                
            except sqlite3.Error as e:
                method_status[method] = {
                    "error": str(e)
                }
        
        return method_status
        
    except Exception as e:
        return {
            "error": str(e)
        }

def suggest_next_run():
    """Suggest the next DR run to execute based on current state"""
    # Get configs
    configs = load_configs()
    if 'error' in configs:
        return {
            "error": "Could not load configs"
        }
    
    # Get current run status
    runs = get_run_status()
    if 'error' in runs:
        return {
            "error": "Could not get run status"
        }
    
    # Find methods with missing runs
    suggestions = []
    
    for method, method_configs in configs['configs'].items():
        # Skip if method has an error
        if method in runs and 'error' in runs[method]:
            continue
            
        # Get completed config IDs
        completed_configs = set()
        if method in runs:
            for detail in runs[method].get('details', []):
                if detail.get('points', 0) > 0:
                    completed_configs.add(detail.get('config_id'))
        
        # Find configs to run
        for config_name in method_configs:
            # Check if this is a new config or has no points
            is_new = True
            for detail in runs.get(method, {}).get('details', []):
                if detail.get('subset_strategy') == method_configs[config_name].get('subset_strategy') and \
                   detail.get('subset_size') == method_configs[config_name].get('subset_size'):
                    is_new = False
                    break
            
            if is_new:
                suggestions.append({
                    "method": method,
                    "config": config_name,
                    "reason": "New configuration"
                })
    
    # Handle empty case - look for fast runs
    if not suggestions:
        for method in ['umap', 'isomap']:
            if method in configs['configs']:
                fast_configs = [c for c in configs['configs'][method] 
                               if c.lower().startswith('fast') or c.lower() == 'basic']
                if fast_configs:
                    suggestions.append({
                        "method": method,
                        "config": fast_configs[0],
                        "reason": "No new configs, suggesting fast run"
                    })
    
    return {
        "suggestions": suggestions
    }

if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "status"
    
    if command == "status":
        get_project_status()
    elif command == "suggest":
        result = suggest_next_run()
        print(json.dumps(result, indent=2))
    else:
        print(f"Unknown command: {command}")
        print("Available commands: status, suggest")

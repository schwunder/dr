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
        "configs.yaml",
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
    config_path = "configs.yaml"
    
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
                configs = conn.execute(f"SELECT config_id, name, subset_strategy, subset_size, runtime_seconds FROM {config_table}").fetchall()
                
                # Get points for each config
                config_points = defaultdict(int)
                for config in configs:
                    config_id = config['config_id']
                    points_count = conn.execute(
                        "SELECT COUNT(*) FROM projection_points WHERE config_id = ?", 
                        (config_id,)
                    ).fetchone()[0]
                    config_points[config_id] = points_count
                
                # Build status
                method_status[method] = {
                    "configs": len(configs),
                    "total_points": sum(config_points.values()),
                    "details": [{
                        "config_id": c['config_id'],
                        "name": c['name'],
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
    
    # Find methods that haven't been run yet
    methods_not_run = []
    for method in configs['configs'].keys():
        if method not in runs or runs[method].get('total_points', 0) == 0:
            methods_not_run.append(method)
    
    # Prioritize methods that haven't been run yet
    suggestions = []
    
    # First suggest methods that haven't been run at all
    for method in methods_not_run:
        for config in configs['configs'][method]:
            config_name = config.get('name')
            if config_name and (config_name.lower() == 'fast' or config_name.lower() == 'basic'):
                suggestions.append({
                    "method": method,
                    "config": config_name,
                    "reason": f"Method {method} has not been run yet",
                    "priority": "high"
                })
                break
        else:
            # If no 'fast' or 'basic' config, suggest the first one
            if configs['configs'][method]:
                config_name = configs['configs'][method][0].get('name')
                if config_name:
                    suggestions.append({
                        "method": method,
                        "config": config_name,
                        "reason": f"Method {method} has not been run yet",
                        "priority": "high"
                    })
    
    # Then suggest new configurations for methods that have been run
    for method, method_configs in configs['configs'].items():
        # Skip methods that haven't been run (already handled above)
        if method in methods_not_run:
            continue
            
        # Skip if method has an error
        if method in runs and 'error' in runs[method]:
            continue
            
        # Get completed config names
        completed_config_names = set()
        if method in runs:
            for detail in runs[method].get('details', []):
                if detail.get('points', 0) > 0:
                    completed_config_names.add(detail.get('name', ''))
        
        # Find configs to run
        for config in method_configs:
            config_name = config.get('name')
            if not config_name or config_name in completed_config_names:
                continue
                
            suggestions.append({
                "method": method,
                "config": config_name,
                "reason": f"New configuration for {method}",
                "priority": "medium"
            })
    
    # If no suggestions, suggest re-running a different subset strategy
    if not suggestions:
        # Look for fast/basic configs with a different subset strategy
        for method in ['tsne', 'umap', 'isomap']:
            if method in configs['configs']:
                for config in configs['configs'][method]:
                    config_name = config.get('name', '')
                    if config_name.lower() == 'fast' or config_name.lower() == 'basic':
                        # Modify the config to use a different subset strategy
                        suggestions.append({
                            "method": method,
                            "config": config_name,
                            "reason": "Retry with random subset strategy",
                            "priority": "low",
                            "modify": {
                                "subset_strategy": "random",
                                "subset_size": 300
                            }
                        })
                        break
    
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

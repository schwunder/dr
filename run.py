#!/usr/bin/env python3
import argparse
import importlib
import os
import time
import yaml
import sys
import traceback
import json
from contextlib import redirect_stdout, redirect_stderr
import io

# Import database functions
import db

# AGENT_NOTE: Global variables for tracking state
CURRENT_METHOD = None
CURRENT_CONFIG = None
CURRENT_CONFIG_ID = None
EXECUTION_STATUS = "idle"  # idle, running, success, error

def load_configs():
    """Load all method configs from YAML"""
    config_path = os.path.join(os.path.dirname(__file__), 'configs', 'configs.yaml')
    try:
        with open(config_path, 'r') as f:
            configs = yaml.safe_load(f)
            print(f"CONFIG_LOADED: Read {len(configs)} methods from {config_path}")
            return configs
    except Exception as e:
        print(f"CONFIG_ERROR: Failed to load configs from {config_path}: {e}")
        return {}

def print_status(status_type, message):
    """Print status messages with consistent formatting for agent parsing"""
    print(f"STATUS_{status_type.upper()}: {message}")

def capture_output(func, *args, **kwargs):
    """Capture stdout and stderr from a function call"""
    stdout = io.StringIO()
    stderr = io.StringIO()
    result = None
    error = None
    
    try:
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = func(*args, **kwargs)
        return {
            'result': result,
            'stdout': stdout.getvalue(),
            'stderr': stderr.getvalue(),
            'success': True
        }
    except Exception as e:
        return {
            'result': None,
            'stdout': stdout.getvalue(),
            'stderr': stderr.getvalue(),
            'error': str(e),
            'traceback': traceback.format_exc(),
            'success': False
        }

def run_dr_method(method, config_name):
    """Run a specific DR method with the named config"""
    global CURRENT_METHOD, CURRENT_CONFIG, CURRENT_CONFIG_ID, EXECUTION_STATUS
    
    CURRENT_METHOD = method
    CURRENT_CONFIG = config_name
    EXECUTION_STATUS = "running"
    
    print("\n" + "="*80)
    print_status("start", f"Running {method} with config '{config_name}'")
    print("="*80)
    
    # Load configs
    all_configs = load_configs()
    
    if method not in all_configs:
        print_status("error", f"Method '{method}' not found in configs")
        EXECUTION_STATUS = "error"
        return False
    
    if config_name not in all_configs[method]:
        print_status("error", f"Config '{config_name}' not found for method '{method}'")
        EXECUTION_STATUS = "error"
        return False
    
    # Get config params
    config = all_configs[method][config_name]
    print_status("config", json.dumps(config))
    
    # Get subset data
    subset_strategy = config.get('subset_strategy', 'artist_first5')
    subset_size = config.get('subset_size', 250)
    seed = config.get('random_state', 42)
    
    try:
        print_status("subset", f"Fetching {subset_strategy} (size: {subset_size}, seed: {seed})")
        subset_data = db.get_subset(subset_strategy, subset_size, seed)
        print_status("subset", f"Fetched {len(subset_data)} embeddings")
        
        # Sanity check on embeddings
        if len(subset_data) == 0:
            print_status("error", "Empty subset data")
            EXECUTION_STATUS = "error"
            return False
            
        first_embedding = subset_data[0]['embedding']
        print_status("debug", f"First embedding shape: {first_embedding.shape}")
        
        # Import the DR method module
        try:
            dr_module = importlib.import_module(f"methods.{method}")
            print_status("import", f"Successfully imported {method} module")
        except ImportError as e:
            print_status("error", f"Could not import module for method '{method}': {e}")
            EXECUTION_STATUS = "error"
            return False
        
        # Run the DR method
        print_status("execute", f"Starting {method} dimensionality reduction...")
        start_time = time.time()
        
        # Get embeddings as array for the DR method
        try:
            embeddings = db.get_embeddings_as_array(subset_data)
        except Exception as e:
            print_status("error", f"Failed to prepare embeddings array: {e}")
            print(traceback.format_exc())
            EXECUTION_STATUS = "error"
            return False
        
        # Run the DR method with output capture
        print_status("execute", f"Running {method} on {embeddings.shape[0]} embeddings...")
        dr_result = capture_output(dr_module.run, embeddings, config)
        
        if not dr_result['success']:
            print_status("error", f"DR method failed: {dr_result['error']}")
            print(dr_result['traceback'])
            EXECUTION_STATUS = "error"
            return False
        
        result_coords = dr_result['result']
        
        # Prepare points data
        print_status("process", "Preparing point data...")
        points_data = []
        for i, coords in enumerate(result_coords):
            if i < len(subset_data):  # Safety check
                points_data.append({
                    'filename': subset_data[i]['filename'],
                    'artist': subset_data[i]['artist'],
                    'x': coords[0],
                    'y': coords[1]
                })
        
        # Calculate runtime
        runtime = time.time() - start_time
        print_status("timing", f"Completed in {runtime:.2f} seconds")
        
        # Save config
        print_status("save", f"Saving {method} configuration...")
        config_with_runtime = config.copy()
        config_with_runtime['runtime_seconds'] = runtime
        config_id = db.save_config(method, config_with_runtime)
        CURRENT_CONFIG_ID = config_id
        print_status("save", f"Saved {method} config with ID: {config_id}")
        
        # Save points
        print_status("save", f"Saving {len(points_data)} projected points...")
        success = db.save_points(config_id, method, points_data)
        if success:
            print_status("save", f"Saved {len(points_data)} points to database")
        else:
            print_status("error", "Failed to save points")
            EXECUTION_STATUS = "error"
            return False
        
        # Validate the run
        print_status("validate", f"Validating {method} run with config #{config_id}...")
        os.system(f"python validate.py {method} {config_id}")
        
        print_status("complete", f"Successfully completed {method} with config '{config_name}'")
        EXECUTION_STATUS = "success"
        return config_id
    
    except Exception as e:
        print_status("error", str(e))
        print(traceback.format_exc())
        EXECUTION_STATUS = "error"
        return False

def run_all():
    """Run one config from each method"""
    all_configs = load_configs()
    results = {}
    
    for method in all_configs:
        # Take the first config for each method
        config_name = next(iter(all_configs[method].keys()))
        config_id = run_dr_method(method, config_name)
        results[method] = config_id
    
    print("\n" + "="*80)
    print_status("summary", "Run complete")
    print("="*80)
    
    for method, config_id in results.items():
        status = "SUCCESS" if config_id else "FAILED"
        print(f"{method:<10}: {status} {config_id if config_id else ''}")
    
    return all(results.values())

def get_method_status():
    """Get current execution status"""
    return {
        "method": CURRENT_METHOD,
        "config": CURRENT_CONFIG,
        "config_id": CURRENT_CONFIG_ID,
        "status": EXECUTION_STATUS
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run dimensionality reduction methods")
    parser.add_argument("--method", help="DR method to run (umap, tsne, etc.)")
    parser.add_argument("--config", help="Config name to use")
    parser.add_argument("--all", action="store_true", help="Run one config from each method")
    parser.add_argument("--status", action="store_true", help="Show current execution status")
    
    args = parser.parse_args()
    
    if args.status:
        status = get_method_status()
        print(json.dumps(status, indent=2))
    elif args.all:
        success = run_all()
        sys.exit(0 if success else 1)
    elif args.method and args.config:
        success = run_dr_method(args.method, args.config)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()

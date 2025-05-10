#!/usr/bin/env python3
import argparse
import sys
# import your own modules here…

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--method", required=True)
    p.add_argument("--config", required=True)
    args = p.parse_args()

    # Call into your existing code, e.g.:
    from run import run_method
    success = run_method(args.method, args.config)
    if not success:
        sys.exit(1)

    print("Finished", args.method, args.config)

if __name__ == "__main__":
    main()
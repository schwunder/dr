# agent.py
#!/usr/bin/env python3
"""Lightweight helper for IDE: quick DB status."""
import sys, db

def status() -> None:
    for tbl, n in db.table_counts().items():
        print(f"{tbl:25} {n}")

if __name__ == "__main__":
    status()
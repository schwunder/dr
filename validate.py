# validate.py
#!/usr/bin/env python3
"""Quick duplicate-point check for a given run."""
import sys, db

def dup_report(method: str, cfg_id: int):
    with db.conn() as c:
        rows = c.execute(
            "SELECT filename FROM projection_points WHERE method=? AND config_id=?",
            (method, cfg_id)
        ).fetchall()
    total  = len(rows)
    unique = len({r["filename"] for r in rows})
    print(f"{method} cfg {cfg_id}: {unique}/{total} unique filenames")

if __name__ == "__main__":
    if len(sys.argv) != 3 or not sys.argv[2].isdigit():
        sys.exit("Usage: validate.py <method> <config_id>")
    dup_report(sys.argv[1], int(sys.argv[2]))
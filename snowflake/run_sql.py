"""
Run a .sql file against Snowflake from the terminal.

Usage:
    python run_sql.py setup.sql
    python run_sql.py teardown.sql

Why this exists: setup.sql contains many statements AND switches roles partway
through (USE ROLE SYSADMIN, then USERADMIN, then SECURITYADMIN). All statements
must run in ONE session so those role switches persist. The connector's
`execute_string()` does exactly that — it runs a multi-statement script in a
single session, in order.
"""

import sys
from pathlib import Path

# Reuse the connection helper we already wrote for ingestion.
sys.path.append(str(Path(__file__).resolve().parent.parent / "ingestion"))
from db import get_snowflake_connection


def run_sql_file(path: str):
    sql = Path(path).read_text()

    conn = get_snowflake_connection()
    try:
        # execute_string returns one cursor per statement it ran.
        cursors = conn.execute_string(sql, remove_comments=False)
        for cur in cursors:
            # sfqid is Snowflake's query id; handy if you need to look it up later.
            print(f"[run_sql] OK  ({cur.rowcount if cur.rowcount is not None else 0} rows)  qid={cur.sfqid}")
        print(f"[run_sql] Done — executed {path}")
    except Exception as e:
        print(f"[run_sql] ERROR while running {path}: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run_sql.py <file.sql>")
        sys.exit(1)
    run_sql_file(sys.argv[1])

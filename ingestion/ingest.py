import pandas as pd
from db import get_supabase_client, get_snowflake_connection

TABLES = [
    "users",
    "boards",
    "memberships",
    "entries",
    "announcements",
    "announcement_reactions",
    "subscriptions",
    "usage_events",
    "support_requests",
]


def fetch_table(client, table_name: str) -> pd.DataFrame:
    print(f"[ingest] Fetching {table_name} from Supabase...")
    # Supabase/PostgREST caps a single response at 1000 rows. We must paginate
    # with .range() or tables larger than 1000 are silently truncated. Loop until
    # a page returns fewer rows than the page size, meaning we've hit the end.
    page_size = 1000
    offset = 0
    all_rows = []
    while True:
        result = (
            client.table(table_name)
            .select("*")
            .range(offset, offset + page_size - 1)  # .range() is inclusive on both ends
            .execute()
        )
        all_rows.extend(result.data)
        if len(result.data) < page_size:
            break  # short page = last page
        offset += page_size
    df = pd.DataFrame(all_rows)
    print(f"[ingest] {table_name}: {len(df)} rows fetched")
    return df


def load_table(conn, table_name: str, df: pd.DataFrame):
    if df.empty:
        print(f"[ingest] {table_name}: no data, skipping")
        return

    cursor = conn.cursor()

    # Atomic full refresh via load-then-swap. We never touch the live table until the
    # new data is fully built in a side table, then replace it with a single atomic
    # ALTER TABLE ... SWAP. A crash before the swap leaves the live table holding the
    # previous run's complete data — never empty or half-loaded.
    # (A transaction would NOT help: Snowflake DDL auto-commits and can't be rolled back.)
    load_table_name = f"{table_name}__load"

    # Build column list from dataframe — quote names to preserve case in Snowflake
    columns = ", ".join([f'"{col}"' for col in df.columns.tolist()])
    placeholders = ", ".join(["%s"] * len(df.columns))

    # Table names stay unquoted (Snowflake folds them to uppercase) to match the existing
    # convention; only column names are quoted to preserve their source casing (see ISSUES_LOG #3).
    column_ddl = ", ".join([f'"{col}" VARCHAR' for col in df.columns])

    # 1. Build the new data off to the side. Live table untouched.
    cursor.execute(f"CREATE OR REPLACE TABLE {load_table_name} ({column_ddl})")

    # 2. Fill the side table. If this raises, we stop here and the live table is intact.
    rows = [tuple(str(v) if v is not None else None for v in row) for row in df.itertuples(index=False)]
    cursor.executemany(
        f'INSERT INTO {load_table_name} ({columns}) VALUES ({placeholders})',
        rows
    )

    # 3. Ensure the live table exists so SWAP has a counterpart (no-op after first run).
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} LIKE {load_table_name}")

    # 4. The one atomic moment: live table now holds the new data; load table holds the old.
    cursor.execute(f"ALTER TABLE {table_name} SWAP WITH {load_table_name}")

    # 5. Discard the old data.
    cursor.execute(f"DROP TABLE IF EXISTS {load_table_name}")

    print(f"[ingest] {table_name}: {len(df)} rows loaded into Snowflake")
    cursor.close()


def run():
    supabase = get_supabase_client()
    snowflake_conn = get_snowflake_connection()

    for table in TABLES:
        try:
            df = fetch_table(supabase, table)
            load_table(snowflake_conn, table, df)
        except Exception as e:
            print(f"[ingest] ERROR on {table}: {e}")

    snowflake_conn.close()
    print("[ingest] Done.")


if __name__ == "__main__":
    run()

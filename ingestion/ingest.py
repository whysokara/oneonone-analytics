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

    # Build column list from dataframe — quote names to preserve case in Snowflake
    columns = ", ".join([f'"{col}"' for col in df.columns.tolist()])
    placeholders = ", ".join(["%s"] * len(df.columns))

    # Drop and recreate table for full refresh
    cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
    cursor.execute(f"""
        CREATE TABLE {table_name} (
            {", ".join([f'"{col}" VARCHAR' for col in df.columns])}
        )
    """)

    # Insert rows
    rows = [tuple(str(v) if v is not None else None for v in row) for row in df.itertuples(index=False)]
    cursor.executemany(
        f'INSERT INTO {table_name} ({columns}) VALUES ({placeholders})',
        rows
    )

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

from db import get_supabase_client, get_snowflake_connection


def test_supabase():
    client = get_supabase_client()
    result = client.table("users").select("id").limit(1).execute()
    print(f"[supabase] OK — got {len(result.data)} row(s) from users table")


def test_snowflake():
    conn = get_snowflake_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_WAREHOUSE()")
    row = cursor.fetchone()
    print(f"[snowflake] OK — connected to {row[0]}.{row[1]} using warehouse {row[2]}")
    cursor.close()
    conn.close()


if __name__ == "__main__":
    test_supabase()
    test_snowflake()

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client
import snowflake.connector

load_dotenv()


def get_supabase_client() -> Client:
    try:
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
        return create_client(url, key)
    except KeyError as e:
        print(f"[db] Missing environment variable: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[db] Failed to connect to Supabase: {e}")
        sys.exit(1)


def get_snowflake_connection() -> snowflake.connector.SnowflakeConnection:
    try:
        return snowflake.connector.connect(
            account=os.environ["SNOWFLAKE_ACCOUNT"],
            user=os.environ["SNOWFLAKE_USER"],
            password=os.environ["SNOWFLAKE_PASSWORD"],
            # role controls which privileges this session has. Optional: if unset,
            # Snowflake falls back to the user's default role. Ingestion sets it to
            # ONEONONE_LOADER so it runs with exactly the rights it needs.
            role=os.environ.get("SNOWFLAKE_ROLE"),
            warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
            database=os.environ["SNOWFLAKE_DATABASE"],
            schema=os.environ["SNOWFLAKE_SCHEMA"],
        )
    except KeyError as e:
        print(f"[db] Missing environment variable: {e}")
        sys.exit(1)
    except snowflake.connector.errors.DatabaseError as e:
        print(f"[db] Snowflake connection failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[db] Unexpected error connecting to Snowflake: {e}")
        sys.exit(1)

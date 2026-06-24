"""
Create the SVC_ONEONONE_LOADER service user for CI (GitHub Actions).

WHY A SERVICE USER:
The daily ingestion cron runs on GitHub's servers and needs Snowflake creds in
GitHub Secrets. We must NEVER put a personal ACCOUNTADMIN user (COCOON) there.
Instead we create a dedicated user that holds ONLY the ONEONONE_LOADER role, so
a leaked CI secret can at worst write to RAW — it cannot touch anything else.

WHY YOU RUN THIS YOURSELF (not the AI):
It generates a password and prints it ONCE. Secrets should never pass through an
agent's tool output / logs. Run it in your own terminal, copy the password
straight into GitHub Secrets, and it's never written to disk or git.

USAGE:
    cd snowflake
    python create_service_user.py

Connects as your admin user (COCOON) from .env, then switches to USERADMIN /
SECURITYADMIN to create the user and grant the role.
"""

import os
import secrets
import string
from pathlib import Path

from dotenv import load_dotenv
import snowflake.connector

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

SERVICE_USER = "SVC_ONEONONE_LOADER"


def generate_password(length: int = 28) -> str:
    # Snowflake requires >= 8 chars with upper, lower, and digit. We exceed that
    # comfortably and guarantee at least one of each, then fill the rest randomly.
    alphabet = string.ascii_letters + string.digits
    while True:
        pw = "".join(secrets.choice(alphabet) for _ in range(length))
        if (any(c.isupper() for c in pw)
                and any(c.islower() for c in pw)
                and any(c.isdigit() for c in pw)):
            return pw


def main():
    password = generate_password()

    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
    )
    cur = conn.cursor()

    # USERADMIN creates users (and roles). Create the service user, pin its
    # default role/warehouse so it doesn't have to set them each run, and mark
    # the password as not requiring a change (it's a machine account).
    cur.execute("USE ROLE USERADMIN")
    cur.execute(f"""
        CREATE USER IF NOT EXISTS {SERVICE_USER}
            PASSWORD            = '{password}'
            DEFAULT_ROLE        = ONEONONE_LOADER
            DEFAULT_WAREHOUSE   = ONEONONE_WH
            MUST_CHANGE_PASSWORD = FALSE
            COMMENT             = 'Service account for GitHub Actions ingestion. LOADER role only.'
    """)
    # If the user already existed, make sure the password is the new one.
    cur.execute(f"ALTER USER {SERVICE_USER} SET PASSWORD = '{password}'")

    # SECURITYADMIN owns granting. Give it ONLY the loader role — least privilege.
    cur.execute("USE ROLE SECURITYADMIN")
    cur.execute(f"GRANT ROLE ONEONONE_LOADER TO USER {SERVICE_USER}")

    conn.close()

    print("\n" + "=" * 64)
    print(f"  Service user created: {SERVICE_USER}")
    print("=" * 64)
    print("  Add these to GitHub repo Secrets (Settings > Secrets > Actions):")
    print()
    print(f"    SNOWFLAKE_USER      = {SERVICE_USER}")
    print(f"    SNOWFLAKE_PASSWORD  = {password}")
    print(f"    SNOWFLAKE_ROLE      = ONEONONE_LOADER")
    print(f"    SNOWFLAKE_WAREHOUSE = ONEONONE_WH")
    print()
    print("  ^ This password is shown ONCE. Copy it now. It is not saved anywhere.")
    print("=" * 64 + "\n")


if __name__ == "__main__":
    main()

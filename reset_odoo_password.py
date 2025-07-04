import os
import sys
import argparse
import psycopg2
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

parser = argparse.ArgumentParser(description="Reset odoo user password!")
parser.add_argument("--db", required=True, help="Odoo database name")
args = parser.parse_args()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
USER_ID = os.getenv("USER_ID")
NEW_PASSWORD = os.getenv("NEW_PASSWORD")

required_vars = {
    "DB_HOST": DB_HOST,
    "DB_PORT": DB_PORT,
    "DB_USER": DB_USER,
    "DB_PASSWORD": DB_PASSWORD,
    "USER_ID": USER_ID,
    "NEW_PASSWORD": NEW_PASSWORD,
}

missing = [key for key, value in required_vars.items() if value is None]
if missing:
    print(f"Missing required environment variables: {', '.join(missing)}")
    sys.exit(1)

USER_ID = int(USER_ID)

pwd_context = CryptContext(
    schemes=["pbkdf2_sha512"],
    default="pbkdf2_sha512",
    pbkdf2_sha512__default_rounds=60000,
)

hashed_password = pwd_context.hash(NEW_PASSWORD)

try:
    conn = psycopg2.connect(
        dbname=args.db,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )
    cur = conn.cursor()
    cur.execute("UPDATE res_users SET password = %s WHERE id = %s", (hashed_password, USER_ID))

    conn.commit()
    cur.close()
    conn.close()
    print("Password reset successful!!")
except Exception as e:
    print(f"Error: {e}")

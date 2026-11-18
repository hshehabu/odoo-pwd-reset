import argparse
import sys
from core import execute_reset, DB_USER_16, DB_USER_17, DB_USER_18, DB_USER_19, DEFAULT_LOGIN, DEFAULT_NEW_PASSWORD, DEFAULT_USER_ID

def main():
    parser = argparse.ArgumentParser(
        description="Reset Odoo User Password across v16, v17, v18, and v19 without modifying .env"
    )
    parser.add_argument("--db", required=True, help="Odoo database name")
    parser.add_argument(
        "--version",
        default="auto",
        choices=["auto", "16", "17", "18", "19"],
        help=f"Odoo version: 16 ({DB_USER_16}), 17 ({DB_USER_17}), 18/19 ({DB_USER_18}), or auto",
    )
    parser.add_argument("--user", default=None, help="Explicit PostgreSQL DB user override")
    parser.add_argument("--login", default=DEFAULT_LOGIN, help="Odoo login username (default: admin)")
    parser.add_argument("--password", default=DEFAULT_NEW_PASSWORD, help="New password (default: admin)")
    parser.add_argument("--uid", default=DEFAULT_USER_ID, type=int, help="Odoo user ID (default: 2)")

    args = parser.parse_args()

    print(f"[*] Resetting password for '{args.login}' on database '{args.db}' (Version: {args.version})...")
    try:
        res = execute_reset(
            dbname=args.db,
            version=args.version,
            db_user=args.user,
            login=args.login,
            new_password=args.password,
            user_id=args.uid,
        )
        if res.get("success"):
            det = res.get("details", {})
            print(f"[+] SUCCESS: {res.get('message')}")
            print(f"    - Database: {det.get('database')}")
            print(f"    - DB User: {det.get('db_user')}")
            print(f"    - Version: {det.get('detected_version') or args.version}")
            print(f"    - Login: {det.get('login')}")
        else:
            print(f"[-] ERROR: {res.get('error')}")
            sys.exit(1)
    except Exception as e:
        print(f"[-] ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

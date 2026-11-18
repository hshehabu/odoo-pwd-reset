"""Shared Odoo password-reset logic (used by the Chrome native host, web UI and CLI).
Never prints to stdout: the native host uses stdout for its protocol."""
import os
import psycopg2
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_PASSWORD = os.getenv("DB_PASSWORD", "openpgpwd")

# Version specific DB users
DB_USER_16 = os.getenv("DB_USER_16", "openpg16")
DB_USER_17 = os.getenv("DB_USER_17", "openpg17")
DB_USER_18 = os.getenv("DB_USER_18", "openpg")
DB_USER_19 = os.getenv("DB_USER_19", "openpg")
DB_USER_FALLBACK = os.getenv("DB_USER", "openpg")

DEFAULT_LOGIN = os.getenv("LOGIN", "admin").strip()
DEFAULT_NEW_PASSWORD = os.getenv("NEW_PASSWORD", "admin").strip()
DEFAULT_USER_ID = int(os.getenv("USER_ID", "2"))
SERVER_PORT = int(os.getenv("PORT", os.getenv("SERVER_PORT", "1111")))

VERSION_USER_MAP = {
    "16": DB_USER_16,
    "17": DB_USER_17,
    "18": DB_USER_18,
    "19": DB_USER_19,
}

pwd_context = CryptContext(
    schemes=["pbkdf2_sha512"],
    default="pbkdf2_sha512",
    pbkdf2_sha512__default_rounds=60000,
)


def get_meta_connection():
    """Connect to postgres DB to inspect databases and owners."""
    # Try openpg, openpg17, openpg16, postgres
    candidate_users = [DB_USER_18, DB_USER_17, DB_USER_16, "postgres"]
    last_err = None
    for u in candidate_users:
        try:
            conn = psycopg2.connect(
                dbname="postgres",
                user=u,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT,
                connect_timeout=3,
            )
            return conn, u
        except Exception as e:
            last_err = e
            continue
    raise Exception(f"Could not connect to postgres catalog: {last_err}")


def get_databases():
    """Return all non-template databases with their owner and mapped version."""
    conn, _ = get_meta_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT d.datname, u.usename
        FROM pg_database d
        JOIN pg_user u ON d.datdba = u.usesysid
        WHERE d.datistemplate = false
        ORDER BY d.datname;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    result = []
    for datname, usename in rows:
        owner = usename or ""
        suggested_version = "auto"
        if owner == DB_USER_16:
            suggested_version = "16"
        elif owner == DB_USER_17:
            suggested_version = "17"
        elif owner == DB_USER_18 or owner == DB_USER_19:
            suggested_version = "18/19"

        result.append({
            "name": datname,
            "owner": owner,
            "suggested_version": suggested_version,
        })
    return result


def detect_database_info(dbname):
    """Detect database owner and installed base version."""
    owner = None
    try:
        conn, _ = get_meta_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT u.usename
            FROM pg_database d
            JOIN pg_user u ON d.datdba = u.usesysid
            WHERE d.datname = %s;
        """, (dbname,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            owner = row[0]
    except Exception:
        pass

    # Resolve candidate user to inspect tables
    candidate_user = resolve_db_user(dbname=dbname, version="auto", explicit_user=None, owner=owner)

    exact_version = None
    major_version = None
    try:
        conn = psycopg2.connect(
            dbname=dbname,
            user=candidate_user,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            connect_timeout=3,
        )
        cur = conn.cursor()
        cur.execute("SELECT latest_version FROM ir_module_module WHERE name = 'base';")
        v_row = cur.fetchone()
        if v_row and v_row[0]:
            exact_version = v_row[0]
            major_version = exact_version.split(".")[0]
        cur.close()
        conn.close()
    except Exception:
        # If ir_module_module check fails, infer from owner
        if owner == DB_USER_16:
            major_version = "16"
        elif owner == DB_USER_17:
            major_version = "17"
        elif owner == DB_USER_18:
            major_version = "18"

    return {
        "dbname": dbname,
        "owner": owner,
        "exact_version": exact_version,
        "major_version": major_version,
        "recommended_user": candidate_user,
    }


def resolve_db_user(dbname, version="auto", explicit_user=None, owner=None):
    """Determine the right PostgreSQL user for the given db and version."""
    if explicit_user and explicit_user.strip():
        return explicit_user.strip()

    v_str = str(version).strip().lower() if version else "auto"

    if v_str in ("16", "v16"):
        return DB_USER_16
    elif v_str in ("17", "v17"):
        return DB_USER_17
    elif v_str in ("18", "v18"):
        return DB_USER_18
    elif v_str in ("19", "v19"):
        return DB_USER_19

    # Auto resolution by checking database owner
    if not owner and dbname:
        try:
            conn, _ = get_meta_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT u.usename
                FROM pg_database d
                JOIN pg_user u ON d.datdba = u.usesysid
                WHERE d.datname = %s;
            """, (dbname,))
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row:
                owner = row[0]
        except Exception:
            pass

    if owner:
        if owner == DB_USER_16:
            return DB_USER_16
        elif owner == DB_USER_17:
            return DB_USER_17
        elif owner == DB_USER_18 or owner == DB_USER_19:
            return DB_USER_18

    # Fallback default
    return DB_USER_FALLBACK


def execute_reset(dbname, version="auto", db_user=None, db_password=None, login="admin", new_password="admin", user_id=2):
    """Execute password reset query on the target database."""
    if not dbname or not dbname.strip():
        raise ValueError("Database name is required.")

    dbname = dbname.strip()
    login = (login or DEFAULT_LOGIN).strip()
    new_password = new_password if new_password is not None else DEFAULT_NEW_PASSWORD
    user_id = int(user_id) if user_id is not None else DEFAULT_USER_ID
    db_password = db_password or DB_PASSWORD

    resolved_user = resolve_db_user(dbname=dbname, version=version, explicit_user=db_user)

    hashed = pwd_context.hash(new_password)

    conn = None
    try:
        conn = psycopg2.connect(
            dbname=dbname,
            user=resolved_user,
            password=db_password,
            host=DB_HOST,
            port=DB_PORT,
            connect_timeout=5,
        )
        cur = conn.cursor()

        # Update user 2 by id
        cur.execute(
            "UPDATE res_users SET login = %s, password = %s, active = true WHERE id = %s;",
            (login, hashed, user_id),
        )
        rows_affected = cur.rowcount

        # If user ID not found, attempt update by login
        if rows_affected == 0:
            cur.execute(
                "UPDATE res_users SET password = %s, active = true WHERE login = %s;",
                (hashed, login),
            )
            rows_affected = cur.rowcount

        # Query version from ir_module_module if available
        detected_version = None
        try:
            cur.execute("SELECT latest_version FROM ir_module_module WHERE name = 'base';")
            v_row = cur.fetchone()
            if v_row and v_row[0]:
                detected_version = v_row[0]
        except Exception:
            pass

        conn.commit()
        cur.close()

        if rows_affected == 0:
            return {
                "success": False,
                "error": f"No user matched ID {user_id} or login '{login}' in database '{dbname}'.",
                "db_user_used": resolved_user,
            }

        return {
            "success": True,
            "message": f"Password reset successfully for '{login}' on '{dbname}'!",
            "details": {
                "database": dbname,
                "login": login,
                "user_id": user_id,
                "db_user": resolved_user,
                "rows_affected": rows_affected,
                "detected_version": detected_version,
            },
        }
    finally:
        if conn and not conn.closed:
            conn.close()

"""Chrome Native Messaging host for the Odoo Reset extension.

Chrome launches this process on demand when the extension popup opens and
kills it when the popup closes. No background service, port or autostart.

Protocol: each message is a 4-byte little-endian length followed by UTF-8 JSON.
Request:  {"id": 1, "action": "databases" | "detect" | "reset" | "ping", ...}
Response: {"id": 1, "success": true/false, ...}
"""
import json
import os
import struct
import sys

# Grab the real stdout for the protocol, then point print() at stderr so a
# stray print anywhere can never corrupt the message stream.
if sys.platform == "win32":
    import msvcrt
    msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
_in = sys.stdin.buffer
_out = sys.stdout.buffer
sys.stdout = sys.stderr


def send(msg):
    data = json.dumps(msg).encode("utf-8")
    _out.write(struct.pack("<I", len(data)))
    _out.write(data)
    _out.flush()


def read():
    raw_len = _in.read(4)
    if len(raw_len) < 4:
        return None
    (length,) = struct.unpack("<I", raw_len)
    return json.loads(_in.read(length).decode("utf-8"))


def handle(msg, core):
    action = msg.get("action")
    if action == "ping":
        return {"success": True}
    if action == "databases":
        return {"success": True, "databases": core.get_databases()}
    if action == "detect":
        return {"success": True, "info": core.detect_database_info(msg["dbname"])}
    if action == "reset":
        return core.execute_reset(
            dbname=msg.get("dbname", ""),
            version=msg.get("version", "auto"),
            db_user=(msg.get("db_user") or "").strip() or None,
            login=msg.get("login") or core.DEFAULT_LOGIN,
            new_password=msg.get("new_password") or core.DEFAULT_NEW_PASSWORD,
            user_id=msg.get("user_id") or core.DEFAULT_USER_ID,
        )
    return {"success": False, "error": f"Unknown action: {action}"}


def main():
    try:
        import core
    except Exception as e:  # missing venv package, bad .env, etc.
        core = None
        import_error = f"Helper failed to start: {e}"

    while True:
        msg = read()
        if msg is None:
            return
        try:
            if core is None:
                result = {"success": False, "error": import_error}
            else:
                result = handle(msg, core)
        except Exception as e:
            result = {"success": False, "error": str(e)}
        result["id"] = msg.get("id")
        send(result)


if __name__ == "__main__":
    main()

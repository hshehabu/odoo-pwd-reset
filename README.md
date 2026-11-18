# Odoo Reset Hub (v16–v19)

Reset an Odoo user's password in one click from Chrome. No background service, no port, no startup entry:
the extension launches a tiny local Python helper on demand (Chrome Native Messaging) and it exits when the popup closes.

## Setup (once)

1. Double-click **`install.bat`**. It registers the helper for Chrome, Edge and Brave (per-user, no admin) and removes the old v1 background service if present.
2. In Chrome, open `chrome://extensions`, enable **Developer mode**, click **Load unpacked**, and pick the `extension` folder.
   If the old version is loaded, remove it first. The new one has the fixed ID `jacalminapabnhdfbalehfbflomiojno`.
3. Pin **Odoo Reset Hub** to the toolbar.

If you move this folder, run `install.bat` again.

## Use

Open an Odoo tab, click the extension, press **Reset password**.

- The database is filled in from the current tab (URL `?db=`, the page's session info, or the `last_used_database` cookie). You can also type or pick any database; the list comes from PostgreSQL.
- The PostgreSQL user is picked automatically from the database owner (`openpg16`, `openpg17`, `openpg`). You can override the version or user under **Advanced**.
- With **Log in on the current tab** checked, the extension fills the Odoo login form and submits it. If you are signed in as someone else, it logs that session out first.

## Other ways to run it

```bash
# CLI
venv\Scripts\python reset_odoo_password.py --db printly            # auto-detect
venv\Scripts\python reset_odoo_password.py --db aldser --version 16

# Web UI on http://127.0.0.1:1111 (runs only while the window is open)
reset_password.bat
```

## Files

```text
extension/          Chrome extension (popup + background worker)
native_host.py      Helper Chrome starts on demand (stdin/stdout JSON)
native_host.bat     Launcher Chrome calls; uses venv\Scripts\python.exe
core.py             Reset logic shared by the extension, CLI and web UI
setup_host.py       Registers/unregisters the helper (called by install/uninstall.bat)
install.bat         One-time setup
uninstall.bat       Removes the registration
server.py           Optional web UI
reset_odoo_password.py  CLI
.env                PostgreSQL connection and defaults
```

## Configuration (`.env`)

```env
DB_HOST=localhost
DB_PORT=5432
DB_PASSWORD=openpgpwd
DB_USER_16=openpg16
DB_USER_17=openpg17
DB_USER_18=openpg
DB_USER_19=openpg
DB_USER=openpg        # fallback
LOGIN=admin
NEW_PASSWORD=admin
USER_ID=2
PORT=1111             # web UI only
```

## Troubleshooting

- **"One-time setup needed" in the popup**: run `install.bat`, then reopen the popup.
- **Red dot / "Could not load databases"**: PostgreSQL isn't reachable with the credentials in `.env`. Hover the dot to see the error.

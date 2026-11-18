import os
import sys
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

from core import (DB_HOST, DB_PORT, DB_USER_16, DB_USER_17, DB_USER_18, DEFAULT_LOGIN,
                  DEFAULT_NEW_PASSWORD, DEFAULT_USER_ID, SERVER_PORT, VERSION_USER_MAP,
                  get_databases, detect_database_info, execute_reset)

# Handle pythonw where stdout/stderr is None
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Odoo Password Reset Hub (v16 - v19)</title>
    <style>
        :root {
            --primary: #714B67;
            --primary-hover: #593b52;
            --secondary: #00A09D;
            --secondary-hover: #008784;
            --bg: #0f172a;
            --card-bg: #1e293b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border: #334155;
            --success: #10b981;
            --error: #ef4444;
            --warning: #f59e0b;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            width: 100%;
            max-width: 520px;
            background: rgba(30, 41, 59, 0.95);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 28px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
        }
        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border);
        }
        .header-title {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .header-title h1 {
            font-size: 1.35rem;
            font-weight: 700;
            background: linear-gradient(135deg, #f8fafc, #cbd5e1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .badge-status {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 9999px;
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }
        .badge-status.offline {
            background: rgba(239, 68, 68, 0.15);
            color: #f87171;
            border-color: rgba(239, 68, 68, 0.3);
        }
        .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: currentColor;
        }
        .form-group {
            margin-bottom: 18px;
        }
        label {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.88rem;
            font-weight: 700;
            color: #e2e8f0;
            margin-bottom: 6px;
        }
        .sub-label {
            font-size: 0.78rem;
            color: #2dd4bf;
            font-weight: 700;
        }
        input, select {
            width: 100%;
            padding: 10px 14px;
            font-size: 0.95rem;
            color: #ffffff;
            background: #0f172a;
            border: 1.5px solid #475569;
            border-radius: 8px;
            outline: none;
            transition: all 0.2s;
        }
        input:focus, select:focus {
            border-color: #a855f7;
            box-shadow: 0 0 0 3px rgba(168, 85, 247, 0.3);
            background: #131c31;
        }
        .version-pills {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 6px;
            margin-top: 4px;
        }
        .version-btn {
            background: #1e293b;
            border: 1.5px solid #475569;
            color: #ffffff;
            padding: 9px 4px;
            border-radius: 8px;
            font-size: 0.88rem;
            font-weight: 800;
            cursor: pointer;
            text-align: center;
            transition: all 0.15s;
        }
        .version-btn:hover {
            background: #334155;
            border-color: #94a3b8;
            color: #ffffff;
        }
        .version-btn.active {
            background: linear-gradient(135deg, #853e74 0%, #9333ea 100%);
            border-color: #d8b4fe;
            color: #ffffff;
            box-shadow: 0 0 0 2px rgba(168, 85, 247, 0.4), 0 4px 12px rgba(147, 51, 234, 0.45);
        }
        .version-btn small {
            display: block;
            font-size: 0.68rem;
            color: #94a3b8;
            font-weight: 600;
            margin-top: 2px;
        }
        .version-btn.active small {
            color: #f5d0fe;
        }
        .db-user-indicator {
            margin-top: 6px;
            font-size: 0.8rem;
            color: #2dd4bf;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .row-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }
        .quick-presets {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 6px;
        }
        .preset-btn {
            background: #1e293b;
            border: 1px solid #475569;
            color: #f1f5f9;
            font-size: 0.76rem;
            font-weight: 700;
            padding: 3px 10px;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.15s;
        }
        .preset-btn:hover {
            background: #334155;
            color: #ffffff;
            border-color: #2dd4bf;
        }
            background: transparent;
            border: 1px solid var(--border);
            color: var(--text-muted);
            font-size: 0.7rem;
            padding: 2px 8px;
            border-radius: 4px;
            cursor: pointer;
        }
        .preset-btn:hover {
            color: var(--text-main);
            border-color: var(--secondary);
        }
        button.submit-btn {
            width: 100%;
            background: linear-gradient(135deg, var(--primary), #9333ea);
            color: white;
            padding: 13px;
            border: none;
            border-radius: 10px;
            font-size: 1rem;
            font-weight: 700;
            cursor: pointer;
            margin-top: 10px;
            transition: all 0.2s;
            box-shadow: 0 4px 14px rgba(113, 75, 103, 0.4);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        button.submit-btn:hover {
            opacity: 0.95;
            transform: translateY(-1px);
        }
        button.submit-btn:disabled {
            background: #475569;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        .alert {
            margin-top: 18px;
            padding: 12px 14px;
            border-radius: 8px;
            font-size: 0.85rem;
            line-height: 1.4;
            display: none;
            animation: fadeIn 0.2s ease-in;
        }
        .alert.success {
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }
        .alert.error {
            background: rgba(239, 68, 68, 0.15);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }
        .alert.info {
            background: rgba(59, 130, 246, 0.15);
            color: #60a5fa;
            border: 1px solid rgba(59, 130, 246, 0.3);
        }
        details {
            margin-top: 14px;
            border-top: 1px solid var(--border);
            padding-top: 10px;
        }
        summary {
            font-size: 0.78rem;
            color: var(--text-muted);
            cursor: pointer;
            user-select: none;
        }
        .details-content {
            padding-top: 12px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-4px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .extension-callout {
            margin-top: 20px;
            background: rgba(0, 160, 157, 0.08);
            border: 1px dashed rgba(0, 160, 157, 0.35);
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 0.75rem;
            color: #cbd5e1;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-title">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#714B67" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                </svg>
                <h1>Odoo Password Reset</h1>
            </div>
            <div id="statusBadge" class="badge-status">
                <span class="dot"></span>
                <span>Server Ready</span>
            </div>
        </div>

        <form id="resetForm">
            <!-- Database Input & Selector -->
            <div class="form-group">
                <label for="dbname">
                    <span>Database Name</span>
                    <span id="detectedVersionText" class="sub-label"></span>
                </label>
                <input list="databasesList" id="dbname" name="dbname" placeholder="e.g. printly, aldser, waha..." required autofocus autocomplete="off">
                <datalist id="databasesList"></datalist>
            </div>

            <!-- Version Selector Pills -->
            <div class="form-group">
                <label>
                    <span>Odoo Version</span>
                    <span id="dbUserText" class="sub-label">DB User: auto</span>
                </label>
                <div class="version-pills">
                    <button type="button" class="version-btn active" data-version="auto">
                        ⚡ Auto
                        <small>Smart detect</small>
                    </button>
                    <button type="button" class="version-btn" data-version="16">
                        v16
                        <small>openpg16</small>
                    </button>
                    <button type="button" class="version-btn" data-version="17">
                        v17
                        <small>openpg17</small>
                    </button>
                    <button type="button" class="version-btn" data-version="18">
                        v18
                        <small>openpg</small>
                    </button>
                    <button type="button" class="version-btn" data-version="19">
                        v19
                        <small>openpg</small>
                    </button>
                </div>
            </div>

            <!-- Login and Password -->
            <div class="row-2">
                <div class="form-group">
                    <label for="login">Login Username</label>
                    <input type="text" id="login" name="login" value="admin" required>
                </div>
                <div class="form-group">
                    <label for="new_password">New Password</label>
                    <input type="text" id="new_password" name="new_password" value="admin" required>
                    <div class="quick-presets">
                        <span style="font-size:0.7rem; color:var(--text-muted);">Quick:</span>
                        <button type="button" class="preset-btn" onclick="document.getElementById('new_password').value='admin'">admin</button>
                        <button type="button" class="preset-btn" onclick="document.getElementById('new_password').value='123456'">123456</button>
                        <button type="button" class="preset-btn" onclick="document.getElementById('new_password').value='admin123'">admin123</button>
                    </div>
                </div>
            </div>

            <!-- Advanced Settings Accordion -->
            <details>
                <summary>⚙️ Advanced DB & User Options</summary>
                <div class="details-content">
                    <div>
                        <label for="user_id">User ID</label>
                        <input type="number" id="user_id" value="2">
                    </div>
                    <div>
                        <label for="db_user_override">Custom DB User</label>
                        <input type="text" id="db_user_override" placeholder="Override (optional)">
                    </div>
                </div>
            </details>

            <button type="submit" id="submitBtn" class="submit-btn">
                <span>Reset Password</span>
            </button>
        </form>

        <div id="alertBox" class="alert"></div>

        <div class="extension-callout">
            <span>✨ Chrome Extension Available in <code>/extension</code></span>
            <span style="color:var(--secondary); font-weight:600;">Load in chrome://extensions</span>
        </div>
    </div>

    <script>
        let selectedVersion = 'auto';
        const versionMap = {
            'auto': 'auto-detect',
            '16': 'openpg16',
            '17': 'openpg17',
            '18': 'openpg',
            '19': 'openpg'
        };
        const dbMeta = {};

        // Fetch databases list on load
        async function loadDatabases() {
            try {
                const res = await fetch('/api/databases');
                const data = await res.json();
                if (data.success && data.databases) {
                    const dl = document.getElementById('databasesList');
                    dl.innerHTML = '';
                    data.databases.forEach(db => {
                        dbMeta[db.name] = db;
                        const opt = document.createElement('option');
                        opt.value = db.name;
                        opt.textContent = `${db.name} (${db.owner} - ${db.suggested_version})`;
                        dl.appendChild(opt);
                    });
                }
            } catch (err) {
                console.warn('Could not pre-fetch databases:', err);
            }
        }
        loadDatabases();

        // Version button switching
        document.querySelectorAll('.version-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.version-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                selectedVersion = btn.getAttribute('data-version');
                updateDbUserIndicator();
            });
        });

        // Autodetect on database input change
        const dbInput = document.getElementById('dbname');
        dbInput.addEventListener('input', () => {
            const val = dbInput.value.trim();
            if (dbMeta[val] && selectedVersion === 'auto') {
                const meta = dbMeta[val];
                document.getElementById('detectedVersionText').textContent = `Owner: ${meta.owner} (${meta.suggested_version})`;
                document.getElementById('dbUserText').textContent = `DB User: ${meta.owner}`;
            } else {
                updateDbUserIndicator();
            }
        });

        function updateDbUserIndicator() {
            const dbVal = dbInput.value.trim();
            if (selectedVersion === 'auto') {
                if (dbMeta[dbVal]) {
                    document.getElementById('dbUserText').textContent = `DB User: ${dbMeta[dbVal].owner}`;
                    document.getElementById('detectedVersionText').textContent = `Owner: ${dbMeta[dbVal].owner}`;
                } else {
                    document.getElementById('dbUserText').textContent = 'DB User: auto-detect';
                    document.getElementById('detectedVersionText').textContent = '';
                }
            } else {
                document.getElementById('dbUserText').textContent = `DB User: ${versionMap[selectedVersion]}`;
                document.getElementById('detectedVersionText').textContent = `Forced v${selectedVersion}`;
            }
        }

        // Handle form submit
        document.getElementById('resetForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = document.getElementById('submitBtn');
            const alertBox = document.getElementById('alertBox');
            
            const dbname = document.getElementById('dbname').value.trim();
            const login = document.getElementById('login').value.trim();
            const new_password = document.getElementById('new_password').value;
            const user_id = document.getElementById('user_id').value;
            const db_user_override = document.getElementById('db_user_override').value.trim();

            if (!dbname) {
                showAlert('Please select or enter a database name.', 'error');
                return;
            }

            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span>Resetting Password...</span>';
            showAlert('Connecting to database and hashing password...', 'info');

            try {
                const res = await fetch('/api/reset', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        dbname,
                        version: selectedVersion,
                        db_user: db_user_override || undefined,
                        login,
                        new_password,
                        user_id: user_id ? parseInt(user_id) : 2
                    })
                });

                const data = await res.json();
                if (data.success) {
                    const det = data.details || {};
                    showAlert(`✅ <strong>${data.message}</strong><br><small style="opacity:0.9;">Database: <strong>${det.database}</strong> | DB User: <strong>${det.db_user}</strong> | Version: <strong>${det.detected_version || 'Detected'}</strong> | Login: <strong>${det.login}</strong></small>`, 'success');
                } else {
                    showAlert(`❌ <strong>Failed:</strong> ${data.error || 'Unknown error'}`, 'error');
                }
            } catch (err) {
                showAlert(`❌ <strong>Network / Server Error:</strong> ${err.message}`, 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<span>Reset Password</span>';
            }
        });

        function showAlert(msg, type) {
            const alertBox = document.getElementById('alertBox');
            alertBox.innerHTML = msg;
            alertBox.className = `alert ${type}`;
            alertBox.style.display = 'block';
        }
    </script>
</body>
</html>"""


class OdooResetHandler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def _send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path.rstrip("/")

        if path == "" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))

        elif path == "/api/status":
            self._send_json(200, {
                "success": True,
                "status": "online",
                "db_host": DB_HOST,
                "db_port": DB_PORT,
                "version_users": VERSION_USER_MAP,
                "default_login": DEFAULT_LOGIN,
                "default_user_id": DEFAULT_USER_ID,
            })

        elif path == "/api/databases":
            try:
                dbs = get_databases()
                self._send_json(200, {"success": True, "databases": dbs})
            except Exception as e:
                self._send_json(500, {"success": False, "error": str(e)})

        else:
            self.send_response(404)
            self._send_cors_headers()
            self.end_headers()

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path.rstrip("/")

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8")

        # Parse JSON or form data
        data = {}
        content_type = self.headers.get("Content-Type", "")
        if "application/json" in content_type:
            try:
                data = json.loads(post_data) if post_data else {}
            except Exception as e:
                self._send_json(400, {"success": False, "error": f"Invalid JSON: {e}"})
                return
        else:
            # Parse urlencoded
            params = urllib.parse.parse_qs(post_data)
            for k, v in params.items():
                data[k] = v[0] if v else ""

        if path == "/api/detect":
            dbname = data.get("dbname", "").strip()
            if not dbname:
                self._send_json(400, {"success": False, "error": "Database name is required"})
                return
            try:
                info = detect_database_info(dbname)
                self._send_json(200, {"success": True, "info": info})
            except Exception as e:
                self._send_json(500, {"success": False, "error": str(e)})

        elif path in ("/api/reset", "/reset"):
            dbname = data.get("dbname", "").strip()
            version = data.get("version", "auto")
            db_user = data.get("db_user", "").strip() or None
            db_password = data.get("db_password", "").strip() or None
            login = data.get("login", DEFAULT_LOGIN)
            new_password = data.get("new_password", DEFAULT_NEW_PASSWORD)
            user_id = data.get("user_id", DEFAULT_USER_ID)

            try:
                result = execute_reset(
                    dbname=dbname,
                    version=version,
                    db_user=db_user,
                    db_password=db_password,
                    login=login,
                    new_password=new_password,
                    user_id=user_id,
                )
                status_code = 200 if result.get("success") else 400
                self._send_json(status_code, result)
            except Exception as e:
                self._send_json(500, {"success": False, "error": str(e)})

        else:
            self.send_response(404)
            self._send_cors_headers()
            self.end_headers()

    def log_message(self, format, *args):
        try:
            if sys.stdout:
                sys.stdout.write(f"[{self.log_date_time_string()}] {format % args}\n")
                sys.stdout.flush()
        except Exception:
            pass


def run_server():
    server_address = ("127.0.0.1", SERVER_PORT)
    try:
        httpd = HTTPServer(server_address, OdooResetHandler)
    except OSError as e:
        # If port is in use, report clearly
        print(f"Error starting server on port {SERVER_PORT}: {e}")
        sys.exit(1)

    try:
        print(f"==================================================")
        print(f"  Odoo Password Reset Server running on http://127.0.0.1:{SERVER_PORT}")
        print(f"  PostgreSQL: {DB_HOST}:{DB_PORT}")
        print(f"  DB Users: v16={DB_USER_16}, v17={DB_USER_17}, v18/v19={DB_USER_18}")
        print(f"  Chrome Extension & Web UI Ready!")
        print(f"==================================================")
    except Exception:
        pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()


if __name__ == "__main__":
    run_server()

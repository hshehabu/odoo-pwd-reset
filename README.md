# 🔑 Odoo Password Reset Hub (v16, v17, v18, v19)

A fast, handy, and easy-to-use tool to reset Odoo passwords across **all Odoo versions (16, 17, 18, 19)** without ever needing to manually edit `.env` or switch PostgreSQL users.

Now available as a **Chrome Extension** with automatic active-tab database detection, as well as a **Web App** and **CLI**.

---

## ⚡ Key Features

- 🧩 **Chrome Extension (Manifest V3)**:
  - 1-click password reset directly from your browser toolbar.
  - **Active Tab Auto-Detection**: Detects Odoo database name and version from your current browser tab.
  - **Auto-Fill & Reload**: Injects credentials directly into the Odoo login form and logs you in.
  - **Live Database List**: Fetches all 60+ PostgreSQL databases with search autocomplete.
- 🔄 **Smart DB User Mapping (No `.env` editing)**:
  - **Odoo 16** ➡️ Uses `openpg16`
  - **Odoo 17** ➡️ Uses `openpg17`
  - **Odoo 18 & 19** ➡️ Share `openpg`
  - **⚡ Auto-Detect** ➡️ Automatically checks database owner and Odoo version!
- 🪟 **Background Service**:
  - `start_background.vbs`: Runs silently in the background with zero terminal windows.
  - `install_autostart.bat`: 1-click setup so the local service starts automatically with Windows.
- 🌐 **Web UI & CLI**:
  - Web UI available at `http://localhost:1111` (or double-click `reset_password.bat`).
  - Enhanced CLI `python reset_odoo_password.py --db <dbname> --version 16|17|18|19|auto`.

---

## 🚀 Quick Setup: Load the Chrome Extension

1. **Start the local service** (runs silently):
   - Double-click **`start_background.vbs`** (or run `install_autostart.bat` so it starts with Windows).
2. **Open Google Chrome**:
   - Go to `chrome://extensions/`
   - Enable **Developer mode** (toggle in the top-right corner).
   - Click **Load unpacked**.
   - Select the **`extension`** folder inside this directory:
     ```
     C:\Users\Admin\Documents\odoo-tools\reset pwd\extension
     ```
3. **Pin the Extension**:
   - Click the puzzle icon in Chrome's toolbar and pin **Odoo Reset Hub**.

---

## 💡 How to Use

### 1. From the Chrome Extension
1. Open any Odoo tab in Chrome (e.g. `http://localhost:8069`, `http://localhost:8016`, or your test server).
2. Click the **Odoo Reset Hub** icon in Chrome.
   - It automatically detects your database and Odoo version!
   - The correct DB user (`openpg16`, `openpg17`, or `openpg`) is mapped automatically.
3. Click **Reset Password**.
4. Click **🚀 Auto-Fill & Reload Active Tab** to log in instantly!

### 2. From the Web Interface
- Double-click **`reset_password.bat`**
- It opens `http://localhost:1111` in your browser.
- Select your database from the dropdown, choose your version (or leave on **⚡ Auto**), and click **Reset Password**.

### 3. From Command Line (CLI)
```bash
# Auto-detect version and DB user
venv\Scripts\python reset_odoo_password.py --db printly

# Explicit version 16 (uses openpg16)
venv\Scripts\python reset_odoo_password.py --db aldser --version 16

# Explicit version 17 (uses openpg17)
venv\Scripts\python reset_odoo_password.py --db alwatikon-live --version 17

# Explicit version 18 or 19 (uses openpg)
venv\Scripts\python reset_odoo_password.py --db printly --version 19
```

---

## 📁 File Structure

```text
├── extension/                     # Chrome Extension (Load Unpacked in Chrome)
│   ├── manifest.json              # MV3 configuration
│   ├── popup.html                 # Sleek popup UI
│   ├── popup.js                   # Extension logic, active tab detection & API calls
│   ├── popup.css                  # Modern dark theme with Odoo styling
│   └── icons/                     # 16, 32, 48, 128 px icons
├── server.py                      # Local Python API server & Web UI
├── reset_odoo_password.py         # CLI password reset tool
├── start_background.vbs           # Starts server silently without a window
├── start_server.bat               # Starts server in a visible console (debug)
├── stop_server.bat                # Stops any running server process
├── install_autostart.bat          # Configures server to run on Windows startup
├── uninstall_autostart.bat        # Removes Windows startup shortcut
├── reset_password.bat             # 1-click launcher for Web UI
├── .env                           # Environment configuration
└── README.md
```

---

## ⚙️ Configuration (`.env`)

```env
DB_HOST=localhost
DB_PORT=5432
DB_PASSWORD=openpgpwd

# Version DB Users:
DB_USER_16=openpg16
DB_USER_17=openpg17
DB_USER_18=openpg
DB_USER_19=openpg

# Default fallback:
DB_USER=openpg

LOGIN=admin
NEW_PASSWORD=admin
USER_ID=2
PORT=1111
```

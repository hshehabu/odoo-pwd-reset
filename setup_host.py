"""Register / unregister the Chrome native messaging host (per-user, no admin).

    python setup_host.py install
    python setup_host.py uninstall
"""
import json
import os
import subprocess
import sys
import winreg

HOST_NAME = "com.odoo.reset_hub"
EXTENSION_ID = "jacalminapabnhdfbalehfbflomiojno"  # fixed by "key" in extension/manifest.json
HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST_PATH = os.path.join(HERE, f"{HOST_NAME}.json")
BROWSER_KEYS = [
    rf"Software\Google\Chrome\NativeMessagingHosts\{HOST_NAME}",
    rf"Software\Microsoft\Edge\NativeMessagingHosts\{HOST_NAME}",
    rf"Software\BraveSoftware\Brave-Browser\NativeMessagingHosts\{HOST_NAME}",
]
OLD_STARTUP_LNK = os.path.join(
    os.environ.get("APPDATA", ""),
    r"Microsoft\Windows\Start Menu\Programs\Startup\OdooPasswordResetService.lnk",
)


def cleanup_old_service():
    """Remove the legacy background service from v1 (startup shortcut + port 1111 server)."""
    if os.path.exists(OLD_STARTUP_LNK):
        os.remove(OLD_STARTUP_LNK)
        print("[OK] Removed old Windows Startup entry (OdooPasswordResetService.lnk)")
    subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-NetTCPConnection -LocalPort 1111 -State Listen -ErrorAction SilentlyContinue | "
         "ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"],
        capture_output=True,
    )


def install():
    manifest = {
        "name": HOST_NAME,
        "description": "Odoo Reset Hub helper",
        "path": os.path.join(HERE, "native_host.bat"),
        "type": "stdio",
        "allowed_origins": [f"chrome-extension://{EXTENSION_ID}/"],
    }
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    for key in BROWSER_KEYS:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key) as k:
            winreg.SetValueEx(k, "", 0, winreg.REG_SZ, MANIFEST_PATH)
    cleanup_old_service()
    print(f"[OK] Native helper registered for extension {EXTENSION_ID}")


def uninstall():
    for key in BROWSER_KEYS:
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key)
        except FileNotFoundError:
            pass
    if os.path.exists(MANIFEST_PATH):
        os.remove(MANIFEST_PATH)
    cleanup_old_service()
    print("[OK] Native helper unregistered")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "install"
    {"install": install, "uninstall": uninstall}[cmd]()

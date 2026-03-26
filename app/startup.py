"""
startup.py — Windows startup integration for Quietum.
Uses --startup flag so the mini widget launches on boot instead of the full app.
"""

import sys
import os
from app.constants import APP_NAME


def _get_startup_command() -> str:
    """Get the command that should run at Windows startup."""
    if getattr(sys, 'frozen', False):
        # Running as compiled .exe — launch with --startup flag
        return f'"{sys.executable}" --startup'
    else:
        # Running as script — use pythonw to avoid console window
        python_dir = os.path.dirname(sys.executable)
        pythonw = os.path.join(python_dir, "pythonw.exe")
        main_script = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "main.py"
        )
        exe = pythonw if os.path.exists(pythonw) else sys.executable
        return f'"{exe}" "{main_script}" --startup'


def enable_startup():
    """Add Quietum to Windows startup (current user)."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE,
        )
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _get_startup_command())
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def disable_startup():
    """Remove Quietum from Windows startup."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE,
        )
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def is_startup_enabled() -> bool:
    """Check if Quietum is in the Windows startup registry."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_READ,
        )
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False

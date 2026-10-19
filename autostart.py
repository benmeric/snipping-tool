"""
Ekran Alıntısı Aracı - Windows Autostart Manager
=================================
Uygulamanın Windows açılışında otomatik başlamasını Registry üzerinden yönetir.
"""

import os
import sys
import winreg

APP_NAME = "EkranAlintisiAraci"
REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def get_startup_command() -> str:
    """Uygulamanın arka planda (pencersiz) başlatılma komutunu döndürür."""
    python_dir = os.path.dirname(sys.executable)
    # pythonw.exe konsol penceresi açmadan arka planda çalıştırır
    pythonw = os.path.join(python_dir, "pythonw.exe")
    if not os.path.exists(pythonw):
        pythonw = sys.executable

    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
    return f'"{pythonw}" "{script_path}"'


def is_autostart_enabled() -> bool:
    """Windows başlangıcında açık olup olmadığını kontrol eder."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ) as key:
            val, _ = winreg.QueryValueEx(key, APP_NAME)
            return bool(val)
    except FileNotFoundError:
        return False
    except Exception:
        return False


def set_autostart(enable: bool) -> bool:
    """Windows başlangıcında çalışmayı açar veya kapatır."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE) as key:
            if enable:
                cmd = get_startup_command()
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError:
                    pass
        return True
    except Exception as e:
        print(f"Başlangıç ayarı güncellenemedi: {e}")
        return False


if __name__ == "__main__":
    print(f"Windows ile başlama durumu: {is_autostart_enabled()}")

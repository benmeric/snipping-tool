"""
Ekran Alıntısı Aracı - Windows Varsayılan Ekran Alıntısı Aracı Yöneticisi
========================================================================
Bu modül, uygulamanın Windows 10 ve Windows 11 üzerinde resmi ve yerel
"Varsayılan Ekran Alıntısı Aracı" (Default Snipping Tool) olarak kaydedilmesini,
PrtScn (Print Screen) tuşunun yönlendirilmesini ve ms-screenclip: protokolünün
yönetilmesini sağlar.
"""

import os
import sys
import winreg
import logging
from config import config
from autostart import set_autostart, is_autostart_enabled

APP_PROG_ID = "EkranAlintisiAraci.ScreenClip"
CAPABILITIES_KEY = r"Software\Classes\EkranAlintisiAraci.Capabilities"
REGISTERED_APPS_KEY = r"Software\RegisteredApplications"
PROTOCOL_KEY = r"Software\Classes\ms-screenclip"
KEYBOARD_KEY = r"Control Panel\Keyboard"


def get_command_path(extra_args="--snip") -> str:
    """Uygulamanın komut satırı çağrı metnini hazırlar."""
    python_dir = os.path.dirname(sys.executable)
    pythonw = os.path.join(python_dir, "pythonw.exe")
    if not os.path.exists(pythonw):
        pythonw = sys.executable

    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
    if extra_args:
        return f'"{pythonw}" "{script_path}" {extra_args} "%1"'
    return f'"{pythonw}" "{script_path}" "%1"'


def is_default_snipping_tool() -> bool:
    """Uygulamanın şu anda varsayılan ekran alıntısı aracı olarak kayıtlı olup olmadığını denetler."""
    try:
        cmd_path = f"{PROTOCOL_KEY}\\shell\\open\\command"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, cmd_path, 0, winreg.KEY_READ) as k:
            val, _ = winreg.QueryValueEx(k, "")
            # Bizim script veya python dosyamızın adı geçiyor mu?
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
            if script_path.lower() in str(val).lower() or "ekranalintisi" in str(val).lower():
                return True
    except Exception:
        pass

    return config.get("is_default_snipper", False)


def _delete_key_tree(root, subkey):
    """Registry anahtarını ve alt anahtarlarını özyinelemeli olarak siler."""
    try:
        with winreg.OpenKey(root, subkey, 0, winreg.KEY_ALL_ACCESS) as k:
            while True:
                try:
                    sub = winreg.EnumKey(k, 0)
                    _delete_key_tree(root, f"{subkey}\\{sub}")
                except OSError:
                    break
        winreg.DeleteKey(root, subkey)
    except Exception:
        pass


def set_as_default_snipping_tool(enable: bool = True) -> tuple[bool, str]:
    """
    Uygulamayı Windows varsayılan ekran alıntısı aracı olarak ayarlar veya kaldırır.
    
    Yaptığı işlemler:
    1. HKCU\\Software\\Classes\\ms-screenclip protokolünü bu uygulamaya bağlar.
    2. HKCU\\Software\\RegisteredApplications altına yetenekleri (Capabilities) kaydeder.
    3. HKCU\\Control Panel\\Keyboard -> PrintScreenKeyForSnippingEnabled ayarını 1 yapar.
    4. Windows ile birlikte otomatik başlamayı açar.
    5. config.json içerisine 'is_default_snipper' ve 'intercept_print_screen' kaydeder.
    """
    try:
        if enable:
            cmd = get_command_path("--snip")

            # 1. ms-screenclip URL Protokolü
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, PROTOCOL_KEY) as k:
                winreg.SetValueEx(k, "", 0, winreg.REG_SZ, "URL:ms-screenclip")
                winreg.SetValueEx(k, "URL Protocol", 0, winreg.REG_SZ, "")
                # İkon
                ico_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.ico")
                if os.path.exists(ico_path):
                    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{PROTOCOL_KEY}\\DefaultIcon") as ik:
                        winreg.SetValueEx(ik, "", 0, winreg.REG_SZ, f'"{ico_path}",0')

            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{PROTOCOL_KEY}\\shell\\open\\command") as k:
                winreg.SetValueEx(k, "", 0, winreg.REG_SZ, cmd)

            # 2. Windows RegisteredApplications Tanımı (Varsayılan Programlar Listesi İçin)
            prog_id_key = f"Software\\Classes\\{APP_PROG_ID}"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, prog_id_key) as k:
                winreg.SetValueEx(k, "", 0, winreg.REG_SZ, "Ekran Alıntısı Aracı (Google Lens)")
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{prog_id_key}\\shell\\open\\command") as k:
                winreg.SetValueEx(k, "", 0, winreg.REG_SZ, cmd)

            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{CAPABILITIES_KEY}\\URLAssociations") as k:
                winreg.SetValueEx(k, "ms-screenclip", 0, winreg.REG_SZ, APP_PROG_ID)

            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, CAPABILITIES_KEY) as k:
                winreg.SetValueEx(k, "ApplicationName", 0, winreg.REG_SZ, "Ekran Alıntısı Aracı")
                winreg.SetValueEx(k, "ApplicationDescription", 0, winreg.REG_SZ, "Google Lens Destekli Ekran Alıntısı Aracı")

            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REGISTERED_APPS_KEY) as k:
                winreg.SetValueEx(k, "EkranAlintisiAraci", 0, winreg.REG_SZ, CAPABILITIES_KEY)

            # 3. Windows Klavye Ayarı: Print Screen tuşunu ekran alıntısına bağla
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, KEYBOARD_KEY, 0, winreg.KEY_SET_VALUE) as k:
                    winreg.SetValueEx(k, "PrintScreenKeyForSnippingEnabled", 0, winreg.REG_DWORD, 1)
            except Exception as e:
                logging.warning("PrintScreenKeyForSnippingEnabled güncellenemedi: %s", e)

            # 4. Windows Başlangıcında Çalıştır
            set_autostart(True)

            # 5. Konfigürasyonu Güncelle
            config.set("is_default_snipper", True)
            config.set("intercept_print_screen", True)

            return True, "Uygulama başarıyla Windows varsayılan ekran alıntısı aracı olarak ayarlandı."

        else:
            # Kaldırma (Reset)
            _delete_key_tree(winreg.HKEY_CURRENT_USER, PROTOCOL_KEY)
            _delete_key_tree(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{APP_PROG_ID}")
            _delete_key_tree(winreg.HKEY_CURRENT_USER, CAPABILITIES_KEY)

            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTERED_APPS_KEY, 0, winreg.KEY_SET_VALUE) as k:
                    winreg.DeleteValue(k, "EkranAlintisiAraci")
            except Exception:
                pass

            config.set("is_default_snipper", False)
            config.set("intercept_print_screen", False)

            return True, "Varsayılan ekran alıntısı aracı ayarı kaldırıldı."

    except Exception as e:
        logging.error("Varsayılan araç ayarlanırken hata: %s", e)
        return False, str(e)


def open_windows_keyboard_settings():
    """Windows'un 'Print Screen tuşuyla ekran alıntısı yap' ayarlar sayfasını açar."""
    try:
        os.system("start ms-settings:easeofaccess-keyboard")
    except Exception:
        pass


def open_windows_default_apps_settings():
    """Windows'un 'Varsayılan Uygulamalar' ayar sayfasını açar."""
    try:
        os.system("start ms-settings:defaultapps")
    except Exception:
        pass

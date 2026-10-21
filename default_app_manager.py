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
                winreg.SetValueEx(k, "", 0, winreg.REG_SZ, "Snipping Tool (Google Lens)")
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{prog_id_key}\\shell\\open\\command") as k:
                winreg.SetValueEx(k, "", 0, winreg.REG_SZ, cmd)

            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{CAPABILITIES_KEY}\\URLAssociations") as k:
                winreg.SetValueEx(k, "ms-screenclip", 0, winreg.REG_SZ, APP_PROG_ID)

            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, CAPABILITIES_KEY) as k:
                winreg.SetValueEx(k, "ApplicationName", 0, winreg.REG_SZ, "Snipping Tool")
                winreg.SetValueEx(k, "ApplicationDescription", 0, winreg.REG_SZ, "Snipping Tool with Google Lens Integration")

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

            return True, "Application successfully set as the default Windows snipping tool."

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

            return True, "Default snipping tool setting has been removed."

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


def get_desktop_dir() -> str:
    """Windows'un gerçek aktif masaüstü klasörünü (OneDrive yönlendirmeleri dahil) döndürür."""
    try:
        import ctypes
        from ctypes import wintypes
        CSIDL_DESKTOP = 0x0010
        buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_DESKTOP, None, 0, buf)
        if buf.value and os.path.exists(buf.value):
            return buf.value
    except Exception:
        pass

    user_home = os.path.expanduser("~")
    for cand in [
        os.path.join(user_home, "OneDrive", "Masaüstü"),
        os.path.join(user_home, "OneDrive", "Desktop"),
        os.path.join(user_home, "Masaüstü"),
        os.path.join(user_home, "Desktop")
    ]:
        if os.path.exists(cand):
            return cand
    return os.path.join(user_home, "Desktop")


def get_shortcut_path() -> str:
    desktop = get_desktop_dir()
    for name in ["Ekran Alıntısı Aracı.lnk", "Snipping Tool.lnk"]:
        cand = os.path.join(desktop, name)
        if os.path.exists(cand):
            return cand
    try:
        from i18n import t
        app_title = t("app_title")
    except Exception:
        app_title = "Snipping Tool"
    return os.path.join(desktop, f"{app_title}.lnk")


def is_desktop_shortcut_existing() -> bool:
    """Masaüstünde kısayolun var olup olmadığını denetler."""
    return os.path.exists(get_shortcut_path())


def create_desktop_shortcut() -> tuple[bool, str]:
    """Masaüstüne uygulamanın özel simgeli (.ico) Windows kısayolunu (.lnk) ekler."""
    try:
        import subprocess
        try:
            from i18n import t
            app_title = t("app_title")
            app_desc = t("app_name_full")
        except Exception:
            app_title = "Snipping Tool"
            app_desc = "Snipping Tool (Google Lens Integration)"

        desktop_dir = get_desktop_dir()
        os.makedirs(desktop_dir, exist_ok=True)

        app_dir = os.path.dirname(os.path.abspath(__file__))
        main_py = os.path.join(app_dir, "main.py")
        ico_path = os.path.join(app_dir, "app_icon.ico")

        python_dir = os.path.dirname(sys.executable)
        pythonw = os.path.join(python_dir, "pythonw.exe")
        if not os.path.exists(pythonw):
            pythonw = sys.executable

        shortcut_name = f"{app_title}.lnk"
        shortcut_path = os.path.join(desktop_dir, shortcut_name)

        ps_cmd = (
            f"$WshShell = New-Object -ComObject WScript.Shell; "
            f"$Shortcut = $WshShell.CreateShortcut('{shortcut_path}'); "
            f"$Shortcut.TargetPath = '{pythonw}'; "
            f'$Shortcut.Arguments = \'"{main_py}"\'; '
            f"$Shortcut.WorkingDirectory = '{app_dir}'; "
            f"$Shortcut.IconLocation = '{ico_path},0'; "
            f"$Shortcut.Description = '{app_desc}'; "
            f"$Shortcut.Save()"
        )

        res = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=8
        )

        if os.path.exists(shortcut_path):
            return True, shortcut_path
        else:
            return False, res.stderr or "Kısayol oluşturulamadı."
    except Exception as e:
        logging.error("Masaüstü kısayolu oluşturulamadı: %s", e)
        return False, str(e)

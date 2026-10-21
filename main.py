"""
Ekran Alıntısı Aracı (Google Lens Entegrasyonlu)
================================================
Tersine mühendislik ile geliştirilmiş Windows Ekran Alıntısı Aracı klonu.
- Print Screen (PrtScn / SysRq) tuşuna basıldığında açılır.
- Resmi panoya kopyalar.
- Bing yerine doğrudan Google Lens ile aratır.
- Windows varsayılan ekran alıntısı aracı (ms-screenclip) ve tekil örnek (Single-Instance IPC) desteği.
"""

import sys
import socket
import threading
import logging
import icon_assets
from editor_window import EkranAlintisiAraci
from hotkey_manager import HotkeyManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

IPC_PORT = 58432


def send_ipc_command(command: str) -> bool:
    """Zaten çalışan bir ana örneğe komut gönderir (örn: 'snip', 'video', 'show')."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.2)
        s.connect(('127.0.0.1', IPC_PORT))
        s.sendall(f"{command}\n".encode("utf-8"))
        s.close()
        return True
    except Exception:
        return False


def start_ipc_server(app):
    """Diğer işlemlerden (ms-screenclip protokolü veya yeni komut satırı) gelen istekleri dinler."""
    def _listen():
        try:
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind(('127.0.0.1', IPC_PORT))
            srv.listen(5)
            while True:
                conn, _ = srv.accept()
                try:
                    data = conn.recv(1024).decode("utf-8").strip()
                    if data == "snip":
                        app.root.after(0, app.on_new_snip)
                    elif data == "video":
                        app.root.after(0, app._on_shortcut_video)
                    elif data == "show":
                        app.root.after(0, lambda: (app.root.deiconify(), app.root.lift(), app.root.focus_force()))
                except Exception:
                    pass
                finally:
                    conn.close()
        except Exception as e:
            logging.debug("IPC server dinleme sonlandı: %s", e)

    t = threading.Thread(target=_listen, daemon=True)
    t.start()


def main():
    # 1. Komut satırı parametrelerini kontrol et
    args_lower = " ".join(sys.argv).lower()
    is_snip_cmd = "--snip" in args_lower or "screenclip" in args_lower
    is_video_cmd = "--record" in args_lower or "--video" in args_lower
    is_startup = "--startup" in args_lower or "--background" in args_lower

    # 2. Eğer zaten çalışan bir uygulama örneği varsa, isteği ona ilet ve anında çık
    if is_snip_cmd:
        if send_ipc_command("snip"):
            logging.info("Çalışan mevcut uygulamaya 'snip' komutu iletildi.")
            sys.exit(0)
    elif is_video_cmd:
        if send_ipc_command("video"):
            logging.info("Çalışan mevcut uygulamaya 'video' komutu iletildi.")
            sys.exit(0)
    elif not is_startup:
        # Normal başlatma ama zaten arka planda açıksa öne getir
        if send_ipc_command("show"):
            logging.info("Uygulama zaten açık, öne getirildi.")
            sys.exit(0)

    # Windows görev çubuğunda python.exe yerine uygulamanın kendi simgesi gözükmesi için App ID ayarla
    icon_assets.setup_windows_app_id()

    logging.info("Ekran Alıntısı Aracı başlatılıyor...")
    
    # 3. Ana grafik arayüzünü oluştur
    app = EkranAlintisiAraci()

    # 4. IPC sunucusunu başlat
    start_ipc_server(app)

    # 5. Başlatma parametrelerine göre pencere durumunu ayarla
    if is_snip_cmd:
        app.root.after(200, app.on_new_snip)
    elif is_video_cmd:
        app.root.after(200, app._on_shortcut_video)
    elif is_startup:
        # Bilgisayar açılışında arka planda sessizce hazır başla
        app.root.withdraw()
        logging.info("Uygulama Windows başlangıcında arka planda hazır olarak başlatıldı.")

    # 6. Print Screen ve video kısayol yöneticisini başlat (Thread-Safe)
    def trigger_snip_safely():
        try:
            app.root.after(0, app.on_new_snip)
        except Exception:
            pass

    def trigger_video_safely():
        try:
            app.root.after(0, app._on_shortcut_video)
        except Exception:
            pass

    hotkeys = HotkeyManager(on_trigger_snip=trigger_snip_safely, on_trigger_video=trigger_video_safely)
    hotkeys.start()

    # 7. Sistem tepsisi (System Tray) simgesi
    tray_icon = None
    try:
        import pystray
        from pystray import MenuItem as item
        from PIL import Image
        import default_app_manager
        import autostart
        from i18n import t

        def _get_tray_image():
            try:
                return icon_assets.get_app_icon_image().resize((64, 64), Image.Resampling.LANCZOS)
            except Exception:
                from tray_app import create_tray_icon_image
                return create_tray_icon_image()

        def _tray_snip(icon, item):
            app.root.after(0, app.on_new_snip)

        def _tray_show(icon, item):
            app.root.after(0, lambda: (app.root.deiconify(), app.root.lift(), app.root.focus_force()))

        def _tray_toggle_default(icon, item):
            curr = default_app_manager.is_default_snipping_tool()
            default_app_manager.set_as_default_snipping_tool(not curr)

        def _tray_toggle_autostart(icon, item):
            curr = autostart.is_autostart_enabled()
            autostart.set_autostart(not curr)

        def _tray_quit(icon, item):
            icon.stop()
            hotkeys.stop()
            app.root.destroy()

        tray_menu = pystray.Menu(
            item(f"{t('app_title')}", _tray_show, default=True),
            pystray.Menu.SEPARATOR,
            item(t("tray_snip"), _tray_snip),
            item(t("btn_open_app"), _tray_show),
            pystray.Menu.SEPARATOR,
            item(t("set_default_app_title"), _tray_toggle_default, checked=lambda item: default_app_manager.is_default_snipping_tool()),
            item(t("set_autostart_title"), _tray_toggle_autostart, checked=lambda item: autostart.is_autostart_enabled()),
            pystray.Menu.SEPARATOR,
            item(t("menu_quit_app"), _tray_quit)
        )

        tray_icon = pystray.Icon("EkranAlintisiAraci", _get_tray_image(), t("app_title"), menu=tray_menu)
        tray_icon.run_detached()
    except Exception as e:
        logging.warning("Sistem tepsisi simgesi başlatılamadı: %s", e)

    # 8. Kapanırken arka planda hazır beklet veya serbest bırak
    def on_closing():
        import autostart
        import default_app_manager
        if autostart.is_autostart_enabled() or default_app_manager.is_default_snipping_tool():
            app.root.withdraw()
            from notification import toast
            from i18n import t
            toast.show(t("app_title"), t("toast_minimized_to_tray"))
        else:
            if tray_icon:
                tray_icon.stop()
            hotkeys.stop()
            app.root.destroy()

    app.root.protocol("WM_DELETE_WINDOW", on_closing)

    # 9. Arayüzü çalıştır
    try:
        app.run()
    except (KeyboardInterrupt, SystemExit):
        if tray_icon:
            tray_icon.stop()
        hotkeys.stop()


if __name__ == '__main__':
    main()

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

    # 2. Eğer zaten çalışan bir uygulama örneği varsa, isteği ona ilet ve anında çık
    if is_snip_cmd:
        if send_ipc_command("snip"):
            logging.info("Çalışan mevcut uygulamaya 'snip' komutu iletildi.")
            sys.exit(0)
    elif is_video_cmd:
        if send_ipc_command("video"):
            logging.info("Çalışan mevcut uygulamaya 'video' komutu iletildi.")
            sys.exit(0)
    else:
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

    # 5. Eğer ilk açılışta doğrudan ekran alıntısı veya video istendiyse aç
    if is_snip_cmd:
        app.root.after(200, app.on_new_snip)
    elif is_video_cmd:
        app.root.after(200, app._on_shortcut_video)

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

    # 7. Kapanırken kısayolları serbest bırak
    def on_closing():
        hotkeys.stop()
        app.root.destroy()

    app.root.protocol("WM_DELETE_WINDOW", on_closing)

    # 8. Arayüzü çalıştır
    try:
        app.run()
    except (KeyboardInterrupt, SystemExit):
        hotkeys.stop()


if __name__ == "__main__":
    main()

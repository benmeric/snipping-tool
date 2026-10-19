"""
Ekran Alıntısı Aracı (Google Lens Entegrasyonlu)
================================================
Tersine mühendislik ile geliştirilmiş Windows Ekran Alıntısı Aracı klonu.
- Print Screen (PrtScn / SysRq) tuşuna basıldığında açılır.
- Resmi panoya kopyalar.
- Bing yerine doğrudan Google Lens ile aratır.
"""

import sys
import logging
import icon_assets
from editor_window import EkranAlintisiAraci
from hotkey_manager import HotkeyManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)


def main():
    # Windows görev çubuğunda python.exe yerine uygulamanın kendi simgesi gözükmesi için App ID ayarla
    icon_assets.setup_windows_app_id()

    logging.info("Ekran Alıntısı Aracı başlatılıyor...")
    
    # 1. Ana grafik arayüzünü oluştur
    app = EkranAlintisiAraci()

    # 2. Print Screen ve video kısayol yöneticisini başlat (Thread-Safe)
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

    # 3. Kapanırken kısayolları serbest bırak
    def on_closing():
        hotkeys.stop()
        app.root.destroy()

    app.root.protocol("WM_DELETE_WINDOW", on_closing)

    # 4. Arayüzü çalıştır
    try:
        app.run()
    except (KeyboardInterrupt, SystemExit):
        hotkeys.stop()


if __name__ == "__main__":
    main()

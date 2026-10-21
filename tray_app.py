import default_app_manager
"""
Ekran Alıntısı Aracı - System Tray Application
==============================================
Windows görev çubuğu / sistem tepsisinde (System Tray) çalışan,
kullanıcının ayarları değiştirmesini ve hızlı işlemler yapmasını sağlayan menü.
"""

import threading
from PIL import Image, ImageDraw, ImageGrab
import pystray
from pystray import MenuItem as item
from config import config
from lens_engine import search_with_google_lens
from screen_snipper import trigger_snipper
from autostart import is_autostart_enabled, set_autostart
from notification import toast
from i18n import t


def create_tray_icon_image() -> Image.Image:
    """Sistem tepsisi için şık bir Google Lens / Büyüteç ikonu çizer."""
    size = (64, 64)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Google Lens tarzı çok renkli halka
    # Dış daire
    draw.ellipse([4, 4, 60, 60], fill=(30, 35, 45, 240), outline="#4285f4", width=3)
    
    # İç lens dairesi
    draw.ellipse([18, 18, 46, 46], fill=(66, 133, 244, 255), outline="#ea4335", width=2)
    draw.ellipse([25, 25, 39, 39], fill="#ffffff")

    # Parlama efekti
    draw.ellipse([22, 22, 28, 28], fill=(255, 255, 255, 200))

    return img


class TrayApp:
    def __init__(self, on_exit=None):
        self.on_exit = on_exit
        self.icon = None

    def _toggle_auto_search(self, icon, item):
        val = config.toggle("auto_search_on_clipboard")
        status = "Açık" if val else "Kapalı"
        toast.show("⚙️ Ayar Güncellendi", f"Pano otomatik arama: {status}")

    def _toggle_toast(self, icon, item):
        config.toggle("show_toast_notification")

    def _toggle_sound(self, icon, item):
        config.toggle("play_sound")

    def _toggle_default_app(self, icon, item):
        curr = default_app_manager.is_default_snipping_tool()
        ok, msg = default_app_manager.set_as_default_snipping_tool(not curr)
        status = t("set_default_app_status_active") if not curr else t("set_default_app_status_inactive")
        toast.show(t("app_title"), status)

    def _toggle_autostart(self, icon, item):
        current = is_autostart_enabled()
        set_autostart(not current)
        status = "Açık" if not current else "Kapalı"
        toast.show("🚀 Başlangıç Ayarı", f"Windows ile başlatma: {status}")

    def _search_clipboard_now(self, icon, item):
        img = ImageGrab.grabclipboard()
        if isinstance(img, Image.Image):
            toast.show("🔍 Google Lens", "Panodaki resim Google Lens'te açılıyor...", image_preview=img)
            threading.Thread(target=lambda: search_with_google_lens(img, open_browser=True), daemon=True).start()
        else:
            toast.show("⚠️ Uyarı", "Panoda taranabilecek bir resim bulunamadı!")

    def _trigger_snip(self, icon, item):
        trigger_snipper()

    def _quit_app(self, icon, item):
        if self.on_exit:
            self.on_exit()
        icon.stop()

    def run(self):
        icon_image = create_tray_icon_image()

        menu = pystray.Menu(
            item(f"{t('app_title')} - Google Lens", None, enabled=False),
            pystray.Menu.SEPARATOR,
            item(
                t("tray_snip"),
                self._trigger_snip,
                default=True
            ),
            item(
                t("tray_search_lens"),
                self._search_clipboard_now
            ),
            pystray.Menu.SEPARATOR,
            item(
                t("tray_auto_lens"),
                self._toggle_auto_search,
                checked=lambda item: config.get("auto_search_on_clipboard", True)
            ),
            item(
                t("tray_toasts"),
                self._toggle_toast,
                checked=lambda item: config.get("show_toast_notification", True)
            ),
            item(
                t("tray_sound"),
                self._toggle_sound,
                checked=lambda item: config.get("play_sound", True)
            ),
            item(
                t("set_default_app_title"),
                self._toggle_default_app,
                checked=lambda item: default_app_manager.is_default_snipping_tool()
            ),
            item(
                t("tray_autostart"),
                self._toggle_autostart,
                checked=lambda item: is_autostart_enabled()
            ),
            pystray.Menu.SEPARATOR,
            item(t("tray_quit"), self._quit_app)
        )

        self.icon = pystray.Icon(
            name="EkranAlintisiAraci",
            icon=icon_image,
            title=t("app_title"),
            menu=menu
        )
        self.icon.run()

    def stop(self):
        if self.icon:
            self.icon.stop()

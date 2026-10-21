"""
Ekran Alıntısı Aracı - Global Kısayol Yöneticisi
================================================
Klavyedeki 'Print Screen' (PrtScn / SysRq), 'Win + Shift + S' ve 'Ctrl + Shift + S'
tuşlarını yakalar ve Ekran Alıntısı Aracı'nı tetikler.
"""

import logging
import keyboard
from config import config
import default_app_manager


class HotkeyManager:
    def __init__(self, on_trigger_snip, on_trigger_video=None):
        self.on_trigger_snip = on_trigger_snip
        self.on_trigger_video = on_trigger_video
        self._running = False

    def start(self):
        try:
            # 1. Print Screen tuşunu yakala
            # Varsayılan araç aktifse tuşu doğrudan bastır (suppress=True), böylece Windows'un eski aracı açılmaz
            suppress_prt = config.get("intercept_print_screen", True) or default_app_manager.is_default_snipping_tool()
            try:
                keyboard.add_hotkey("print screen", self._on_hotkey_pressed, suppress=suppress_prt)
            except Exception:
                keyboard.add_hotkey("print screen", self._on_hotkey_pressed, suppress=False)

            # 2. Ctrl + Shift + S kısayolunu yakala
            keyboard.add_hotkey("ctrl+shift+s", self._on_hotkey_pressed, suppress=False)

            # 3. Windows + Shift + S kısayolunu yakala
            try:
                keyboard.add_hotkey("windows+shift+s", self._on_hotkey_pressed, suppress=False)
            except Exception:
                pass

            # 4. Ctrl + Shift + R video kısayolunu yakala
            if self.on_trigger_video:
                keyboard.add_hotkey("ctrl+shift+r", self._on_video_hotkey_pressed, suppress=False)

            logging.info("Klavye kısayolları dinleniyor (Print Screen, Win+Shift+S, Ctrl+Shift+S, Ctrl+Shift+R).")
            self._running = True
        except Exception as e:
            logging.warning("Global kısayol kaydedilemedi: %s", e)

    def _on_hotkey_pressed(self):
        if self.on_trigger_snip:
            self.on_trigger_snip()

    def _on_video_hotkey_pressed(self):
        if self.on_trigger_video:
            self.on_trigger_video()

    def stop(self):
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        self._running = False

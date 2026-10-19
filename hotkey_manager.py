"""
Ekran Alıntısı Aracı - Global Kısayol Yöneticisi
================================================
Klavyedeki 'Print Screen' (PrtScn / SysRq) ve 'Ctrl + Shift + S'
tuşlarını yakalar ve Ekran Alıntısı Aracı'nı tetikler.
"""

import logging
import keyboard


class HotkeyManager:
    def __init__(self, on_trigger_snip, on_trigger_video=None):
        self.on_trigger_snip = on_trigger_snip
        self.on_trigger_video = on_trigger_video
        self._running = False

    def start(self):
        try:
            # 1. Print Screen tuşunu yakala
            keyboard.add_hotkey("print screen", self._on_hotkey_pressed, suppress=False)
            # 2. Ctrl + Shift + S kısayolunu yakala
            keyboard.add_hotkey("ctrl+shift+s", self._on_hotkey_pressed, suppress=False)
            # 3. Ctrl + Shift + R video kısayolunu yakala
            if self.on_trigger_video:
                keyboard.add_hotkey("ctrl+shift+r", self._on_video_hotkey_pressed, suppress=False)
            logging.info("Klavye kısayolları dinleniyor (Print Screen, Ctrl+Shift+S, Ctrl+Shift+R).")
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

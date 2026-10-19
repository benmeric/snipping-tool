"""
Ekran Alıntısı Aracı - Configuration Manager
============================================
Uygulama ayarlarını JSON dosyası olarak saklar ve yönetir.
Windows 11 Snipping Tool ayarlarının tamamını içerir.
"""

import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

user_home = os.path.expanduser("~")
default_pics_dir = (
    os.path.join(user_home, "OneDrive", "Resimler", "Ekran Görüntüleri")
    if os.path.exists(os.path.join(user_home, "OneDrive", "Resimler"))
    else os.path.join(user_home, "Pictures", "Ekran Görüntüleri")
)

default_videos_dir = os.path.join(user_home, "Videos", "Ekran Kayıtları")

DEFAULT_CONFIG = {
    # Ekran alıntısı alma ayarları
    "auto_copy_snip": True,
    "auto_save_snip": True,
    "snip_save_dir": default_pics_dir,
    "snip_filename_prefix": "Ekran_Goruntusu",
    "ask_save_edited_snip": False,
    "multi_window": False,
    "add_border": False,
    "border_color": "#D13438",
    "border_width": 3,
    "hdr_color_fix": False,

    # Ekran kaydı ayarları
    "auto_copy_video": True,
    "auto_save_video": True,
    "video_save_dir": default_videos_dir,
    "ask_save_edited_video": True,
    "record_mic_default": False,
    "record_system_audio_default": True,

    # Görünüm ve genel
    "app_theme": "dark",
    "app_language": "system",
    "google_lens_enabled": True,
    "play_sound": True
}


class Config:
    def __init__(self):
        self._data = dict(DEFAULT_CONFIG)
        self.load()

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    self._data.update(saved)
            except Exception as e:
                print(f"Ayar dosyası yüklenemedi, varsayılanlar kullanılıyor: {e}")
        else:
            self.save()

    def save(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Ayar dosyası kaydedilemedi: {e}")

    def get(self, key, default=None):
        return self._data.get(key, default if default is not None else DEFAULT_CONFIG.get(key))

    def set(self, key, value):
        self._data[key] = value
        self.save()

    def toggle(self, key):
        current = self.get(key, False)
        self.set(key, not current)
        return not current


config = Config()

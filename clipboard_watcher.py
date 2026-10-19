"""
Ekran Alıntısı Aracı - Clipboard Watcher
========================================
Windows Panosunu (Clipboard) izler. Kullanıcı 'Print Screen' veya 'Win+Shift+S'
ile ekran alıntısı yaptığında yeni resmi anında algılar ve Google Lens'e yönlendirir.

Win32 GetClipboardSequenceNumber API'si sayesinde CPU kullanımı %0'dır.
"""

import ctypes
import hashlib
import io
import logging
import threading
import time
from PIL import ImageGrab, Image
from config import config
from lens_engine import search_with_google_lens
from notification import toast
from i18n import t

user32 = ctypes.windll.user32
CF_DIB = 8
CF_BITMAP = 2


class ClipboardWatcher:
    def __init__(self):
        self._running = False
        self._thread = None
        self._last_seq = 0
        self._last_image_hash = None
        self._lock = threading.Lock()

    def _hash_image(self, img: Image.Image) -> str:
        """Resmin içeriğine göre benzersiz bir MD5 hash'i üretir."""
        buf = io.BytesIO()
        # Hızlı hash için küçük boyuta indirip kontrol et
        small = img.resize((64, 64), Image.Resampling.NEAREST)
        small.save(buf, format="PNG")
        return hashlib.md5(buf.getvalue()).hexdigest()

    def _on_image_detected(self, img: Image.Image):
        """Yeni bir resim kopyalandığında tetiklenir."""
        img_hash = self._hash_image(img)
        if img_hash == self._last_image_hash:
            # Aynı resim tekrar kopyalanmış, işlem yapma
            return

        self._last_image_hash = img_hash
        logging.info("Panoda yeni ekran alıntısı tespit edildi (%dx%d).", img.width, img.height)

        if not config.get("auto_search_on_clipboard", True):
            logging.info("Otomatik arama kapalı olduğu için arama yapılmadı.")
            return

        # Bildirimi göster
        toast.show(
            title=f"🔍 Google Lens - {t('status_searching')}",
            message=t("status_uploading_lens"),
            image_preview=img
        )

        # Arka planda Google Lens'e yükle ve tarayıcıda aç
        def _upload_task():
            search_with_google_lens(img, open_browser=True)

        threading.Thread(target=_upload_task, daemon=True).start()

    def _worker(self):
        """Clipboard izleme döngüsü (GetClipboardSequenceNumber ile 0 CPU kullanımı)."""
        self._last_seq = user32.GetClipboardSequenceNumber()

        while self._running:
            try:
                curr_seq = user32.GetClipboardSequenceNumber()
                if curr_seq != self._last_seq:
                    self._last_seq = curr_seq

                    # Panoda resim formatı var mı kontrol et
                    if user32.IsClipboardFormatAvailable(CF_DIB) or user32.IsClipboardFormatAvailable(CF_BITMAP):
                        # Windows panosunun kopyalamayı bitirmesi için kısa bir bekleme (50ms)
                        time.sleep(0.05)
                        img = ImageGrab.grabclipboard()
                        if isinstance(img, Image.Image):
                            self._on_image_detected(img)

                # 200 ms aralıkla sequence kontrolü (CPU yükü 0'dır)
                time.sleep(0.2)
            except Exception as e:
                logging.error("Pano izleyici döngü hatası: %s", e)
                time.sleep(1)

    def start(self):
        with self._lock:
            if not self._running:
                self._running = True
                self._thread = threading.Thread(target=self._worker, daemon=True, name="ClipboardWatcherThread")
                self._thread.start()
                logging.info("Pano izleyici başlatıldı.")

    def stop(self):
        with self._lock:
            self._running = False
            logging.info("Pano izleyici durduruldu.")


clipboard_watcher = ClipboardWatcher()

if __name__ == "__main__":
    print("Pano izleyici çalışıyor... Print Screen veya Win+Shift+S ile ekran alıntısı yapmayı deneyin.")
    clipboard_watcher.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        clipboard_watcher.stop()

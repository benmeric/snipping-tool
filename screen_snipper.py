"""
Ekran Alıntısı Aracı - Custom Screen Snipper
============================================
Hızlı, modern ve şık bir ekran alıntısı aracı.
Kullanıcı dikdörtgen seçim yapar yapmaz:
1. Seçilen alanı panoya (Clipboard) kopyalar.
2. Resmi doğrudan Google Lens'e yükleyip arama sonucunu tarayıcıda açar.
3. ESC tuşuna basarak istediğiniz an iptal edebilirsiniz.
"""

import ctypes
from ctypes import wintypes
import io
import threading
import tkinter as tk
from PIL import ImageGrab, Image
from lens_engine import search_with_google_lens
from notification import toast
from i18n import t

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

CF_DIB = 8
GHND = 0x0042


def copy_image_to_clipboard(img: Image.Image):
    """PIL Image nesnesini doğrudan Windows panosuna (CF_DIB) kopyalar."""
    try:
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="BMP")
        bmp_data = buf.getvalue()[14:] # 14 baytlık BITMAPFILEHEADER'ı atla (DIB elde et)

        if not user32.OpenClipboard(0):
            return False

        user32.EmptyClipboard()
        h_mem = kernel32.GlobalAlloc(GHND, len(bmp_data))
        if h_mem:
            p_mem = kernel32.GlobalLock(h_mem)
            ctypes.memmove(p_mem, bmp_data, len(bmp_data))
            kernel32.GlobalUnlock(h_mem)
            user32.SetClipboardData(CF_DIB, h_mem)

        user32.CloseClipboard()
        return True
    except Exception as e:
        print(f"Panoya kopyalama hatası: {e}")
        return False


class SnippingOverlay:
    def __init__(self, on_snip_complete=None):
        self.on_snip_complete = on_snip_complete
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.text_id = None
        self.base_image = None
        self.root = None

    def start(self):
        # Tüm monitörleri kapsayan ekran görüntüsünü al
        try:
            self.base_image = ImageGrab.grab(all_screens=True)
        except Exception:
            self.base_image = ImageGrab.grab()

        self._create_window()

    def _create_window(self):
        self.root = tk.Toplevel() if tk._default_root else tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.35) # Yarı saydam koyu ekran
        self.root.configure(bg="#000000", cursor="crosshair")

        width = self.base_image.width
        height = self.base_image.height
        self.root.geometry(f"{width}x{height}+0+0")

        self.canvas = tk.Canvas(self.root, bg="#000000", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bilgi kutucuğu
        self.canvas.create_text(
            width // 2, 40,
            text=t("snipper_guide"),
            font=("Segoe UI", 12, "bold"),
            fill="#ffffff"
        )

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.root.bind("<Escape>", lambda e: self._close())

        self.root.mainloop()

    def _on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="#4285f4", width=2, fill="#ffffff", stipple="gray25"
        )
        self.text_id = self.canvas.create_text(
            self.start_x, self.start_y - 15,
            text="", font=("Segoe UI", 9, "bold"), fill="#ffffff"
        )

    def _on_drag(self, event):
        if not self.rect_id:
            return
        cur_x, cur_y = event.x, event.y
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, cur_x, cur_y)

        w = abs(cur_x - self.start_x)
        h = abs(cur_y - self.start_y)
        self.canvas.coords(self.text_id, min(self.start_x, cur_x) + 35, min(self.start_y, cur_y) - 10)
        self.canvas.itemconfig(self.text_id, text=f"{w} x {h}")

    def _on_release(self, event):
        end_x, end_y = event.x, event.y
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)

        self._close()

        # En az 10x10 piksel seçildiyse kırp
        if (x2 - x1) > 10 and (y2 - y1) > 10:
            cropped = self.base_image.crop((x1, y1, x2, y2))
            # 1. Panoya kopyala
            copy_image_to_clipboard(cropped)

            # 2. Bildirim göster
            toast.show(
                title="🔍 Google Lens ile Aranıyor",
                message=f"{x2-x1}x{y2-y1} piksel seçildi, sonuçlar açılıyor...",
                image_preview=cropped
            )

            # 3. Google Lens'te ara
            threading.Thread(
                target=lambda: search_with_google_lens(cropped, open_browser=True),
                daemon=True
            ).start()

            if self.on_snip_complete:
                self.on_snip_complete(cropped)

    def _close(self):
        try:
            if self.root:
                self.root.destroy()
                self.root = None
        except Exception:
            pass


def trigger_snipper():
    """Ekran alıntısı aracını ayrı bir iş parçacığında başlatır."""
    def _runner():
        snipper = SnippingOverlay()
        snipper.start()

    threading.Thread(target=_runner, daemon=True).start()


if __name__ == "__main__":
    print("Ekran alıntısı aracı başlatılıyor...")
    trigger_snipper()

"""
Ekran Alıntısı Aracı - Ekran Yakalama ve Pano Entegrasyonu
==========================================================
Ekran görüntüsünü mss ile donanım hızında (~5ms) yakalar.
Çoklu monitör (Dual/Triple Monitor) ve 64-bit Windows Pano desteğine sahiptir.
"""

import os
import time
import datetime
import tempfile
import ctypes
from ctypes import wintypes
import io
import threading
import winsound
from PIL import Image
import mss

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

CF_DIB = 8
CF_HDROP = 15
GHND = 0x0042
CF_PNG = user32.RegisterClipboardFormatW("PNG")

# 64-bit Windows için API tiplerini tam tanımla
kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
kernel32.GlobalAlloc.restype = wintypes.HGLOBAL

kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalLock.restype = ctypes.c_void_p

kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalUnlock.restype = wintypes.BOOL

user32.OpenClipboard.argtypes = [wintypes.HWND]
user32.OpenClipboard.restype = wintypes.BOOL

user32.EmptyClipboard.argtypes = []
user32.EmptyClipboard.restype = wintypes.BOOL

user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
user32.SetClipboardData.restype = wintypes.HANDLE

user32.CloseClipboard.argtypes = []
user32.CloseClipboard.restype = wintypes.BOOL


class DROPFILES(ctypes.Structure):
    _fields_ = [
        ('pFiles', wintypes.DWORD),
        ('pt', wintypes.POINT),
        ('fNC', wintypes.BOOL),
        ('fWide', wintypes.BOOL),
    ]


# Windows DPI Farkındalığını (Per-Monitor DPI Aware) etkinleştir
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def capture_all_screens() -> tuple[Image.Image, dict]:
    """
    Tüm monitörleri kapsayan ekran görüntüsünü ve sanal ekran koordinatlarını döndürür.
    :return: (PIL.Image, monitor_dict: {'left', 'top', 'width', 'height'})
    """
    with mss.mss() as sct:
        # monitors[0] tüm monitörlerin birleşik sanal masaüstüdür
        mon = sct.monitors[0]
        sct_img = sct.grab(mon)
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        return img, mon


def copy_image_to_clipboard(img: Image.Image, filepath: str = None) -> bool:
    """PIL Image nesnesini ve dosya referansını Windows panosuna (CF_DIB, CF_PNG, CF_HDROP)
    64-bit güvenli şekilde kopyalar.
    
    Bu sayede:
    1. Web tarayıcıları ve yapay zeka araçları (ChatGPT, Claude, Gemini vb.) görseli isimsiz
       'resim.png' olarak değil, benzersiz zaman damgalı dosya adıyla yapıştırır ve çakışma yaşanmaz!
    2. Masaüstü uygulamaları (Discord, Telegram, Slack, VSCode vb.) doğrudan dosya adıyla yükler.
    3. Paint, Photoshop, Office vb. doğrudan bitmap (CF_DIB/PNG) olarak yapıştırır.
    """
    try:
        # Eğer hazır dosya yolu yoksa veya mevcut değilse benzersiz bir PNG oluştur
        if not filepath or not os.path.exists(filepath):
            cache_dir = os.path.join(tempfile.gettempdir(), "EkranAlintisi_Captures")
            os.makedirs(cache_dir, exist_ok=True)

            # 100'den fazla geçici dosya birikmişse eski olanları temizle
            try:
                cached_files = [os.path.join(cache_dir, f) for f in os.listdir(cache_dir)]
                if len(cached_files) > 100:
                    cached_files.sort(key=os.path.getmtime)
                    for old_f in cached_files[:-50]:
                        try:
                            os.remove(old_f)
                        except Exception:
                            pass
            except Exception:
                pass

            now = datetime.datetime.now()
            ms = now.microsecond // 1000
            try:
                from config import config
                prefix = config.get("snip_filename_prefix", "Ekran_Goruntusu")
            except Exception:
                prefix = "Ekran_Goruntusu"

            file_name = f"{prefix}_{now.strftime('%Y-%m-%d_%H%M%S')}_{ms:03d}.png"
            filepath = os.path.join(cache_dir, file_name)
            img.save(filepath, format="PNG")

        filepath = os.path.abspath(filepath)

        # 1. CF_DIB (Bitmap verisi)
        buf_bmp = io.BytesIO()
        img.convert("RGB").save(buf_bmp, format="BMP")
        bmp_data = buf_bmp.getvalue()[14:]  # 14 baytlık BITMAPFILEHEADER'ı atla (DIB)

        # 2. CF_PNG (Tam şeffaflık ve sıkıştırmalı PNG verisi)
        buf_png = io.BytesIO()
        img.save(buf_png, format="PNG")
        png_data = buf_png.getvalue()

        # 3. CF_HDROP (Dosya yolu listesi - AI ve tarayıcılar için isimlendirme kaynağı)
        df = DROPFILES()
        df.pFiles = ctypes.sizeof(DROPFILES)
        df.pt.x = 0
        df.pt.y = 0
        df.fNC = False
        df.fWide = True
        files_bytes = (filepath + '\0\0').encode('utf-16-le')
        hdrop_data = bytes(df) + files_bytes

        if not user32.OpenClipboard(0):
            time.sleep(0.05)
            if not user32.OpenClipboard(0):
                return False

        user32.EmptyClipboard()

        # CF_DIB ekle
        h_dib = kernel32.GlobalAlloc(GHND, len(bmp_data))
        if h_dib:
            p_dib = kernel32.GlobalLock(h_dib)
            if p_dib:
                ctypes.memmove(p_dib, bmp_data, len(bmp_data))
                kernel32.GlobalUnlock(h_dib)
                user32.SetClipboardData(CF_DIB, h_dib)

        # CF_PNG ekle
        if CF_PNG:
            h_png = kernel32.GlobalAlloc(GHND, len(png_data))
            if h_png:
                p_png = kernel32.GlobalLock(h_png)
                if p_png:
                    ctypes.memmove(p_png, png_data, len(png_data))
                    kernel32.GlobalUnlock(h_png)
                    user32.SetClipboardData(CF_PNG, h_png)

        # CF_HDROP ekle
        h_drop = kernel32.GlobalAlloc(GHND, len(hdrop_data))
        if h_drop:
            p_drop = kernel32.GlobalLock(h_drop)
            if p_drop:
                ctypes.memmove(p_drop, hdrop_data, len(hdrop_data))
                kernel32.GlobalUnlock(h_drop)
                user32.SetClipboardData(CF_HDROP, h_drop)

        user32.CloseClipboard()
        return True
    except Exception as e:
        print(f"Panoya kopyalama hatası: {e}")
        try:
            user32.CloseClipboard()
        except Exception:
            pass
        return False


def copy_file_to_clipboard(filepath: str) -> bool:
    """Belirtilen dosya yolunu Windows panosuna (CF_HDROP) kopyalar.
    Böylece Ctrl+V ile Explorer, Discord, Telegram vb. içine dosya olarak yapıştırılabilir."""
    import os
    filepath = os.path.abspath(filepath)
    if not os.path.exists(filepath):
        return False
    try:
        df = DROPFILES()
        df.pFiles = ctypes.sizeof(DROPFILES)
        df.pt.x = 0
        df.pt.y = 0
        df.fNC = False
        df.fWide = True

        files_bytes = (filepath + '\0\0').encode('utf-16-le')
        total_bytes = ctypes.sizeof(DROPFILES) + len(files_bytes)

        h_mem = kernel32.GlobalAlloc(GHND, total_bytes)
        if not h_mem:
            return False
        p_mem = kernel32.GlobalLock(h_mem)
        if not p_mem:
            return False

        ctypes.memmove(p_mem, ctypes.byref(df), ctypes.sizeof(DROPFILES))
        ctypes.memmove(p_mem + ctypes.sizeof(DROPFILES), files_bytes, len(files_bytes))
        kernel32.GlobalUnlock(h_mem)

        if user32.OpenClipboard(0):
            user32.EmptyClipboard()
            user32.SetClipboardData(CF_HDROP, h_mem)
            user32.CloseClipboard()
            return True
        return False
    except Exception as e:
        print(f"Dosya panoya kopyalama hatası: {e}")
        try:
            user32.CloseClipboard()
        except Exception:
            pass
        return False


def play_shutter_sound():
    """Ekran alıntısı yapıldığında hafif bir kamera deklanşör sesi çalar."""
    try:
        from config import config
        if not config.get("play_sound", True):
            return
    except Exception:
        pass

    def _play():
        import os
        sound_paths = [
            os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Media", "Windows Navigation Start.wav"),
            os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Media", "Windows Pop-up Blocked.wav"),
            os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Media", "Windows Notify Messaging.wav"),
        ]
        played = False
        for p in sound_paths:
            if os.path.exists(p):
                try:
                    winsound.PlaySound(p, winsound.SND_FILENAME)
                    played = True
                    break
                except Exception:
                    continue
        if not played:
            try:
                winsound.MessageBeep(winsound.MB_OK)
            except Exception:
                pass

    threading.Thread(target=_play, daemon=True).start()

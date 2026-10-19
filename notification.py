"""
Ekran Alıntısı Aracı - Modern Toast Notification
================================================
Ekran alıntısı yapıldığında ekranın sağ alt köşesinde beliren modern,
hafif ve dikkat dağıtmayan bildirim penceresi.
"""

import tkinter as tk
from PIL import ImageTk, Image
import threading
import winsound
from config import config


class ToastNotification:
    def __init__(self):
        self._current_window = None

    def show(self, title: str, message: str, image_preview=None, duration_ms: int = 2800):
        if not config.get("show_toast_notification", True):
            return

        # Ses çalma ayarı açıksa Windows sistem bildirim sesini çal
        if config.get("play_sound", True):
            threading.Thread(target=lambda: winsound.MessageBeep(winsound.MB_OK), daemon=True).start()

        def _run_toast():
            try:
                root = tk.Tk()
                root.overrideredirect(True)
                root.attributes("-topmost", True)
                root.attributes("-alpha", 0.95)

                # Koyu tema renkleri
                bg_color = "#1f232a"
                fg_title = "#ffffff"
                fg_text = "#9aa0a6"
                accent_color = "#4285f4" # Google mavi

                root.configure(bg=bg_color, padx=12, pady=10)

                # Konumlandırma (Sağ alt köşe, görev çubuğunun hemen üstü)
                screen_width = root.winfo_screenwidth()
                screen_height = root.winfo_screenheight()
                win_width = 320
                win_height = 80
                pos_x = screen_width - win_width - 24
                pos_y = screen_height - win_height - 60
                root.geometry(f"{win_width}x{win_height}+{pos_x}+{pos_y}")

                # Çerçeve
                frame = tk.Frame(root, bg=bg_color)
                frame.pack(fill=tk.BOTH, expand=True)

                # Resim önizlemesi (varsa)
                photo = None
                if image_preview is not None:
                    try:
                        thumb = image_preview.copy()
                        thumb.thumbnail((56, 56), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(thumb)
                        img_label = tk.Label(frame, image=photo, bg="#2d333b", bd=1, relief="solid")
                        img_label.image = photo
                        img_label.pack(side=tk.LEFT, padx=(0, 10))
                    except Exception:
                        pass

                # Metin alanı
                text_frame = tk.Frame(frame, bg=bg_color)
                text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

                lbl_title = tk.Label(
                    text_frame, text=title, font=("Segoe UI", 10, "bold"),
                    fg=fg_title, bg=bg_color, anchor="w"
                )
                lbl_title.pack(fill=tk.X)

                lbl_msg = tk.Label(
                    text_frame, text=message, font=("Segoe UI", 9),
                    fg=fg_text, bg=bg_color, anchor="w"
                )
                lbl_msg.pack(fill=tk.X)

                # Tıklandığında kapat
                def _close(event=None):
                    try:
                        root.destroy()
                    except Exception:
                        pass

                root.bind("<Button-1>", _close)
                frame.bind("<Button-1>", _close)

                # Belirli süre sonra otomatik kapat
                root.after(duration_ms, _close)
                root.mainloop()
            except Exception as e:
                print(f"Toast hatası: {e}")

        threading.Thread(target=_run_toast, daemon=True).start()


toast = ToastNotification()

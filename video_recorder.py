"""
Ekran Alıntısı Aracı - Ekran Video Kaydedici Modülü
===================================================
Seçilen ekran alanını veya tüm ekranı donanım hızında (~30 FPS)
.mp4 formatında sesli/sessiz kaydeder.
Üstte süzülen modern Windows 11 tarzı kayıt denetim çubuğu sunar.
Mikrofon ses kaydı (sounddevice), FFmpeg muxing ve ekran kayıt çerçevesi içerir.
"""

import os
import sys
import time
import datetime
import threading
import tempfile
import shutil
import subprocess
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
import mss
import numpy as np
import cv2

try:
    import sounddevice as sd
    import wave
    AUDIO_AVAILABLE = True
except Exception:
    AUDIO_AVAILABLE = False

from config import config
from screen_capture import copy_file_to_clipboard
import icon_assets
from i18n import t


class VideoRecorderController:
    def __init__(self, bbox: dict, on_finish_callback=None, master=None):
        """
        :param bbox: {'left': int, 'top': int, 'width': int, 'height': int}
        """
        self.bbox = bbox
        self.width = self.bbox["width"] if self.bbox["width"] % 2 == 0 else self.bbox["width"] - 1
        self.height = self.bbox["height"] if self.bbox["height"] % 2 == 0 else self.bbox["height"] - 1
        self.on_finish_callback = on_finish_callback
        self.master = master

        self.is_recording = False
        self.start_time = 0
        self.elapsed_sec = 0

        # Ayarlardan gelen ses varsayılanları
        self.mic_enabled = config.get("record_mic_default", False)
        self.sys_audio_enabled = config.get("record_system_audio_default", True)

        self.raw_video_path = None
        self.audio_temp_path = None
        self.out_file_path = None
        self.writer = None
        self.bar_window = None
        self.border_window = None
        self.capture_thread = None
        self.audio_thread = None

    def start_recording(self):
        """Kaydı ve yüzen kontrol çubuğunu başlatır."""
        auto_save = config.get("auto_save_video", True)
        videos_dir = config.get("video_save_dir") or os.path.join(os.path.expanduser("~"), "Videos", "Ekran Kayıtları")

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H%M%S")
        ts_id = int(time.time())

        if auto_save:
            os.makedirs(videos_dir, exist_ok=True)
            self.out_file_path = os.path.join(videos_dir, f"{t('video_prefix')} {now_str}.mp4")
            self.raw_video_path = os.path.join(videos_dir, f"raw_rec_{ts_id}.mp4")
        else:
            temp_dir = tempfile.gettempdir()
            self.out_file_path = os.path.join(temp_dir, f"recording_temp_{ts_id}.mp4")
            self.raw_video_path = self.out_file_path

        self.audio_temp_path = os.path.join(tempfile.gettempdir(), f"audio_rec_{ts_id}.wav")

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self.writer = cv2.VideoWriter(self.raw_video_path, fourcc, 24.0, (self.width, self.height))

        self.is_recording = True
        self.start_time = time.time()

        # Video karesi yakalama iş parçacığı
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()

        # Mikrofon ses kaydı iş parçacığı
        if AUDIO_AVAILABLE:
            self.audio_thread = threading.Thread(target=self._audio_capture_loop, daemon=True)
            self.audio_thread.start()

        # Kayıt denetim çubuğu ve vurgulama çerçevesini aç
        self._show_floating_bar()

    def _capture_loop(self):
        """mss ile sürekli kare yakalayıp video dosyasına yazar (~24 FPS)."""
        grab_box = {
            "left": self.bbox["left"],
            "top": self.bbox["top"],
            "width": self.width,
            "height": self.height
        }
        with mss.mss() as sct:
            while self.is_recording:
                loop_start = time.time()
                try:
                    sct_img = sct.grab(grab_box)
                    frame = np.array(sct_img)[:, :, :3]  # BGR
                    if self.writer and self.writer.isOpened():
                        self.writer.write(frame)
                except Exception as e:
                    print(f"Kare yakalama hatası: {e}")
                    break

                elapsed = time.time() - loop_start
                sleep_time = max(0.001, (1.0 / 24.0) - elapsed)
                time.sleep(sleep_time)

        if self.writer:
            try:
                self.writer.release()
            except Exception:
                pass
            self.writer = None

    def _audio_capture_loop(self):
        """sounddevice ile mikrofon sesini kaydeder."""
        sample_rate = 44100
        channels = 1
        try:
            with wave.open(self.audio_temp_path, "wb") as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)

                def callback(indata, frames, time_info, status):
                    if self.is_recording and self.mic_enabled:
                        data = (indata * 32767).astype(np.int16).tobytes()
                        wf.writeframes(data)
                    elif self.is_recording and not self.mic_enabled:
                        wf.writeframes(bytes(frames * channels * 2))

                with sd.InputStream(samplerate=sample_rate, channels=channels, callback=callback):
                    while self.is_recording:
                        time.sleep(0.1)
        except Exception as e:
            print(f"Ses akışı hatası: {e}")

    def _create_recording_border(self):
        """Kayıt edilen ekran alanının etrafında belirgin kırmızı/turuncu bir çerçeve gösterir."""
        pad = 3
        bx = self.bbox["left"]
        by = self.bbox["top"]
        bw = self.width
        bh = self.height

        parent = self.bar_window if self.bar_window else self.master
        self.border_window = tk.Toplevel(parent)
        self.border_window.overrideredirect(True)
        self.border_window.attributes("-topmost", True)
        self.border_window.attributes("-transparentcolor", "#010101")
        self.border_window.configure(bg="#010101")

        win_w = bw + pad * 2
        win_h = bh + pad * 2
        win_x = bx - pad
        win_y = by - pad
        self.border_window.geometry(f"{win_w}x{win_h}+{win_x}+{win_y}")

        canvas = tk.Canvas(
            self.border_window,
            width=win_w,
            height=win_h,
            bg="#010101",
            highlightthickness=0,
            bd=0
        )
        canvas.pack(fill=tk.BOTH, expand=True)

        # Kırmızı kayıt çerçevesi
        canvas.create_rectangle(
            1, 1, win_w - 2, win_h - 2,
            outline="#FF3B30",
            width=pad
        )

        # Köşe vurguları (Windows 11 Snipping Tool stili)
        L = min(22, max(8, win_w // 5), max(8, win_h // 5))
        c_color = "#FF8077"
        canvas.create_line(1, 1, 1 + L, 1, fill=c_color, width=4)
        canvas.create_line(1, 1, 1, 1 + L, fill=c_color, width=4)
        canvas.create_line(win_w - 2 - L, 1, win_w - 2, 1, fill=c_color, width=4)
        canvas.create_line(win_w - 2, 1, win_w - 2, 1 + L, fill=c_color, width=4)
        canvas.create_line(1, win_h - 2 - L, 1, win_h - 2, fill=c_color, width=4)
        canvas.create_line(1, win_h - 2, 1 + L, win_h - 2, fill=c_color, width=4)
        canvas.create_line(win_w - 2 - L, win_h - 2, win_w - 2, win_h - 2, fill=c_color, width=4)
        canvas.create_line(win_w - 2, win_h - 2 - L, win_w - 2, win_h - 2, fill=c_color, width=4)

        # Tıklamaları arkadaki pencerelere doğrudan geçirmek için WS_EX_TRANSPARENT ayarla
        try:
            import ctypes
            user32 = ctypes.windll.user32
            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x00080000
            WS_EX_TRANSPARENT = 0x00000020
            hwnd = user32.GetParent(self.border_window.winfo_id()) or self.border_window.winfo_id()
            styles = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, styles | WS_EX_TRANSPARENT | WS_EX_LAYERED)
        except Exception as e:
            print(f"Click-through ayarlama hatası: {e}")

        self.border_window.deiconify()
        self.border_window.lift()

    def _show_floating_bar(self):
        """1. Ekranda ortalanan modern Windows 11 kayıt denetim çubuğu."""
        if self.master:
            self.bar_window = ctk.CTkToplevel(self.master)
        else:
            self.bar_window = ctk.CTk()

        self.bar_window.overrideredirect(True)
        self.bar_window.attributes("-topmost", True)
        self.bar_window.configure(fg_color="#181818")

        bar_w = 400
        bar_h = 48

        # 1. Monitör koordinatlarını alarak çift ekran sınırında açılmasını engelle
        from snipping_overlay import get_primary_monitor
        mon = get_primary_monitor()
        pos_x = mon["left"] + (mon["width"] - bar_w) // 2
        pos_y = mon["top"] + 24
        self.bar_window.geometry(f"{bar_w}x{bar_h}+{pos_x}+{pos_y}")

        frame = ctk.CTkFrame(
            self.bar_window, fg_color="#202020", corner_radius=12,
            border_width=1, border_color="#333333"
        )
        frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Çubuğu fareyle sürüklenebilir yap
        def _start_drag(event):
            self._drag_x = event.x
            self._drag_y = event.y

        def _do_drag(event):
            deltax = event.x - getattr(self, "_drag_x", 0)
            deltay = event.y - getattr(self, "_drag_y", 0)
            new_x = self.bar_window.winfo_x() + deltax
            new_y = self.bar_window.winfo_y() + deltay
            self.bar_window.geometry(f"+{new_x}+{new_y}")

        frame.bind("<ButtonPress-1>", _start_drag)
        frame.bind("<B1-Motion>", _do_drag)

        # Kırmızı kayıt noktası ve süre
        self.lbl_timer = ctk.CTkLabel(
            frame, text="🔴  00:00",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#FF3B30"
        )
        self.lbl_timer.pack(side=tk.LEFT, padx=(14, 8))
        self.lbl_timer.bind("<ButtonPress-1>", _start_drag)
        self.lbl_timer.bind("<B1-Motion>", _do_drag)

        # Çözünürlük Rozeti
        lbl_res = ctk.CTkLabel(
            frame, text=f"{self.width}×{self.height}",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#888888"
        )
        lbl_res.pack(side=tk.LEFT, padx=(0, 10))
        lbl_res.bind("<ButtonPress-1>", _start_drag)
        lbl_res.bind("<B1-Motion>", _do_drag)

        # Mikrofon Aç/Kapat Butonu
        def _toggle_mic():
            self.mic_enabled = not self.mic_enabled
            ico = "mic" if self.mic_enabled else "mic_off"
            self.btn_mic.configure(image=icon_assets.get_icon_ctk(ico, (18, 18)))

        mic_ico = "mic" if self.mic_enabled else "mic_off"
        self.btn_mic = ctk.CTkButton(
            frame,
            image=icon_assets.get_icon_ctk(mic_ico, (18, 18)),
            text="",
            width=32,
            height=32,
            fg_color="transparent",
            hover_color="#333333",
            corner_radius=6,
            command=_toggle_mic
        )
        self.btn_mic.pack(side=tk.LEFT, padx=3)

        # Sistem Sesi Aç/Kapat Butonu
        def _toggle_speaker():
            self.sys_audio_enabled = not self.sys_audio_enabled
            ico = "speaker" if self.sys_audio_enabled else "speaker_off"
            self.btn_speaker.configure(image=icon_assets.get_icon_ctk(ico, (18, 18)))

        spk_ico = "speaker" if self.sys_audio_enabled else "speaker_off"
        self.btn_speaker = ctk.CTkButton(
            frame,
            image=icon_assets.get_icon_ctk(spk_ico, (18, 18)),
            text="",
            width=32,
            height=32,
            fg_color="transparent",
            hover_color="#333333",
            corner_radius=6,
            command=_toggle_speaker
        )
        self.btn_speaker.pack(side=tk.LEFT, padx=3)

        # [ ⏹️ Kaydı Bitir ] Butonu
        self.btn_stop = ctk.CTkButton(
            frame, text=t("video_stop"),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#D83B01", hover_color="#EA4A1F",
            corner_radius=8, width=76, height=30,
            command=self.stop_recording
        )
        self.btn_stop.pack(side=tk.LEFT, padx=(8, 4))

        # [ ✕ İptal ] Butonu
        btn_cancel = ctk.CTkButton(
            frame, text="✕",
            font=ctk.CTkFont(size=12),
            fg_color="transparent", hover_color="#333333",
            corner_radius=6, width=28, height=30,
            command=self.cancel_recording
        )
        btn_cancel.pack(side=tk.LEFT, padx=3)

        # Kayıt edilen ekran alanını vurgulayan şeffaf çerçeveyi oluştur
        self._create_recording_border()

        self.bar_window.deiconify()
        self.bar_window.lift()
        self.bar_window.focus_force()

        self._update_timer()
        if not self.master:
            self.bar_window.mainloop()

    def _update_timer(self):
        if not self.is_recording or not self.bar_window:
            return

        elapsed = int(time.time() - self.start_time)
        mins = elapsed // 60
        secs = elapsed % 60
        try:
            self.lbl_timer.configure(text=f"🔴  {mins:02d}:{secs:02d}")
            self.bar_window.after(1000, self._update_timer)
        except Exception:
            pass

    def stop_recording(self):
        """Kaydı tamamlar, ses ve videoyu birleştirir ve dosyayı kaydeder."""
        if hasattr(self, "btn_stop") and self.btn_stop:
            try:
                self.btn_stop.configure(text=f"⏳ {t('video_saving')}", state="disabled")
            except Exception:
                pass

        self.is_recording = False

        # İş parçacıklarının güvenle tamamlanmasını bekle (dosya kilitlerini çözmek için şart!)
        if self.capture_thread and self.capture_thread.is_alive():
            try:
                self.capture_thread.join(timeout=3.0)
            except Exception:
                pass

        if self.audio_thread and self.audio_thread.is_alive():
            try:
                self.audio_thread.join(timeout=2.0)
            except Exception:
                pass

        if self.writer:
            try:
                self.writer.release()
            except Exception:
                pass
            self.writer = None

        # Arayüz pencerelerini kapat
        if hasattr(self, "border_window") and self.border_window:
            try:
                self.border_window.destroy()
                self.border_window = None
            except Exception:
                pass

        if hasattr(self, "bar_window") and self.bar_window:
            try:
                self.bar_window.withdraw()
                self.bar_window.destroy()
                self.bar_window = None
            except Exception:
                pass

        # Video dosyasını hazırla ve sesle birleştir
        try:
            ffmpeg_exe = shutil.which("ffmpeg")
            has_audio = (
                self.audio_temp_path
                and os.path.exists(self.audio_temp_path)
                and os.path.getsize(self.audio_temp_path) > 1000
            )

            if ffmpeg_exe and has_audio and self.raw_video_path and os.path.exists(self.raw_video_path):
                merged_target = self.raw_video_path.replace(".mp4", "_merged.mp4")
                cmd = [
                    ffmpeg_exe, "-y",
                    "-i", self.raw_video_path,
                    "-i", self.audio_temp_path,
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-strict", "-2",
                    "-shortest",
                    merged_target
                ]
                creationflags = 0x08000000 if os.name == "nt" else 0
                res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=creationflags)
                if res.returncode == 0 and os.path.exists(merged_target) and os.path.getsize(merged_target) > 0:
                    try:
                        os.remove(self.raw_video_path)
                    except Exception:
                        pass
                    if os.path.exists(self.out_file_path):
                        try:
                            os.remove(self.out_file_path)
                        except Exception:
                            pass
                    shutil.move(merged_target, self.out_file_path)
                else:
                    if os.path.exists(merged_target):
                        try:
                            os.remove(merged_target)
                        except Exception:
                            pass
                    if self.raw_video_path != self.out_file_path and os.path.exists(self.raw_video_path):
                        if os.path.exists(self.out_file_path):
                            try:
                                os.remove(self.out_file_path)
                            except Exception:
                                pass
                        shutil.move(self.raw_video_path, self.out_file_path)
            else:
                if self.raw_video_path and os.path.exists(self.raw_video_path):
                    if self.raw_video_path != self.out_file_path:
                        if os.path.exists(self.out_file_path):
                            try:
                                os.remove(self.out_file_path)
                            except Exception:
                                pass
                        shutil.move(self.raw_video_path, self.out_file_path)
        except Exception as e:
            print(f"Video işleme hatası: {e}")
            if self.raw_video_path and os.path.exists(self.raw_video_path):
                try:
                    if self.raw_video_path != self.out_file_path:
                        shutil.copy(self.raw_video_path, self.out_file_path)
                except Exception:
                    pass

        # Geçici ses dosyasını temizle
        if self.audio_temp_path and os.path.exists(self.audio_temp_path):
            try:
                os.remove(self.audio_temp_path)
            except Exception:
                pass

        # Otomatik kaydetme kapalıysa kullanıcıya nereye kaydedeceğini sor
        auto_save = config.get("auto_save_video", True)
        if not auto_save and self.out_file_path and os.path.exists(self.out_file_path):
            save_dest = filedialog.asksaveasfilename(
                title=t("video_save_title"),
                defaultextension=".mp4",
                filetypes=[("MP4 Video", "*.mp4")]
            )
            if save_dest:
                shutil.move(self.out_file_path, save_dest)
                self.out_file_path = save_dest

        # Otomatik panoya kopyalama
        if config.get("auto_copy_video", True) and self.out_file_path and os.path.exists(self.out_file_path):
            copy_file_to_clipboard(self.out_file_path)

        # 1. Ana pencereyi HER DURUMDA hemen geri getir
        if self.on_finish_callback:
            try:
                self.on_finish_callback(self.out_file_path)
            except Exception as e:
                print(f"Bitiş çağrısı hatası: {e}")

        # 2. "Düzenlenen ekran kayıtlarını kaydetmek için sor" veya bildirim diyaloğu
        if config.get("ask_save_edited_video", True):
            if self.out_file_path and os.path.exists(self.out_file_path):
                self._show_finished_dialog(self.out_file_path)

    def cancel_recording(self):
        """Kaydı iptal eder ve geçici dosyayı siler."""
        self.is_recording = False

        if self.capture_thread and self.capture_thread.is_alive():
            try:
                self.capture_thread.join(timeout=2.0)
            except Exception:
                pass

        if self.audio_thread and self.audio_thread.is_alive():
            try:
                self.audio_thread.join(timeout=2.0)
            except Exception:
                pass

        if self.writer:
            try:
                self.writer.release()
            except Exception:
                pass
            self.writer = None

        if hasattr(self, "border_window") and self.border_window:
            try:
                self.border_window.destroy()
                self.border_window = None
            except Exception:
                pass

        if hasattr(self, "bar_window") and self.bar_window:
            try:
                self.bar_window.destroy()
                self.bar_window = None
            except Exception:
                pass

        for p in [self.raw_video_path, self.audio_temp_path, self.out_file_path]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

        if self.on_finish_callback:
            try:
                self.on_finish_callback(None)
            except Exception as e:
                print(f"İptal çağrısı hatası: {e}")

    def _show_finished_dialog(self, file_path):
        """Kayıt bittiğinde açılan şık bildirim penceresi."""
        parent = self.master if self.master else None
        if parent:
            dlg = ctk.CTkToplevel(parent)
        else:
            dlg = ctk.CTk()

        dlg.title(t("video_finished_title"))
        dlg.geometry("460x220")
        dlg.resizable(False, False)
        dlg.configure(fg_color="#202020")
        dlg.attributes("-topmost", True)

        from snipping_overlay import get_primary_monitor
        mon = get_primary_monitor()
        dx = mon["left"] + (mon["width"] - 460) // 2
        dy = mon["top"] + (mon["height"] - 220) // 2
        dlg.geometry(f"460x220+{dx}+{dy}")
        dlg.protocol("WM_DELETE_WINDOW", dlg.destroy)
        dlg.deiconify()
        dlg.lift()
        dlg.focus_force()

        card = ctk.CTkFrame(dlg, fg_color="#282828", corner_radius=12, border_width=1, border_color="#383838")
        card.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

        lbl_title = ctk.CTkLabel(
            card, text=f"🎬  {t('video_finished_heading')}",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#0F9D58"
        )
        lbl_title.pack(pady=(16, 4))

        lbl_path = ctk.CTkLabel(
            card, text=f"{os.path.basename(file_path)}",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#AAAAAA"
        )
        lbl_path.pack(pady=(0, 6))

        copied_txt = t("video_also_copied") if config.get("auto_copy_video", True) else ""
        lbl_copied = ctk.CTkLabel(
            card, text=copied_txt,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#60CDFF"
        )
        lbl_copied.pack(pady=(0, 14))

        btn_box = ctk.CTkFrame(card, fg_color="transparent")
        btn_box.pack(pady=(0, 12))

        btn_play = ctk.CTkButton(
            btn_box, text=f"▶️  {t('video_open_file')}",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#0078D4", hover_color="#0063B1",
            corner_radius=8, width=120, height=34,
            command=lambda: os.startfile(file_path)
        )
        btn_play.pack(side=tk.LEFT, padx=6)

        btn_folder = ctk.CTkButton(
            btn_box, text=f"📁  {t('video_open_folder')}",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="#333333", hover_color="#444444",
            corner_radius=8, width=110, height=34,
            command=lambda: os.system(f'explorer /select,"{file_path}"')
        )
        btn_folder.pack(side=tk.LEFT, padx=6)

        def _copy_again():
            copy_file_to_clipboard(file_path)
            btn_copy.configure(text=f"✓ {t('copied_toast')}")

        btn_copy = ctk.CTkButton(
            btn_box, text=f"📋 {t('btn_copy')}",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="#333333", hover_color="#444444",
            corner_radius=8, width=90, height=34,
            command=_copy_again
        )
        btn_copy.pack(side=tk.LEFT, padx=6)

        btn_close = ctk.CTkButton(
            btn_box, text="✕",
            fg_color="transparent", hover_color="#333333",
            corner_radius=6, width=32, height=34,
            command=dlg.destroy
        )
        btn_close.pack(side=tk.LEFT, padx=4)

        if not parent:
            dlg.mainloop()


def start_video_recording(bbox: dict, on_finish=None, master=None):
    """Video kaydediciyi başlatır."""
    recorder = VideoRecorderController(bbox, on_finish_callback=on_finish, master=master)
    recorder.start_recording()
    return recorder

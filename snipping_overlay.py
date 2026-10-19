"""
Ekran Alıntısı Aracı - Modern Ekran Kırpma Arayüzü (Snipping Overlay)
========================================================
Windows 11 Snipping Tool birebir kırpma modları:
1. Dikdörtgen (rect)
2. Pencere (window)
3. Tam Ekran (fullscreen)
4. Serbest Form (freeform)
5. Metin Ayıklama (ocr)

Çoklu monitör desteklidir; araç çubuğu her zaman 1. Ekranın (Birincil Monitör)
ortasında konumlanır (iki ekranın birleşim yerine taşmaz).
"""

import ctypes
from ctypes import wintypes
import tkinter as tk
import customtkinter as ctk
from PIL import ImageTk, Image, ImageDraw
import mss

import icon_assets
from i18n import t
from screen_capture import capture_all_screens, play_shutter_sound

user32 = ctypes.windll.user32
WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)


def get_primary_monitor():
    """1. Ekranın (Birincil Monitör) koordinatlarını döndürür."""
    with mss.mss() as sct:
        if len(sct.monitors) > 1:
            return sct.monitors[1]
        return sct.monitors[0]


def get_visible_window_rects():
    """Masaüstündeki açık pencerelerin koordinatlarını (left, top, right, bottom) listeler."""
    rects = []
    def enum_proc(hwnd, lp):
        if user32.IsWindowVisible(hwnd) and not user32.IsIconic(hwnd):
            r = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(r))
            w = r.right - r.left
            h = r.bottom - r.top
            if w > 120 and h > 80:
                rects.append((r.left, r.top, r.right, r.bottom))
        return True
    try:
        user32.EnumWindows(WNDENUMPROC(enum_proc), 0)
    except Exception:
        pass
    return rects


class SnippingOverlay:
    def __init__(self, master, on_snip_completed=None, on_video_bbox=None, on_cancel=None, mode="rect", is_video=False):
        self.master = master
        self.on_snip_completed = on_snip_completed
        self.on_video_bbox = on_video_bbox
        self.on_cancel = on_cancel
        self.mode = mode
        self.is_video = is_video

        self.top = None
        self.canvas = None
        self.orig_image = None
        self.dark_image = None
        self.photo_dark = None
        self.mon_info = None

        self.start_x = 0
        self.start_y = 0
        self.rect_id = None
        self.badge_bg_id = None
        self.badge_txt_id = None
        self.points = []
        self.freeform_line_ids = []

        self.window_rects = []
        self.hover_win_id = None
        self.hover_selected_rect = None
        self.bar_frame = None

    def start(self):
        self.window_rects = get_visible_window_rects()
        self.orig_image, self.mon_info = capture_all_screens()

        # Tam ekran modundaysa doğrudan tamamla
        if self.mode == "fullscreen":
            if self.is_video and self.on_video_bbox:
                self.on_video_bbox(self.mon_info)
                return
            elif self.on_snip_completed:
                play_shutter_sound()
                self.on_snip_completed(self.orig_image)
                return

        self.dark_image = self.orig_image.point(lambda p: int(p * 0.60))

        self.top = tk.Toplevel(self.master)
        self.top.overrideredirect(True)
        self.top.attributes("-topmost", True)
        self.top.configure(cursor="crosshair")

        w = self.mon_info["width"]
        h = self.mon_info["height"]
        left = self.mon_info["left"]
        top = self.mon_info["top"]

        self.top.geometry(f"{w}x{h}+{left}+{top}")

        self.canvas = tk.Canvas(self.top, width=w, height=h, highlightthickness=0, bg="#000000")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.photo_dark = ImageTk.PhotoImage(self.dark_image)
        self.canvas.create_image(0, 0, image=self.photo_dark, anchor="nw")

        # Üst araç çubuğunu 1. Ekranın tam ortasında oluştur
        self._build_modern_bar()

        # Fare ve klavye olayları
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.top.bind("<Escape>", lambda e: self._do_cancel())

        self.top.lift()
        self.top.focus_force()

    def _build_modern_bar(self):
        """Araç çubuğunu iki ekranın arasına değil, 1. Ekranın (Birincil Monitör) tam ortasına yerleştirir."""
        if hasattr(self, "bar_frame") and self.bar_frame:
            try:
                self.bar_frame.destroy()
            except Exception:
                pass

        mon1 = get_primary_monitor()
        if self.is_video:
            bar_w = 286
            modes = [
                (t("overlay_record_area"), "rect", "rect", 120),
                (t("overlay_fullscreen"), "fullscreen", "fullscreen", 110),
            ]
        else:
            bar_w = 476
            modes = [
                (t("overlay_rect"), "rect", "rect", 110),
                (t("overlay_window"), "window", "window", 94),
                (t("overlay_fullscreen"), "fullscreen", "fullscreen", 104),
                (t("overlay_freeform"), "freeform", "freeform", 90),
            ]
        bar_h = 44

        # 1. Ekranın (Monitor 1) kanvas koordinatlarına göre sol konumu
        mon1_canvas_left = mon1["left"] - self.mon_info["left"]
        bar_x = mon1_canvas_left + (mon1["width"] - bar_w) // 2
        bar_y = 18

        self.bar_frame = ctk.CTkFrame(
            self.canvas,
            fg_color="#1F1F1F",
            border_width=1,
            border_color="#383838",
            corner_radius=8,
            width=bar_w,
            height=bar_h
        )
        self.bar_frame.pack_propagate(False)

        for label_text, mode_val, ico_name, btn_w in modes:
            is_active = (self.mode == mode_val)
            accent = "#D83B01" if self.is_video else "#0078D4"
            fg_col = accent if is_active else "transparent"
            hover_col = "#0063B1" if is_active else "#2E2E2E"

            btn = ctk.CTkButton(
                self.bar_frame,
                image=icon_assets.get_icon_ctk(ico_name, (18, 18)),
                text=f" {label_text}",
                compound="left",
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color="#FFFFFF",
                fg_color=fg_col,
                hover_color=hover_col,
                corner_radius=6,
                width=btn_w,
                height=32,
                command=lambda m=mode_val: self._on_mode_select(m)
            )
            btn.pack(side=tk.LEFT, padx=3, pady=6)

        # İptal (✕) Butonu
        btn_close = ctk.CTkButton(
            self.bar_frame,
            text="✕",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#FF6B6B",
            fg_color="transparent",
            hover_color="#C42B1C",
            corner_radius=6,
            width=36,
            height=32,
            command=self._do_cancel
        )
        btn_close.pack(side=tk.LEFT, padx=(3, 4), pady=6)

        self.canvas.create_window(bar_x, bar_y, window=self.bar_frame, anchor="nw")

    def _on_mode_select(self, mode):
        if mode == "cancel":
            self._do_cancel()
        elif mode == "fullscreen":
            self._close_window()
            if self.is_video and self.on_video_bbox:
                self.on_video_bbox(self.mon_info)
            elif self.on_snip_completed:
                play_shutter_sound()
                self.on_snip_completed(self.orig_image)
        else:
            self.mode = mode
            self.start_x = 0
            self.start_y = 0
            self._clear_selection()
            self._build_modern_bar()

    def _on_motion(self, event):
        if self.mode == "window":
            screen_x = event.x + self.mon_info["left"]
            screen_y = event.y + self.mon_info["top"]

            best_rect = None
            min_area = float("inf")
            for r in self.window_rects:
                if r[0] <= screen_x <= r[2] and r[1] <= screen_y <= r[3]:
                    area = (r[2] - r[0]) * (r[3] - r[1])
                    if area < min_area:
                        min_area = area
                        best_rect = r

            if best_rect:
                cx1 = best_rect[0] - self.mon_info["left"]
                cy1 = best_rect[1] - self.mon_info["top"]
                cx2 = best_rect[2] - self.mon_info["left"]
                cy2 = best_rect[3] - self.mon_info["top"]
                self.hover_selected_rect = (cx1, cy1, cx2, cy2)

                if not self.hover_win_id:
                    self.hover_win_id = self.canvas.create_rectangle(
                        cx1, cy1, cx2, cy2, outline="#60CDFF", width=3
                    )
                else:
                    self.canvas.coords(self.hover_win_id, cx1, cy1, cx2, cy2)
            else:
                if self.hover_win_id:
                    self.canvas.delete(self.hover_win_id)
                    self.hover_win_id = None
                self.hover_selected_rect = None

    def _on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y

        if self.mode in ("rect", "ocr"):
            self._clear_selection()
            accent = "#D83B01" if self.is_video else "#0078D4"
            self.rect_id = self.canvas.create_rectangle(
                self.start_x, self.start_y, self.start_x, self.start_y,
                outline=accent, width=2
            )
            self.badge_bg_id = self.canvas.create_rectangle(
                self.start_x, self.start_y - 24, self.start_x + 100, self.start_y - 4,
                fill="#181818", outline=accent, width=1
            )
            self.badge_txt_id = self.canvas.create_text(
                self.start_x + 50, self.start_y - 14,
                text="", fill="#FFFFFF", font=("Segoe UI", 8, "bold")
            )

        elif self.mode == "freeform" and not self.is_video:
            self._clear_selection()
            self.points = [(event.x, event.y)]

        elif self.mode == "window":
            if self.hover_selected_rect:
                cx1, cy1, cx2, cy2 = self.hover_selected_rect
                x1 = max(0, min(cx1, cx2))
                y1 = max(0, min(cy1, cy2))
                x2 = min(self.orig_image.width, max(cx1, cx2))
                y2 = min(self.orig_image.height, max(cy1, cy2))
                w = x2 - x1
                h = y2 - y1
                if w > 20 and h > 20:
                    self._close_window()
                    if self.is_video and self.on_video_bbox:
                        bbox = {
                            "left": x1 + self.mon_info["left"],
                            "top": y1 + self.mon_info["top"],
                            "width": w,
                            "height": h
                        }
                        self.on_video_bbox(bbox)
                    elif self.on_snip_completed:
                        play_shutter_sound()
                        cropped = self.orig_image.crop((x1, y1, x2, y2))
                        self.on_snip_completed(cropped)
                    return
            self._clear_selection()
            accent = "#D83B01" if self.is_video else "#0078D4"
            self.rect_id = self.canvas.create_rectangle(
                self.start_x, self.start_y, self.start_x, self.start_y,
                outline=accent, width=2
            )

    def _on_drag(self, event):
        if self.mode in ("rect", "ocr", "window") and self.rect_id:
            cur_x, cur_y = event.x, event.y
            self.canvas.coords(self.rect_id, self.start_x, self.start_y, cur_x, cur_y)
            w = abs(cur_x - self.start_x)
            h = abs(cur_y - self.start_y)

            if self.badge_bg_id and self.badge_txt_id:
                min_x = min(self.start_x, cur_x)
                min_y = min(self.start_y, cur_y)
                bx1 = min_x
                by1 = min_y - 26 if min_y > 35 else min_y + 10
                self.canvas.coords(self.badge_bg_id, bx1, by1, bx1 + 100, by1 + 22)
                self.canvas.coords(self.badge_txt_id, bx1 + 50, by1 + 11)
                self.canvas.itemconfig(self.badge_txt_id, text=f"{w} × {h} px")

        elif self.mode == "freeform" and not self.is_video:
            self.points.append((event.x, event.y))
            if len(self.points) > 1:
                p1 = self.points[-2]
                p2 = self.points[-1]
                line_id = self.canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill="#0078D4", width=3)
                self.freeform_line_ids.append(line_id)

    def _on_release(self, event):
        end_x, end_y = event.x, event.y

        if self.mode in ("rect", "ocr", "window") and self.rect_id:
            x1 = min(self.start_x, end_x)
            y1 = min(self.start_y, end_y)
            x2 = max(self.start_x, end_x)
            y2 = max(self.start_y, end_y)
            w = x2 - x1
            h = y2 - y1

            if w > 16 and h > 16:
                self._close_window()
                if self.is_video and self.on_video_bbox:
                    bbox = {
                        "left": x1 + self.mon_info["left"],
                        "top": y1 + self.mon_info["top"],
                        "width": w,
                        "height": h
                    }
                    self.on_video_bbox(bbox)
                elif self.on_snip_completed:
                    play_shutter_sound()
                    cropped = self.orig_image.crop((x1, y1, x2, y2))
                    self.on_snip_completed(cropped)
            else:
                self._do_cancel()

        elif self.mode == "freeform" and not self.is_video and len(self.points) > 5:
            xs = [p[0] for p in self.points]
            ys = [p[1] for p in self.points]
            min_x = max(0, min(xs))
            min_y = max(0, min(ys))
            max_x = min(self.orig_image.width, max(xs))
            max_y = min(self.orig_image.height, max(ys))
            w = max_x - min_x
            h = max_y - min_y

            if w > 16 and h > 16:
                self._close_window()
                play_shutter_sound()

                crop_box = self.orig_image.crop((min_x, min_y, max_x, max_y))
                mask = Image.new("L", (w, h), 0)
                rel_points = [(p[0] - min_x, p[1] - min_y) for p in self.points]
                if rel_points[0] != rel_points[-1]:
                    rel_points.append(rel_points[0])

                ImageDraw.Draw(mask).polygon(rel_points, fill=255)

                final_img = Image.new("RGB", (w, h), (255, 255, 255))
                final_img.paste(crop_box, (0, 0), mask=mask)

                if self.on_snip_completed:
                    self.on_snip_completed(final_img)
            else:
                self._do_cancel()
        else:
            self._do_cancel()

    def _clear_selection(self):
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            self.rect_id = None
        if self.badge_bg_id:
            self.canvas.delete(self.badge_bg_id)
            self.badge_bg_id = None
        if self.badge_txt_id:
            self.canvas.delete(self.badge_txt_id)
            self.badge_txt_id = None
        if self.hover_win_id:
            self.canvas.delete(self.hover_win_id)
            self.hover_win_id = None
        for lid in self.freeform_line_ids:
            self.canvas.delete(lid)
        self.freeform_line_ids.clear()
        self.points.clear()

    def _do_cancel(self):
        self._close_window()
        if self.on_cancel:
            self.on_cancel()

    def _close_window(self):
        try:
            if hasattr(self, "bar_frame") and self.bar_frame:
                self.bar_frame.destroy()
                self.bar_frame = None
            if self.top:
                self.top.destroy()
                self.top = None
        except Exception:
            pass


def open_snipper(master, on_completed=None, on_video_bbox=None, on_cancel=None, mode="rect", is_video=False):
    overlay = SnippingOverlay(
        master=master,
        on_snip_completed=on_completed,
        on_video_bbox=on_video_bbox,
        on_cancel=on_cancel,
        mode=mode,
        is_video=is_video
    )
    overlay.start()

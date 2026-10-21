"""
Ekran Alıntısı Aracı - Windows 11 Birebir Ekran Alıntısı Aracı
==================================================
Windows 11 Snipping Tool (Ekran Alıntısı Aracı) tasarımının birebir klonudur.

Özellikler:
1. 📷 Fotoğraf Kırpma & 🎥 Ekran Video Kaydı
2. 🔲 Dikdörtgen, 🪟 Pencere, 🖥️ Tam Ekran, ☁️ Serbest Form Kırpma Modları
3. 🔤 Google Lens Yapay Zeka OCR Metin Ayıklama (Türkçe Destekli)
4. 🔍 Doğrudan Google Lens ile Görsel Arama (Bing Yerine)
5. 📋 64-bit Windows Pano Kopyalama & Çizim Araçları (Kalem, Şeffaf Vurgulayıcı, Silgi)
6. ⏱️ 3s, 5s, 10s Gecikmeli Ekran Alıntısı
7. ⚙️ Birebir Windows 11 Fluent Ayarlar Paneli (Otomatik Kayıt, Klasör Seçimi, Temalar, Ses vb.)
"""

import os
import sys
import datetime
import threading
import webbrowser
from tkinter import filedialog, messagebox, colorchooser
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageTk, ImageEnhance
import mss

import icon_assets
import i18n
from i18n import t
from config import config
import default_app_manager
from notification import toast
from google_lens import search_image_in_google_lens
from screen_capture import copy_image_to_clipboard, play_shutter_sound
from snipping_overlay import open_snipper
from ocr_engine import extract_text_from_image
from video_recorder import start_video_recording

# Windows 11 Fluent Koyu / Açık Tema Ayarı
initial_theme = config.get("app_theme", "dark")
ctk.set_appearance_mode(initial_theme)
ctk.set_default_color_theme("blue")


# =============================================================================
# BAĞIMSIZ EDİTÖR PENCERESİ (BİRDEN FAZLA PENCERE DESTEĞİ İÇİN)
# =============================================================================
class SnippingEditorWindow(ctk.CTkToplevel):
    """'Birden fazla pencere' ayarı açıkken açılan bağımsız düzenleyici penceresi."""
    def __init__(self, parent, img: Image.Image, on_new_snip=None, saved_filepath=None):
        super().__init__(parent)
        self.title(t("app_title"))
        self.geometry("1040x680")
        self.minsize(820, 520)
        self.configure(fg_color="#202020")
        self.on_new_snip_callback = on_new_snip
        self.saved_filepath = saved_filepath

        icon_assets.apply_window_icon(self)

        self.current_image = img.copy()
        self.draw_image = img.copy()
        self.history = [self.draw_image.copy()]
        self.active_tool = "none"
        self.pen_color = "#E81123"
        self.pen_size = 4
        self.last_x = None
        self.last_y = None
        self.scale = 1.0
        self.img_x = 0
        self.img_y = 0
        self.highlighter_pts = []
        self._has_saved = False

        self._build_ui()
        self._bind_keys()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _bind_keys(self):
        self.bind("<Control-c>", lambda e: self.on_copy_clipboard())
        self.bind("<Control-s>", lambda e: self.on_save_file())
        self.bind("<Control-g>", lambda e: self.on_google_lens_search())
        self.bind("<Control-z>", lambda e: self.on_undo())

    def _build_ui(self):
        # Üst Araç Çubuğu
        self.editor_bar = ctk.CTkFrame(self, fg_color="#202020", height=46, corner_radius=0)
        self.editor_bar.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(8, 4))

        if self.on_new_snip_callback:
            self.btn_new = ctk.CTkButton(
                self.editor_bar, text=t("btn_new"),
                font=ctk.CTkFont(family="Segoe UI", size=13),
                text_color="#FFFFFF", fg_color="#2B2B2B", hover_color="#363636",
                border_width=1, border_color="#383838", corner_radius=6,
                width=80, height=34,
                command=self._on_new_click
            )
            self.btn_new.pack(side=tk.LEFT, padx=(0, 6))

            sep1 = ctk.CTkFrame(self.editor_bar, width=1, height=20, fg_color="#383838")
            sep1.pack(side=tk.LEFT, padx=4)

        # Çizim Araçları
        self.btn_pen = ctk.CTkButton(
            self.editor_bar, image=icon_assets.get_icon_ctk("pen", (18, 18)),
            text=t("tool_pen"), compound="left", width=74, height=34, corner_radius=6,
            fg_color="#0078D4" if self.active_tool == "pen" else "#252525",
            hover_color="#383838", font=ctk.CTkFont(family="Segoe UI", size=12),
            command=lambda: self._select_tool("pen")
        )
        self.btn_pen.pack(side=tk.LEFT, padx=3)

        self.btn_highlighter = ctk.CTkButton(
            self.editor_bar, image=icon_assets.get_icon_ctk("highlighter", (18, 18)),
            text=t("tool_highlighter"), compound="left", width=78, height=34, corner_radius=6,
            fg_color="#0078D4" if self.active_tool == "highlighter" else "#252525",
            hover_color="#383838", font=ctk.CTkFont(family="Segoe UI", size=12),
            command=lambda: self._select_tool("highlighter")
        )
        self.btn_highlighter.pack(side=tk.LEFT, padx=3)

        self.btn_eraser = ctk.CTkButton(
            self.editor_bar, image=icon_assets.get_icon_ctk("eraser", (18, 18)),
            text=t("tool_eraser"), compound="left", width=68, height=34, corner_radius=6,
            fg_color="#0078D4" if self.active_tool == "eraser" else "#252525",
            hover_color="#383838", font=ctk.CTkFont(family="Segoe UI", size=12),
            command=lambda: self._select_tool("eraser")
        )
        self.btn_eraser.pack(side=tk.LEFT, padx=3)

        self.btn_undo = ctk.CTkButton(
            self.editor_bar, image=icon_assets.get_icon_ctk("undo", (18, 18)),
            text="", width=34, height=34, corner_radius=6, fg_color="#252525", hover_color="#383838",
            command=self.on_undo
        )
        self.btn_undo.pack(side=tk.LEFT, padx=3)

        sep2 = ctk.CTkFrame(self.editor_bar, width=1, height=20, fg_color="#383838")
        sep2.pack(side=tk.LEFT, padx=6)

        # Metin Ayıkla (OCR)
        self.btn_ocr = ctk.CTkButton(
            self.editor_bar, image=icon_assets.get_icon_ctk("ocr", (18, 18)),
            text=t("btn_ocr"), compound="left",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#1F4E79", hover_color="#2E75B6", corner_radius=6,
            width=120, height=34, command=self.on_extract_text_ocr
        )
        self.btn_ocr.pack(side=tk.LEFT, padx=4)

        # Google Lens ile Görsel Ara (Ayar açıksa)
        if config.get("google_lens_enabled", True):
            self.btn_lens = ctk.CTkButton(
                self.editor_bar, image=icon_assets.get_icon_ctk("google_lens", (20, 20)),
                text=t("btn_lens"), compound="left",
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                fg_color="#0B3820", hover_color="#144F2E",
                border_width=1, border_color="#1A5935", corner_radius=6,
                width=172, height=34, command=self.on_google_lens_search
            )
            self.btn_lens.pack(side=tk.LEFT, padx=5)

        self.btn_combine = ctk.CTkButton(
            self.editor_bar, image=icon_assets.get_icon_ctk("combine", (18, 18)),
            text=t("btn_combine"), compound="left",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="#252525", hover_color="#383838", corner_radius=6,
            width=92, height=34, command=self.on_open_combiner
        )
        self.btn_combine.pack(side=tk.LEFT, padx=4)

        # Sağ Taraf: Kopyala, Kaydet, Kapat
        self.btn_back = ctk.CTkButton(
            self.editor_bar, text="✕", width=36, height=34, corner_radius=6,
            fg_color="transparent", hover_color="#C42B1C",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            command=self._on_close
        )
        self.btn_back.pack(side=tk.RIGHT)

        self.btn_save = ctk.CTkButton(
            self.editor_bar, image=icon_assets.get_icon_ctk("save", (18, 18)),
            text="", width=36, height=34, corner_radius=6, fg_color="#252525", hover_color="#383838",
            command=self.on_save_file
        )
        self.btn_save.pack(side=tk.RIGHT, padx=3)

        self.btn_copy = ctk.CTkButton(
            self.editor_bar, image=icon_assets.get_icon_ctk("copy", (18, 18)),
            text="", width=36, height=34, corner_radius=6, fg_color="#252525", hover_color="#383838",
            command=self.on_copy_clipboard
        )
        self.btn_copy.pack(side=tk.RIGHT, padx=3)

        # İnce Çizgi
        self.divider = ctk.CTkFrame(self, fg_color="#2D2D2D", height=1)
        self.divider.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(2, 0))

        # Görsel Alanı
        self.canvas_frame = ctk.CTkFrame(self, fg_color="#181818", corner_radius=0)
        self.canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=0, pady=0)

        self.canvas = tk.Canvas(self.canvas_frame, bg="#181818", highlightthickness=0, bd=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Alt Durum Çubuğu
        self.footer = ctk.CTkFrame(self, fg_color="#202020", height=28, corner_radius=0)
        self.footer.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=(0, 4))

        self.lbl_status = ctk.CTkLabel(
            self.footer, text=f"✓  {t('status_copied')}",
            font=ctk.CTkFont(family="Segoe UI", size=11), text_color="#0F9D58"
        )
        self.lbl_status.pack(side=tk.LEFT)

        w, h = self.current_image.size
        self.lbl_dim = ctk.CTkLabel(
            self.footer, text=f"{w} × {h} px",
            font=ctk.CTkFont(family="Segoe UI", size=11), text_color="#888888"
        )
        self.lbl_dim.pack(side=tk.RIGHT)

        # Canvas Etkileşim Olayları
        self.canvas.bind("<ButtonPress-1>", self._on_canvas_press)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.canvas.bind("<Configure>", lambda e: self._render_current_image())

        self.after(50, self._render_current_image)

    def _select_tool(self, tool_name):
        self.active_tool = "none" if self.active_tool == tool_name else tool_name
        self.btn_pen.configure(fg_color="#0078D4" if self.active_tool == "pen" else "#252525")
        self.btn_highlighter.configure(fg_color="#0078D4" if self.active_tool == "highlighter" else "#252525")
        self.btn_eraser.configure(fg_color="#0078D4" if self.active_tool == "eraser" else "#252525")
        self.canvas.configure(cursor="crosshair" if self.active_tool in ("pen", "highlighter", "eraser") else "")

    def _render_current_image(self, image_to_render=None):
        target = image_to_render if image_to_render is not None else self.draw_image
        if not hasattr(self, "canvas") or target is None:
            return

        self.canvas.delete("all")
        cw = self.canvas.winfo_width() or 800
        ch = self.canvas.winfo_height() or 500
        iw, ih = target.size

        scale = min(cw / iw, ch / ih, 1.0)
        new_w = max(1, int(iw * scale))
        new_h = max(1, int(ih * scale))

        if scale < 1.0:
            resized = target.resize((new_w, new_h), Image.Resampling.LANCZOS)
        else:
            resized = target

        self.display_image = ImageTk.PhotoImage(resized)
        self.img_x = (cw - new_w) // 2
        self.img_y = (ch - new_h) // 2
        self.scale = scale

        self.canvas.create_rectangle(
            self.img_x - 1, self.img_y - 1, self.img_x + new_w + 1, self.img_y + new_h + 1,
            outline="#333333", width=1
        )
        self.canvas.create_image(self.img_x, self.img_y, image=self.display_image, anchor="nw")

    def _on_canvas_press(self, event):
        if self.draw_image is None or self.active_tool == "none":
            return
        self.last_x = (event.x - self.img_x) / self.scale
        self.last_y = (event.y - self.img_y) / self.scale
        if self.active_tool == "highlighter":
            self.highlighter_pts = [(self.last_x, self.last_y)]

    def _on_canvas_drag(self, event):
        if self.draw_image is None or self.active_tool == "none" or self.last_x is None:
            return

        cur_x = (event.x - self.img_x) / self.scale
        cur_y = (event.y - self.img_y) / self.scale

        if self.active_tool == "pen":
            draw = ImageDraw.Draw(self.draw_image, "RGB")
            draw.line([(self.last_x, self.last_y), (cur_x, cur_y)], fill=self.pen_color, width=self.pen_size)
            self.last_x = cur_x
            self.last_y = cur_y
            self._render_current_image()
        elif self.active_tool == "highlighter":
            self.highlighter_pts.append((cur_x, cur_y))
            if len(self.highlighter_pts) > 1:
                hl_layer = Image.new("RGBA", self.draw_image.size, (0, 0, 0, 0))
                ImageDraw.Draw(hl_layer).line(self.highlighter_pts, fill=(255, 235, 59, 110), width=22, joint="curve")
                preview = Image.alpha_composite(self.draw_image.convert("RGBA"), hl_layer)
                self._render_current_image(image_to_render=preview)
        elif self.active_tool == "eraser":
            ix, iy = int(cur_x), int(cur_y)
            orig_crop = self.current_image.crop((ix-12, iy-12, ix+12, iy+12))
            self.draw_image.paste(orig_crop, (ix-12, iy-12))
            self.last_x = cur_x
            self.last_y = cur_y
            self._render_current_image()

    def _on_canvas_release(self, event):
        if self.draw_image is not None and self.active_tool != "none":
            if self.active_tool == "highlighter" and len(self.highlighter_pts) > 1:
                hl_layer = Image.new("RGBA", self.draw_image.size, (0, 0, 0, 0))
                ImageDraw.Draw(hl_layer).line(self.highlighter_pts, fill=(255, 235, 59, 110), width=22, joint="curve")
                self.draw_image = Image.alpha_composite(self.draw_image.convert("RGBA"), hl_layer).convert("RGB")
                self.highlighter_pts = []
                self._render_current_image()

            self.history.append(self.draw_image.copy())
            if len(self.history) > 15:
                self.history.pop(0)

            self._has_saved = False

            # "Beni otomatik olarak kopyala" ayarı açıksa her çizimde panoyu güncelle
            if config.get("auto_copy_snip", True):
                copy_image_to_clipboard(self.draw_image)
                self.lbl_status.configure(text=f"✓  {t('status_edit_copied')}", text_color="#0F9D58")

        self.last_x = None
        self.last_y = None
        self.highlighter_pts = []

    def on_undo(self):
        if len(self.history) > 1:
            self.history.pop()
            self.draw_image = self.history[-1].copy()
            self._render_current_image()
            self._has_saved = False
            if config.get("auto_copy_snip", True):
                copy_image_to_clipboard(self.draw_image)
                self.lbl_status.configure(text=f"↩️  {t('status_undo_copied')}", text_color="#0F9D58")
            else:
                self.lbl_status.configure(text=f"↩️  {t('status_undo')}", text_color="#FFFFFF")

    def on_save_file(self):
        if self.draw_image is None:
            return False

        now = datetime.datetime.now()
        prefix = config.get("snip_filename_prefix", "Ekran_Goruntusu")
        suggested_name = f"{prefix}_{now.strftime('%Y-%m-%d_%H%M%S')}.png"

        file_path = filedialog.asksaveasfilename(
            initialfile=suggested_name,
            defaultextension=".png",
            filetypes=[
                (f"{t('filetype_png')} (*.png)", "*.png"),
                (f"{t('filetype_jpg')} (*.jpg)", "*.jpg"),
                (f"{t('filetype_all')} (*.*)", "*.*")
            ]
        )
        if file_path:
            self.draw_image.save(file_path)
            self._has_saved = True
            self.saved_filepath = file_path
            self.lbl_status.configure(text=f"✓  {t('status_saved')}: {os.path.basename(file_path)}", text_color="#0F9D58")
            return True
        return False

    def on_copy_clipboard(self):
        if self.draw_image:
            has_unsaved = (len(self.history) > 1 and not self._has_saved)
            fp = self.saved_filepath if not has_unsaved else None
            copy_image_to_clipboard(self.draw_image, filepath=fp)
            self.lbl_status.configure(text=f"✓  {t('copied_toast')}!", text_color="#0F9D58")

    def on_google_lens_search(self):
        if self.draw_image is None:
            return
        if hasattr(self, "btn_lens"):
            self.btn_lens.configure(state="disabled", text=f"⏳ {t('status_searching')}...")
        self.lbl_status.configure(text=f"🔍 {t('status_uploading_lens')}", text_color="#FFB900")

        def _search():
            url = search_image_in_google_lens(self.draw_image, open_browser=True)
            def _done():
                if hasattr(self, "btn_lens"):
                    self.btn_lens.configure(state="normal", text=t("btn_lens"))
                if url:
                    self.lbl_status.configure(text=f"✓  {t('status_lens_opened')}", text_color="#0F9D58")
                else:
                    self.lbl_status.configure(text=f"✕  {t('status_upload_failed')}", text_color="#E81123")
            self.after(0, _done)

        threading.Thread(target=_search, daemon=True).start()

    def on_extract_text_ocr(self):
        if self.draw_image is None:
            return
        self.btn_ocr.configure(state="disabled", text=f"⏳ {t('status_scanning')}...")
        self.lbl_status.configure(text=f"🔤 {t('status_scanning_text')}", text_color="#FFB900")

        def _ocr_thread():
            text = extract_text_from_image(self.draw_image)
            def _done():
                self.btn_ocr.configure(state="normal", text=t("btn_ocr"))
                if text:
                    self.lbl_status.configure(text=f"✓  {t('status_text_copied')}", text_color="#0F9D58")
                    self._show_ocr_dialog(text)
                else:
                    self.lbl_status.configure(text=t("status_no_text"), text_color="#888888")
                    messagebox.showinfo(t("ocr_dialog_title"), t("ocr_no_text"))
            self.after(0, _done)

        threading.Thread(target=_ocr_thread, daemon=True).start()

    def _show_ocr_dialog(self, extracted_text: str):
        dlg = ctk.CTkToplevel(self)
        dlg.title(t("ocr_dialog_title"))
        dlg.geometry("540x420")
        dlg.minsize(440, 320)
        dlg.configure(fg_color="#202020")
        dlg.attributes("-topmost", True)

        header = ctk.CTkFrame(dlg, fg_color="transparent")
        header.pack(fill=tk.X, padx=16, pady=(16, 8))

        lbl_h = ctk.CTkLabel(
            header, image=icon_assets.get_icon_ctk("ocr", (20, 20)),
            text=f"  {t('ocr_extracted_text')}", compound="left",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"), text_color="#FFFFFF"
        )
        lbl_h.pack(side=tk.LEFT)

        lbl_sub = ctk.CTkLabel(
            dlg, text=t("ocr_auto_copied_hint"),
            font=ctk.CTkFont(family="Segoe UI", size=11), text_color="#AAAAAA"
        )
        lbl_sub.pack(anchor="w", padx=16, pady=(0, 8))

        txt_box = ctk.CTkTextbox(
            dlg, fg_color="#181818", border_width=1, border_color="#333333",
            corner_radius=8, font=ctk.CTkFont(family="Segoe UI", size=13), text_color="#FFFFFF"
        )
        txt_box.pack(fill=tk.BOTH, expand=True, padx=16, pady=4)
        txt_box.insert("1.0", extracted_text)

        bottom_bar = ctk.CTkFrame(dlg, fg_color="transparent")
        bottom_bar.pack(fill=tk.X, padx=16, pady=14)

        def _copy_again():
            content = txt_box.get("1.0", "end-1c")
            self.clipboard_clear()
            self.clipboard_append(content)
            btn_copy_all.configure(text=f"✓  {t('copied_toast')}!")
            dlg.after(1500, lambda: btn_copy_all.configure(text=f"  {t('ocr_copy_all')}"))

        btn_copy_all = ctk.CTkButton(
            bottom_bar, image=icon_assets.get_icon_ctk("copy", (16, 16)),
            text=f"  {t('ocr_copy_all')}", compound="left",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#0078D4", hover_color="#0063B1", corner_radius=6, height=34,
            command=_copy_again
        )
        btn_copy_all.pack(side=tk.LEFT)

        btn_close_dlg = ctk.CTkButton(
            bottom_bar, text=t("btn_close"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="#2B2B2B", hover_color="#383838", corner_radius=6, height=34, width=80,
            command=dlg.destroy
        )
        btn_close_dlg.pack(side=tk.RIGHT)

    def _on_new_click(self):
        if config.get("ask_save_edited_snip", False) and len(self.history) > 1 and not self._has_saved:
            res = messagebox.askyesnocancel(
                t("app_title"),
                t("prompt_save_changes")
            )
            if res is True:
                if self.on_save_file() and self.on_new_snip_callback:
                    self.on_new_snip_callback()
            elif res is False and self.on_new_snip_callback:
                self.on_new_snip_callback()
        elif self.on_new_snip_callback:
            self.on_new_snip_callback()

    def _on_close(self):
        if config.get("ask_save_edited_snip", False) and len(self.history) > 1 and not self._has_saved:
            res = messagebox.askyesnocancel(
                t("app_title"),
                t("prompt_save_changes")
            )
            if res is True:
                if self.on_save_file():
                    self.destroy()
            elif res is False:
                self.destroy()
        else:
            self.destroy()

    def on_open_combiner(self):
        """Birleştirme / Kolaj penceresini mevcut görseli içerecek şekilde açar."""
        from image_combiner import ImageCombinerWindow
        ImageCombinerWindow(
            parent=self,
            initial_images=[self.draw_image.copy()],
            on_open_in_editor=self._load_from_combiner
        )

    def _load_from_combiner(self, img: Image.Image):
        """Kolajdan gelen birleştirilmiş görseli düzenleyiciye yükler."""
        self.current_image = img.copy()
        self.draw_image = img.copy()
        self.history = [self.draw_image.copy()]
        self._has_saved = False
        self._render_current_image()
        w, h = self.current_image.size
        self.lbl_dim.configure(text=f"{w} × {h} px")
        self.lbl_status.configure(text=f"✓ {t('combiner_title_suffix')}")



# =============================================================================
# ANA UYGULAMA SINIFI
# =============================================================================
class EkranAlintisiAraci:
    def __init__(self):
        icon_assets.setup_windows_app_id()

        self.root = ctk.CTk()
        self.root.title(t("app_title"))
        self.root.geometry("560x240")
        self.root.minsize(500, 210)
        self.root.configure(fg_color="#202020")

        icon_assets.apply_window_icon(self.root)

        self.capture_type = "camera"  # 'camera' veya 'video'
        self.snip_mode = "rect"       # 'rect', 'window', 'fullscreen', 'freeform'
        self.delay_sec = 0            # 0, 3, 5, 10

        self.active_popup = None
        self.is_editor_mode = False
        self.is_settings_mode = False
        self.current_image = None
        self.draw_image = None
        self.display_image = None
        self.history = []
        self.active_tool = "none"
        self.pen_color = "#E81123"
        self.pen_size = 4
        self.last_x = None
        self.last_y = None
        self.scale = 1.0
        self.img_x = 0
        self.img_y = 0
        self.highlighter_pts = []
        self._has_saved = False
        self.extra_windows = []

        self._build_compact_ui()
        self._bind_shortcuts()

        self.root.bind("<Button-1>", self._on_root_click, add="+")
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _bind_shortcuts(self):
        self.root.bind("<Control-c>", lambda e: self.on_copy_clipboard())
        self.root.bind("<Control-s>", lambda e: self.on_save_file())
        self.root.bind("<Control-g>", lambda e: self.on_google_lens_search())
        self.root.bind("<Control-n>", lambda e: self.on_new_snip())
        self.root.bind("<Control-z>", lambda e: self.on_undo())
        self.root.bind("<Control-comma>", lambda e: self._build_settings_ui())
        # '+' veya Numpad '+' tuşuna basıldığında yeni alıntı/kayıt başlat
        self.root.bind("+", lambda e: self.on_new_snip())
        self.root.bind("<KP_Add>", lambda e: self.on_new_snip())
        self.root.bind("<Control-Shift-S>", lambda e: self._on_shortcut_photo())
        self.root.bind("<Control-Shift-s>", lambda e: self._on_shortcut_photo())
        self.root.bind("<Control-Shift-R>", lambda e: self._on_shortcut_video())
        self.root.bind("<Control-Shift-r>", lambda e: self._on_shortcut_video())

    def _on_shortcut_photo(self):
        self.capture_type = "camera"
        self._build_compact_ui()
        self.on_new_snip()

    def _on_shortcut_video(self):
        self.capture_type = "video"
        self._build_compact_ui()
        self.on_new_snip()

    def _close_popup(self):
        if self.active_popup:
            try:
                self.active_popup.destroy()
            except Exception:
                pass
            self.active_popup = None

    def _on_root_click(self, event):
        if self.active_popup:
            widget = event.widget
            while widget:
                if widget == self.active_popup:
                    return
                widget = getattr(widget, "master", None)
            self._close_popup()

    def _center_on_primary_monitor(self, width, height):
        from snipping_overlay import get_primary_monitor
        mon = get_primary_monitor()
        x = mon["left"] + (mon["width"] - width) // 2
        y = mon["top"] + (mon["height"] - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    # =========================================================================
    # 1. WINDOWS 11 BOŞTA DURUMU (COMPACT IDLE VIEW)
    # =========================================================================
    def _build_compact_ui(self):
        self._close_popup()
        self.is_editor_mode = False
        self.is_settings_mode = False
        self._center_on_primary_monitor(600, 240)
        self.root.title(t("app_title"))
        self.root.minsize(540, 210)

        for widget in self.root.winfo_children():
            widget.destroy()

        self.top_bar = ctk.CTkFrame(self.root, fg_color="#202020", height=48, corner_radius=0)
        self.top_bar.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(10, 4))

        # Mod Butonları
        cam_active = (self.capture_type == "camera")
        self.btn_camera = ctk.CTkButton(
            self.top_bar, image=icon_assets.get_seg_icon("camera", cam_active),
            text="", fg_color="transparent", hover_color="#333333", corner_radius=6,
            width=42, height=36, command=self._switch_to_camera
        )
        self.btn_camera.pack(side=tk.LEFT, padx=(0, 2))

        vid_active = (self.capture_type == "video")
        self.btn_video = ctk.CTkButton(
            self.top_bar, image=icon_assets.get_seg_icon("video", vid_active),
            text="", fg_color="transparent", hover_color="#333333", corner_radius=6,
            width=42, height=36, command=self._switch_to_video
        )
        self.btn_video.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_new = ctk.CTkButton(
            self.top_bar, text=t("btn_new"),
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#FFFFFF", fg_color="#0078D4", hover_color="#0063B1",
            corner_radius=6, width=88, height=34, command=self.on_new_snip
        )
        self.btn_new.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_mode_dropdown = ctk.CTkButton(
            self.top_bar, image=icon_assets.get_combo_icon(self.snip_mode),
            text="", fg_color="transparent", hover_color="#333333", corner_radius=6,
            width=46, height=34, command=self._toggle_mode_menu
        )
        self.btn_mode_dropdown.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_delay_dropdown = ctk.CTkButton(
            self.top_bar, image=icon_assets.get_delay_combo_icon(self.delay_sec),
            text="", fg_color="transparent", hover_color="#333333", corner_radius=6,
            width=46, height=34, command=self._toggle_delay_menu
        )
        self.btn_delay_dropdown.pack(side=tk.LEFT, padx=(0, 8))

        sep_v = ctk.CTkFrame(self.top_bar, width=1, height=20, fg_color="#383838")
        sep_v.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_quick_ocr = ctk.CTkButton(
            self.top_bar, image=icon_assets.get_icon_ctk("ocr", (20, 20)),
            text="", fg_color="transparent", hover_color="#333333", corner_radius=6,
            width=34, height=34, command=self._launch_ocr_snip
        )
        self.btn_quick_ocr.pack(side=tk.LEFT, padx=(0, 4))

        self.btn_quick_combine = ctk.CTkButton(
            self.top_bar, image=icon_assets.get_icon_ctk("combine", (20, 20)),
            text="", fg_color="transparent", hover_color="#333333", corner_radius=6,
            width=34, height=34, command=self.open_image_combiner
        )
        self.btn_quick_combine.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_dots = ctk.CTkButton(
            self.top_bar, image=icon_assets.get_icon_ctk("dots", (18, 18)),
            text="", fg_color="transparent", hover_color="#333333", corner_radius=6,
            width=34, height=34, command=self._open_more_menu
        )
        self.btn_dots.pack(side=tk.RIGHT)

        self.divider = ctk.CTkFrame(self.root, fg_color="#2D2D2D", height=1)
        self.divider.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(2, 0))

        self.content_frame = ctk.CTkFrame(self.root, fg_color="#1E1E1E", corner_radius=0)
        self.content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Orta Bilgi ve Kısayol Alanı
        center_box = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        center_box.place(relx=0.5, rely=0.48, anchor="center")

        is_video = (self.capture_type == "video")
        title_text = t("hint_video_lead") if is_video else t("hint_snip_lead")
        key_char = "R" if is_video else "S"

        row_keys = ctk.CTkFrame(center_box, fg_color="transparent", cursor="hand2")
        row_keys.pack()
        row_keys.bind("<Button-1>", lambda e: self.on_new_snip())

        lbl_lead = ctk.CTkLabel(
            row_keys, text=f"{title_text}  ",
            font=ctk.CTkFont(family="Segoe UI", size=13), text_color="#CCCCCC"
        )
        lbl_lead.pack(side=tk.LEFT)
        lbl_lead.bind("<Button-1>", lambda e: self.on_new_snip())

        # 1. Tuş: Windows Logo Tuşu
        key_win = ctk.CTkFrame(row_keys, fg_color="#2B2B2B", border_width=1, border_color="#444444", corner_radius=5)
        key_win.pack(side=tk.LEFT, padx=3, pady=2)
        key_win.bind("<Button-1>", lambda e: self.on_new_snip())
        lbl_win = ctk.CTkLabel(
            key_win, image=icon_assets.get_icon_ctk("windows", (14, 14)), text="", width=28, height=24
        )
        lbl_win.pack(padx=4, pady=1)
        lbl_win.bind("<Button-1>", lambda e: self.on_new_snip())

        plus1 = ctk.CTkLabel(row_keys, text="+", font=ctk.CTkFont(family="Segoe UI", size=12), text_color="#888888")
        plus1.pack(side=tk.LEFT, padx=2)
        plus1.bind("<Button-1>", lambda e: self.on_new_snip())

        # 2. Tuş: Shift
        key_shift = ctk.CTkFrame(row_keys, fg_color="#2B2B2B", border_width=1, border_color="#444444", corner_radius=5)
        key_shift.pack(side=tk.LEFT, padx=3, pady=2)
        key_shift.bind("<Button-1>", lambda e: self.on_new_snip())
        lbl_shift = ctk.CTkLabel(
            key_shift, text="Shift", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#FFFFFF", height=24
        )
        lbl_shift.pack(padx=8, pady=1)
        lbl_shift.bind("<Button-1>", lambda e: self.on_new_snip())

        plus2 = ctk.CTkLabel(row_keys, text="+", font=ctk.CTkFont(family="Segoe UI", size=12), text_color="#888888")
        plus2.pack(side=tk.LEFT, padx=2)
        plus2.bind("<Button-1>", lambda e: self.on_new_snip())

        # 3. Tuş: S veya R
        key_action = ctk.CTkFrame(row_keys, fg_color="#2B2B2B", border_width=1, border_color="#444444", corner_radius=5)
        key_action.pack(side=tk.LEFT, padx=3, pady=2)
        key_action.bind("<Button-1>", lambda e: self.on_new_snip())
        lbl_action = ctk.CTkLabel(
            key_action, text=key_char, font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#FFFFFF", width=22, height=24
        )
        lbl_action.pack(padx=6, pady=1)
        lbl_action.bind("<Button-1>", lambda e: self.on_new_snip())

        lbl_trail = ctk.CTkLabel(
            row_keys, text=f"  {t('hint_trail')}",
            font=ctk.CTkFont(family="Segoe UI", size=13), text_color="#CCCCCC"
        )
        lbl_trail.pack(side=tk.LEFT)
        lbl_trail.bind("<Button-1>", lambda e: self.on_new_snip())

        # Alt açıklama (veya + Yeni butonunu seçin)
        sub_text = ctk.CTkLabel(
            center_box,
            text=t("hint_sub"),
            font=ctk.CTkFont(family="Segoe UI", size=11), text_color="#777777"
        )
        sub_text.pack(pady=(6, 0))

    def _switch_to_camera(self):
        self.capture_type = "camera"
        self._build_compact_ui()

    def _switch_to_video(self):
        self.capture_type = "video"
        self._build_compact_ui()

    def _open_more_menu(self):
        if self.active_popup:
            self._close_popup()
            return

        x = self.btn_dots.winfo_rootx() - 110
        y = self.btn_dots.winfo_rooty() + self.btn_dots.winfo_height() + 4

        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.geometry(f"250x92+{x-80}+{y}")
        popup.configure(bg="#202020")
        self.active_popup = popup

        card = ctk.CTkFrame(popup, fg_color="#202020", border_width=1, border_color="#383838", corner_radius=8)
        card.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        def _go_settings():
            self._close_popup()
            self._build_settings_ui()

        btn_settings = ctk.CTkButton(
            card, text=f"⚙  {t('btn_settings')}", anchor="w",
            font=ctk.CTkFont(family="Segoe UI", size=13), text_color="#FFFFFF",
            fg_color="transparent", hover_color="#383838", height=38, corner_radius=4,
            command=_go_settings
        )
        btn_settings.pack(fill=tk.X, padx=4, pady=(2, 1))

        def _toggle_default_action():
            self._close_popup()
            curr = default_app_manager.is_default_snipping_tool()
            ok, msg = default_app_manager.set_as_default_snipping_tool(not curr)
            if not curr:
                toast.show(t("app_title"), t("set_default_app_success"))
            else:
                toast.show(t("app_title"), t("set_default_app_removed"))

        is_def = default_app_manager.is_default_snipping_tool()
        def_icon = "✓ " if is_def else "★ "
        btn_def = ctk.CTkButton(
            card, text=f"{def_icon}{t('set_default_app_title')}", anchor="w",
            font=ctk.CTkFont(family="Segoe UI", size=12), text_color="#60CDFF" if is_def else "#E0E0E0",
            fg_color="transparent", hover_color="#383838", height=36, corner_radius=4,
            command=_toggle_default_action
        )
        btn_def.pack(fill=tk.X, padx=4, pady=(1, 2))

    def _toggle_mode_menu(self):
        if self.active_popup:
            self._close_popup()
            return

        x = self.btn_mode_dropdown.winfo_rootx()
        y = self.btn_mode_dropdown.winfo_rooty() + self.btn_mode_dropdown.winfo_height() + 4

        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.geometry(f"160x180+{x}+{y}")
        popup.configure(bg="#202020")
        self.active_popup = popup

        card = ctk.CTkFrame(popup, fg_color="#202020", border_width=1, border_color="#383838", corner_radius=8)
        card.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        items = [
            (t("shape_rect"), "rect"),
            (t("shape_window"), "window"),
            (t("shape_fullscreen"), "fullscreen"),
            (t("shape_freeform"), "freeform")
        ]

        for label_text, mode_key in items:
            is_active = (self.snip_mode == mode_key)
            btn = ctk.CTkButton(
                card, image=icon_assets.get_menu_icon(mode_key, is_active),
                text=f"  {label_text}", compound="left", anchor="w",
                font=ctk.CTkFont(family="Segoe UI", size=13), text_color="#FFFFFF",
                fg_color="#303030" if is_active else "transparent", hover_color="#383838",
                height=40, corner_radius=4,
                command=lambda m=mode_key: self._select_mode(m)
            )
            btn.pack(fill=tk.X, padx=4, pady=2)

    def _select_mode(self, mode_key):
        self.snip_mode = mode_key
        self._close_popup()
        self._build_compact_ui()

    def _toggle_delay_menu(self):
        if self.active_popup:
            self._close_popup()
            return

        x = self.btn_delay_dropdown.winfo_rootx()
        y = self.btn_delay_dropdown.winfo_rooty() + self.btn_delay_dropdown.winfo_height() + 4

        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.geometry(f"180x180+{x}+{y}")
        popup.configure(bg="#202020")
        self.active_popup = popup

        card = ctk.CTkFrame(popup, fg_color="#202020", border_width=1, border_color="#383838", corner_radius=8)
        card.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        delays = [
            (t("delay_none"), 0),
            (t("delay_3s"), 3),
            (t("delay_5s"), 5),
            (t("delay_10s"), 10),
        ]

        for label_text, sec in delays:
            is_active = (self.delay_sec == sec)
            btn = ctk.CTkButton(
                card, image=icon_assets.get_delay_menu_icon(sec, is_active),
                text=f"  {label_text}", compound="left", anchor="w",
                font=ctk.CTkFont(family="Segoe UI", size=13), text_color="#FFFFFF",
                fg_color="#303030" if is_active else "transparent", hover_color="#383838",
                height=40, corner_radius=4,
                command=lambda s=sec: self._select_delay(s)
            )
            btn.pack(fill=tk.X, padx=4, pady=2)

    def _select_delay(self, sec):
        self.delay_sec = sec
        self._close_popup()
        self._build_compact_ui()

    # =========================================================================
    # 2. WINDOWS 11 BİREBİR AYARLAR ARAYÜZÜ (SETTINGS PAGE)
    # =========================================================================
    def _build_settings_ui(self):
        """Windows 11 Snipping Tool ayarlar penceresinin çalışan birebir klonunu oluşturur."""
        self._close_popup()
        self.is_editor_mode = False
        self.is_settings_mode = True
        self._center_on_primary_monitor(600, 720)
        self.root.title(f"{t('app_title')} - {t('settings_title')}")
        self.root.minsize(540, 520)

        for widget in self.root.winfo_children():
            widget.destroy()

        # Üst Başlık Çubuğu: [←] Ayarlar
        header = ctk.CTkFrame(self.root, fg_color="#202020", height=48, corner_radius=0)
        header.pack(side=tk.TOP, fill=tk.X, padx=16, pady=(12, 6))

        btn_back = ctk.CTkButton(
            header, image=icon_assets.get_icon_ctk("arrow_left", (20, 20)),
            text="", width=36, height=36, fg_color="transparent", hover_color="#333333",
            corner_radius=6, command=self._build_compact_ui
        )
        btn_back.pack(side=tk.LEFT, padx=(0, 12))

        lbl_title = ctk.CTkLabel(
            header, text=t("settings_title"),
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"), text_color="#FFFFFF"
        )
        lbl_title.pack(side=tk.LEFT)

        # Kaydırılabilir Ayarlar Paneli
        scroll = ctk.CTkScrollableFrame(self.root, fg_color="#202020")
        scroll.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=16, pady=(0, 10))

        def _add_section_header(title):
            lbl = ctk.CTkLabel(
                scroll, text=title, font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                text_color="#E0E0E0", anchor="w"
            )
            lbl.pack(fill=tk.X, padx=4, pady=(14, 6))

        def _add_switch_card(title, desc=None, config_key=None, icon_name=None, on_change=None):
            card = ctk.CTkFrame(scroll, fg_color="#282828", border_width=1, border_color="#363636", corner_radius=6)
            card.pack(fill=tk.X, pady=3)

            if icon_name:
                ico_lbl = ctk.CTkLabel(card, image=icon_assets.get_icon_ctk(icon_name, (18, 18)), text="", width=24)
                ico_lbl.pack(side=tk.LEFT, padx=(12, 0), pady=10)

            initial_val = config.get(config_key, False) if config_key else False

            def _on_toggle():
                is_on = sw.get() == 1
                sw.configure(text=t("switch_on") if is_on else t("switch_off"))
                if config_key:
                    config.set(config_key, is_on)
                if on_change:
                    on_change(is_on)

            sw = ctk.CTkSwitch(
                card, text=t("switch_on") if initial_val else t("switch_off"),
                progress_color="#60CDFF", button_color="#FFFFFF", button_hover_color="#E0E0E0",
                fg_color="#383838", switch_width=44, switch_height=22,
                font=ctk.CTkFont(family="Segoe UI", size=12), text_color="#FFFFFF",
                command=_on_toggle
            )
            if initial_val:
                sw.select()
            else:
                sw.deselect()
            sw.pack(side=tk.RIGHT, padx=14, pady=10)

            txt_frame = ctk.CTkFrame(card, fg_color="transparent")
            txt_frame.pack(side=tk.LEFT, padx=12, pady=10, fill=tk.BOTH, expand=True)

            t_lbl = ctk.CTkLabel(txt_frame, text=title, font=ctk.CTkFont(family="Segoe UI", size=13), text_color="#FFFFFF", anchor="w", wraplength=330, justify="left")
            t_lbl.pack(fill=tk.X)

            if desc:
                d_lbl = ctk.CTkLabel(txt_frame, text=desc, font=ctk.CTkFont(family="Segoe UI", size=11), text_color="#9E9E9E", anchor="w", wraplength=330, justify="left")
                d_lbl.pack(fill=tk.X, pady=(2, 0))

            return card, sw

        # Açılır Klasör Kartı (Screenshot 1 & 2 Accordion)
        def _add_folder_card(title, config_key, dir_config_key, label_sub):
            card = ctk.CTkFrame(scroll, fg_color="#282828", border_width=1, border_color="#363636", corner_radius=6)
            card.pack(fill=tk.X, pady=3)

            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill=tk.X, padx=12, pady=(10, 4))

            sub_frame = ctk.CTkFrame(card, fg_color="#222222", corner_radius=4)

            def _toggle_sub():
                is_on = sw.get() == 1
                sw.configure(text=t("switch_on") if is_on else t("switch_off"))
                config.set(config_key, is_on)
                lbl_chevron.configure(text="˄" if is_on else "˅")
                if is_on:
                    sub_frame.pack(fill=tk.X, padx=12, pady=(0, 10))
                else:
                    sub_frame.pack_forget()

            initial_val = config.get(config_key, True)
            sw = ctk.CTkSwitch(
                top_row, text=t("switch_on") if initial_val else t("switch_off"),
                progress_color="#60CDFF", button_color="#FFFFFF", button_hover_color="#E0E0E0",
                fg_color="#383838", switch_width=44, switch_height=22,
                font=ctk.CTkFont(family="Segoe UI", size=12), text_color="#FFFFFF",
                command=_toggle_sub
            )
            if initial_val:
                sw.select()
            else:
                sw.deselect()
            sw.pack(side=tk.RIGHT, padx=(6, 0))

            lbl_chevron = ctk.CTkLabel(top_row, text="˄" if initial_val else "˅", font=ctk.CTkFont(size=12), text_color="#888888")
            lbl_chevron.pack(side=tk.RIGHT, padx=(4, 8))

            t_lbl = ctk.CTkLabel(top_row, text=title, font=ctk.CTkFont(family="Segoe UI", size=13), text_color="#FFFFFF", anchor="w", wraplength=330, justify="left")
            t_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

            sub_left = ctk.CTkFrame(sub_frame, fg_color="transparent")
            sub_left.pack(side=tk.LEFT, padx=12, pady=10, fill=tk.X, expand=True)

            lbl_sub_t = ctk.CTkLabel(sub_left, text=label_sub, font=ctk.CTkFont(family="Segoe UI", size=12), text_color="#CCCCCC", anchor="w")
            lbl_sub_t.pack(fill=tk.X)

            path_row = ctk.CTkFrame(sub_left, fg_color="transparent")
            path_row.pack(fill=tk.X, pady=(2, 0))

            cur_path = config.get(dir_config_key, "")
            lbl_path = ctk.CTkLabel(path_row, text=cur_path, font=ctk.CTkFont(family="Segoe UI", size=11), text_color="#9E9E9E", anchor="w")
            lbl_path.pack(side=tk.LEFT)

            def _change_dir():
                new_d = filedialog.askdirectory(initialdir=config.get(dir_config_key))
                if new_d:
                    config.set(dir_config_key, new_d)
                    lbl_path.configure(text=new_d)

            btn_change = ctk.CTkButton(
                path_row, text=t("btn_change"), font=ctk.CTkFont(family="Segoe UI", size=11, underline=True),
                text_color="#60CDFF", fg_color="transparent", hover=False, width=50, height=20,
                command=_change_dir
            )
            btn_change.pack(side=tk.LEFT, padx=(8, 0))

            def _open_folder():
                p = config.get(dir_config_key)
                if p:
                    os.makedirs(p, exist_ok=True)
                    try:
                        os.startfile(p)
                    except Exception as e:
                        print(f"Klasör açma hatası: {e}")

            btn_open_f = ctk.CTkButton(
                sub_frame, text=t("btn_open_folder"), font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color="#FFFFFF", fg_color="#333333", hover_color="#3E3E3E", corner_radius=4,
                width=90, height=32, command=_open_folder
            )
            btn_open_f.pack(side=tk.RIGHT, padx=12, pady=10)

            if initial_val:
                sub_frame.pack(fill=tk.X, padx=12, pady=(0, 10))

        # Kenarlık Ayarları Kartı (Accordion Renk ve Kalınlık)
        def _add_border_card():
            card = ctk.CTkFrame(scroll, fg_color="#282828", border_width=1, border_color="#363636", corner_radius=6)
            card.pack(fill=tk.X, pady=3)

            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill=tk.X, padx=12, pady=(10, 4))

            sub_frame = ctk.CTkFrame(card, fg_color="#222222", corner_radius=4)

            def _toggle_border():
                is_on = sw.get() == 1
                sw.configure(text=t("switch_on") if is_on else t("switch_off"))
                config.set("add_border", is_on)
                lbl_chevron.configure(text="˄" if is_on else "˅")
                if is_on:
                    sub_frame.pack(fill=tk.X, padx=12, pady=(0, 10))
                else:
                    sub_frame.pack_forget()

            initial_val = config.get("add_border", False)
            sw = ctk.CTkSwitch(
                top_row, text=t("switch_on") if initial_val else t("switch_off"),
                progress_color="#60CDFF", button_color="#FFFFFF", button_hover_color="#E0E0E0",
                fg_color="#383838", switch_width=44, switch_height=22,
                font=ctk.CTkFont(family="Segoe UI", size=12), text_color="#FFFFFF",
                command=_toggle_border
            )
            if initial_val:
                sw.select()
            else:
                sw.deselect()
            sw.pack(side=tk.RIGHT, padx=(6, 0))

            lbl_chevron = ctk.CTkLabel(top_row, text="˄" if initial_val else "˅", font=ctk.CTkFont(size=12), text_color="#888888")
            lbl_chevron.pack(side=tk.RIGHT, padx=(4, 8))

            t_lbl = ctk.CTkLabel(top_row, text=t("set_border"), font=ctk.CTkFont(family="Segoe UI", size=13), text_color="#FFFFFF", anchor="w", wraplength=330, justify="left")
            t_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # Renk ve Kalınlık Seçimi
            sub_inner = ctk.CTkFrame(sub_frame, fg_color="transparent")
            sub_inner.pack(fill=tk.X, padx=14, pady=10)

            # 1. Renk Seçimi
            lbl_col = ctk.CTkLabel(sub_inner, text=t("set_border_color"), font=ctk.CTkFont(family="Segoe UI", size=12), text_color="#CCCCCC", anchor="w")
            lbl_col.pack(fill=tk.X)

            colors_row = ctk.CTkFrame(sub_inner, fg_color="transparent")
            colors_row.pack(fill=tk.X, pady=(4, 10))

            cur_color = config.get("border_color", "#D13438")
            color_swatches = [
                ("#D13438", "Kırmızı"),
                ("#000000", "Siyah"),
                ("#808080", "Gri"),
                ("#FFFFFF", "Beyaz"),
                ("#0078D4", "Mavi"),
                ("#107C41", "Yeşil"),
                ("#FFB900", "Sarı"),
            ]

            swatch_btns = []

            def _set_color(c):
                config.set("border_color", c)
                for btn, hex_c in swatch_btns:
                    btn.configure(border_width=2 if hex_c == c else 0)

            for hex_code, name in color_swatches:
                b = ctk.CTkButton(
                    colors_row, text="", width=26, height=26, corner_radius=13,
                    fg_color=hex_code, hover_color=hex_code,
                    border_color="#FFFFFF" if hex_code != "#FFFFFF" else "#0078D4",
                    border_width=2 if hex_code == cur_color else 0,
                    command=lambda h=hex_code: _set_color(h)
                )
                b.pack(side=tk.LEFT, padx=3)
                swatch_btns.append((b, hex_code))

            def _custom_color():
                c = colorchooser.askcolor(initialcolor=config.get("border_color", "#D13438"))[1]
                if c:
                    _set_color(c)

            btn_custom = ctk.CTkButton(
                colors_row, text=t("set_custom_color"), width=60, height=26, corner_radius=6,
                fg_color="#333333", hover_color="#444444", font=ctk.CTkFont(family="Segoe UI", size=11),
                command=_custom_color
            )
            btn_custom.pack(side=tk.LEFT, padx=8)

            # 2. Kalınlık Seçimi
            lbl_thick = ctk.CTkLabel(sub_inner, text=t("set_border_width"), font=ctk.CTkFont(family="Segoe UI", size=12), text_color="#CCCCCC", anchor="w")
            lbl_thick.pack(fill=tk.X)

            thick_row = ctk.CTkFrame(sub_inner, fg_color="transparent")
            thick_row.pack(fill=tk.X, pady=(4, 0))

            cur_w = config.get("border_width", 3)
            thick_btns = []

            def _set_thick(w):
                config.set("border_width", w)
                for btn, val in thick_btns:
                    btn.configure(fg_color="#0078D4" if val == w else "#333333")

            for w_val in [1, 2, 3, 5, 8]:
                b = ctk.CTkButton(
                    thick_row, text=f"{w_val} px", width=52, height=26, corner_radius=6,
                    fg_color="#0078D4" if w_val == cur_w else "#333333", hover_color="#444444",
                    font=ctk.CTkFont(family="Segoe UI", size=11),
                    command=lambda w=w_val: _set_thick(w)
                )
                b.pack(side=tk.LEFT, padx=3)
                thick_btns.append((b, w_val))

            if initial_val:
                sub_frame.pack(fill=tk.X, padx=12, pady=(0, 10))

        # ---------------------------------------------------------------------
        # BÖLÜM 1: Ekran alıntısı alma
        # ---------------------------------------------------------------------
        _add_section_header(t("sec_snipping"))

        _add_switch_card(
            title=t("set_auto_copy_snip"),
            desc=t("set_auto_copy_snip_desc"),
            config_key="auto_copy_snip"
        )

        _add_folder_card(
            title=t("set_auto_save_snip"),
            config_key="auto_save_snip",
            dir_config_key="snip_save_dir",
            label_sub=t("set_save_path_sub")
        )

        # Dosya adı öneki ayarı kartı (AI ve pano çakışmalarını önleyen isimlendirme)
        def _add_naming_card():
            card = ctk.CTkFrame(scroll, fg_color="#282828", border_width=1, border_color="#363636", corner_radius=6)
            card.pack(fill=tk.X, pady=3)

            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill=tk.X, padx=12, pady=10)

            cur_lang = i18n.get_current_language()
            prefix_map = {
                "tr": ["Ekran_Goruntusu", "EkranAlintisi", "Alinti", "Gorsel", "Resim"],
                "en": ["Screenshot", "Snip", "Capture", "ScreenClip", "Image"],
                "de": ["Screenshot", "Bildschirmfoto", "Ausschnitt", "Aufnahme", "Bild"],
                "es": ["Captura", "Recorte", "CapturaPantalla", "Imagen"],
                "fr": ["Capture", "CaptureEcran", "Extrait", "Image"],
                "ru": ["Снимок_экрана", "Фрагмент", "Скриншот", "Изображение"],
            }
            all_known_defaults = {p for plist in prefix_map.values() for p in plist}
            lang_options = prefix_map.get(cur_lang, prefix_map["en"])
            cur_prefix = config.get("snip_filename_prefix", lang_options[0])

            # Dil değiştiğinde eski varsayılan önek otomatik olarak yeni dilin önekiyle güncellenir
            if cur_prefix in all_known_defaults and cur_prefix not in lang_options:
                cur_prefix = lang_options[0]
                config.set("snip_filename_prefix", cur_prefix)

            if cur_prefix not in lang_options:
                all_options = [cur_prefix] + [opt for opt in lang_options if opt != cur_prefix]
            else:
                all_options = lang_options

            # Önce sağdaki OptionMenu pack edilir ki buton boyutu korunup metin tarafından ezilmesin
            opt_menu = ctk.CTkOptionMenu(
                top_row,
                values=all_options,
                width=160,
                height=30,
                fg_color="#333333",
                button_color="#3A3A3A",
                button_hover_color="#444444",
                dropdown_fg_color="#2B2B2B",
                command=lambda val: config.set("snip_filename_prefix", val)
            )
            opt_menu.set(cur_prefix)
            opt_menu.pack(side=tk.RIGHT, padx=(10, 0))

            t_box = ctk.CTkFrame(top_row, fg_color="transparent")
            t_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            t_lbl = ctk.CTkLabel(
                t_box, text=t("set_naming_title"),
                font=ctk.CTkFont(family="Segoe UI", size=13), text_color="#FFFFFF",
                anchor="w", wraplength=310, justify="left"
            )
            t_lbl.pack(fill=tk.X)

            d_lbl = ctk.CTkLabel(
                t_box, text=t("set_naming_desc"),
                font=ctk.CTkFont(family="Segoe UI", size=11), text_color="#9E9E9E",
                anchor="w", wraplength=310, justify="left"
            )
            d_lbl.pack(fill=tk.X, pady=(2, 0))

        _add_naming_card()

        _add_switch_card(
            title=t("set_ask_save_snip"),
            config_key="ask_save_edited_snip"
        )

        _add_switch_card(
            title=t("set_multi_window"),
            desc=t("set_multi_window_desc"),
            config_key="multi_window"
        )

        _add_border_card()

        _add_switch_card(
            title=t("set_hdr_fix"),
            desc=t("set_hdr_fix_desc"),
            config_key="hdr_color_fix"
        )

        # ---------------------------------------------------------------------
        # BÖLÜM 2: Ekran kaydı
        # ---------------------------------------------------------------------
        _add_section_header(t("sec_recording"))

        _add_switch_card(
            title=t("set_auto_copy_video"),
            desc=t("set_auto_copy_video_desc"),
            config_key="auto_copy_video"
        )

        _add_folder_card(
            title=t("set_auto_save_video"),
            config_key="auto_save_video",
            dir_config_key="video_save_dir",
            label_sub=t("set_video_save_path_sub")
        )

        _add_switch_card(
            title=t("set_ask_save_video"),
            config_key="ask_save_edited_video"
        )

        _add_switch_card(
            title=t("set_record_mic"),
            icon_name="mic",
            config_key="record_mic_default"
        )

        _add_switch_card(
            title=t("set_record_sys_audio"),
            icon_name="speaker",
            config_key="record_system_audio_default"
        )

        # ---------------------------------------------------------------------
        # BÖLÜM 3: Kısayollar ve Varsayılan Ekran Alıntısı Aracı
        # ---------------------------------------------------------------------
        _add_section_header(t("sec_shortcuts"))

        def _add_default_app_card():
            card = ctk.CTkFrame(scroll, fg_color="#282828", border_width=1, border_color="#363636", corner_radius=6)
            card.pack(fill=tk.X, pady=3)

            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill=tk.X, padx=12, pady=10)

            is_def = default_app_manager.is_default_snipping_tool()

            def _toggle_default():
                is_on = sw.get() == 1
                ok, msg = default_app_manager.set_as_default_snipping_tool(is_on)
                sw.configure(text=t("switch_on") if is_on else t("switch_off"))
                if is_on:
                    lbl_status.configure(text=t("set_default_app_status_active"), text_color="#60CDFF")
                    toast.show(t("app_title"), t("set_default_app_success"))
                else:
                    lbl_status.configure(text=t("set_default_app_status_inactive"), text_color="#888888")
                    toast.show(t("app_title"), t("set_default_app_removed"))

            sw = ctk.CTkSwitch(
                top_row, text=t("switch_on") if is_def else t("switch_off"),
                progress_color="#60CDFF", button_color="#FFFFFF", button_hover_color="#E0E0E0",
                fg_color="#383838", switch_width=44, switch_height=22,
                font=ctk.CTkFont(family="Segoe UI", size=12), text_color="#FFFFFF",
                command=_toggle_default
            )
            if is_def:
                sw.select()
            else:
                sw.deselect()
            sw.pack(side=tk.RIGHT, padx=(6, 0))

            t_box = ctk.CTkFrame(top_row, fg_color="transparent")
            t_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            t_lbl = ctk.CTkLabel(
                t_box, text=t("set_default_app_title"),
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), text_color="#FFFFFF",
                anchor="w", wraplength=340, justify="left"
            )
            t_lbl.pack(fill=tk.X)

            d_lbl = ctk.CTkLabel(
                t_box, text=t("set_default_app_desc"),
                font=ctk.CTkFont(family="Segoe UI", size=11), text_color="#9E9E9E",
                anchor="w", wraplength=340, justify="left"
            )
            d_lbl.pack(fill=tk.X, pady=(2, 4))

            lbl_status = ctk.CTkLabel(
                t_box,
                text=t("set_default_app_status_active") if is_def else t("set_default_app_status_inactive"),
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color="#60CDFF" if is_def else "#888888",
                anchor="w"
            )
            lbl_status.pack(fill=tk.X)

            # Alt Bağlantılar Çubuğu
            link_row = ctk.CTkFrame(card, fg_color="#222222", corner_radius=4)
            link_row.pack(fill=tk.X, padx=12, pady=(0, 10))

            btn_link_default_apps = ctk.CTkButton(
                link_row, text=t("link_windows_default_apps"),
                font=ctk.CTkFont(family="Segoe UI", size=11, underline=True),
                text_color="#60CDFF", fg_color="transparent", hover=False, height=26, anchor="w",
                command=default_app_manager.open_windows_default_apps_settings
            )
            btn_link_default_apps.pack(side=tk.LEFT, padx=8, pady=4)

        _add_default_app_card()

        sc_card = ctk.CTkFrame(scroll, fg_color="#282828", border_width=1, border_color="#363636", corner_radius=6)
        sc_card.pack(fill=tk.X, pady=3)

        sc_link = ctk.CTkButton(
            sc_card, text=t("set_shortcut_link"),
            font=ctk.CTkFont(family="Segoe UI", size=12, underline=True),
            text_color="#60CDFF", fg_color="transparent", hover=False,
            command=lambda: os.system("start ms-settings:easeofaccess-keyboard")
        )
        sc_link.pack(side=tk.RIGHT, padx=12, pady=10)

        sc_txt = ctk.CTkLabel(
            sc_card, text=t("set_shortcut_prtscn"),
            font=ctk.CTkFont(family="Segoe UI", size=13), text_color="#FFFFFF",
            anchor="w", wraplength=310, justify="left"
        )
        sc_txt.pack(side=tk.LEFT, padx=12, pady=14, fill=tk.BOTH, expand=True)

        # ---------------------------------------------------------------------
        # BÖLÜM 4: Görünüm (Dil ve Tema Seçimi)
        # ---------------------------------------------------------------------
        _add_section_header(t("sec_appearance"))

        # 1. Uygulama Dili Seçimi Kartı
        lang_card = ctk.CTkFrame(scroll, fg_color="#282828", border_width=1, border_color="#363636", corner_radius=6)
        lang_card.pack(fill=tk.X, pady=3)

        def _on_lang_select(selected_val):
            code = i18n.get_language_code_from_option(selected_val)
            i18n.set_language(code)
            self.root.title(f"{t('app_title')} - {t('settings_title')}")
            # Arayüzü anında yeni dille baştan oluştur
            self._build_settings_ui()

        lang_options = i18n.get_language_dropdown_options()
        cur_lang_label = i18n.get_current_option_label()

        lang_opt = ctk.CTkOptionMenu(
            lang_card, values=lang_options,
            fg_color="#333333", button_color="#383838", button_hover_color="#444444",
            dropdown_fg_color="#252525", corner_radius=6, width=170, height=32,
            font=ctk.CTkFont(family="Segoe UI", size=12), command=_on_lang_select
        )
        lang_opt.set(cur_lang_label)
        lang_opt.pack(side=tk.RIGHT, padx=12, pady=10)

        lang_txt_frame = ctk.CTkFrame(lang_card, fg_color="transparent")
        lang_txt_frame.pack(side=tk.LEFT, padx=12, pady=10, fill=tk.BOTH, expand=True)

        lang_t_lbl = ctk.CTkLabel(
            lang_txt_frame, text=t("set_language"),
            font=ctk.CTkFont(family="Segoe UI", size=13), text_color="#FFFFFF",
            anchor="w", wraplength=310, justify="left"
        )
        lang_t_lbl.pack(fill=tk.X)

        lang_d_lbl = ctk.CTkLabel(
            lang_txt_frame, text=t("set_language_desc"),
            font=ctk.CTkFont(family="Segoe UI", size=11), text_color="#9E9E9E",
            anchor="w", wraplength=310, justify="left"
        )
        lang_d_lbl.pack(fill=tk.X, pady=(2, 0))

        # 2. Uygulama Teması Kartı
        th_card = ctk.CTkFrame(scroll, fg_color="#282828", border_width=1, border_color="#363636", corner_radius=6)
        th_card.pack(fill=tk.X, pady=3)

        def _on_theme_select(val):
            mode = "dark" if val == t("theme_dark") else ("light" if val == t("theme_light") else "system")
            ctk.set_appearance_mode(mode)
            config.set("app_theme", mode)
            # Arayüzü seçilen temayla anında yenile
            self._build_settings_ui()

        cur_th = config.get("app_theme", "dark")
        cur_th_str = t("theme_dark") if cur_th == "dark" else (t("theme_light") if cur_th == "light" else t("theme_system"))
        th_opt = ctk.CTkOptionMenu(
            th_card, values=[t("theme_dark"), t("theme_light"), t("theme_system")],
            fg_color="#333333", button_color="#383838", button_hover_color="#444444",
            dropdown_fg_color="#252525", corner_radius=6, width=170, height=32,
            font=ctk.CTkFont(family="Segoe UI", size=12), command=_on_theme_select
        )
        th_opt.set(cur_th_str)
        th_opt.pack(side=tk.RIGHT, padx=12, pady=10)

        th_txt = ctk.CTkLabel(
            th_card, text=t("set_theme"),
            font=ctk.CTkFont(family="Segoe UI", size=13), text_color="#FFFFFF",
            anchor="w", wraplength=310, justify="left"
        )
        th_txt.pack(side=tk.LEFT, padx=12, pady=12, fill=tk.BOTH, expand=True)

        # ---------------------------------------------------------------------
        # BÖLÜM 5: Görsel Arama Motoru (Özel Google Lens)
        # ---------------------------------------------------------------------
        _add_section_header(t("sec_lens"))
        _add_switch_card(
            title=t("set_lens_search"),
            desc=t("set_lens_search_desc"),
            config_key="google_lens_enabled"
        )
        _add_switch_card(
            title=t("set_shutter_sound"),
            desc=t("set_shutter_sound_desc"),
            config_key="play_sound"
        )

        # ---------------------------------------------------------------------
        # BÖLÜM 6: Bu uygulama hakkında
        # ---------------------------------------------------------------------
        _add_section_header(t("sec_about"))
        ab_card = ctk.CTkFrame(scroll, fg_color="#282828", border_width=1, border_color="#363636", corner_radius=6)
        ab_card.pack(fill=tk.X, pady=3)

        ab_inner = ctk.CTkFrame(ab_card, fg_color="transparent")
        ab_inner.pack(fill=tk.X, padx=16, pady=14)

        lbl_ab_t = ctk.CTkLabel(
            ab_inner, text=t("app_name_full"),
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), text_color="#FFFFFF", anchor="w"
        )
        lbl_ab_t.pack(fill=tk.X)

        lbl_ab_dev = ctk.CTkLabel(
            ab_inner, text=t("author_credit"),
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color="#60CDFF", anchor="w"
        )
        lbl_ab_dev.pack(fill=tk.X, pady=(2, 4))

        lbl_ab_desc = ctk.CTkLabel(
            ab_inner,
            text=t("about_desc"),
            font=ctk.CTkFont(family="Segoe UI", size=11), text_color="#CCCCCC", anchor="w",
            wraplength=520, justify="left"
        )
        lbl_ab_desc.pack(fill=tk.X, pady=(2, 8))

        # Açık Kaynak ve Lisans Bağlantıları
        links = [
            (t("link_github"), "https://github.com/benmeric/snipping-tool"),
            (t("link_license"), "https://opensource.org/licenses/MIT"),
            (t("link_lens"), "https://lens.google/"),
        ]
        for l_title, l_url in links:
            btn_l = ctk.CTkButton(
                ab_inner, text=f"↗  {l_title}", font=ctk.CTkFont(family="Segoe UI", size=11, underline=True),
                text_color="#60CDFF", fg_color="transparent", hover=False, anchor="w", height=24,
                command=lambda u=l_url: webbrowser.open(u)
            )
            btn_l.pack(fill=tk.X, pady=1)

        def _show_third_party():
            messagebox.showinfo(
                t("dialog_third_party_title"),
                f"{t('app_name_full')}\n"
                f"{t('author_credit')}\n\n"
                f"{t('about_desc')}\n\n"
                f"{t('link_third_party')}:\n"
                "• CustomTkinter (Tom Schimansky, MIT License)\n"
                "• Pillow (PIL Software License)\n"
                "• OpenCV (Apache License 2.0)\n"
                "• sounddevice (MIT License)\n"
                "• mss (Guillaume Roggemans, MIT License)\n"
                "• FFmpeg (LGPL / GPL)\n"
                "• Google Lens Reverse Visual Search API"
            )

        btn_tp = ctk.CTkButton(
            ab_inner, text=f"↗  {t('link_third_party')}",
            font=ctk.CTkFont(family="Segoe UI", size=11, underline=True),
            text_color="#60CDFF", fg_color="transparent", hover=False, anchor="w", height=24,
            command=_show_third_party
        )
        btn_tp.pack(fill=tk.X, pady=(1, 10))

        def _open_feedback_dialog():
            fb_win = ctk.CTkToplevel(self.root)
            fb_win.title(t("feedback_title"))
            fb_win.geometry("440x280")
            fb_win.configure(fg_color="#202020")
            fb_win.attributes("-topmost", True)

            lbl_f = ctk.CTkLabel(
                fb_win, text=t("feedback_heading"),
                font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), text_color="#FFFFFF"
            )
            lbl_f.pack(padx=16, pady=(16, 6), anchor="w")

            txt_fb = ctk.CTkTextbox(
                fb_win, fg_color="#181818", border_width=1, border_color="#333333",
                corner_radius=6, font=ctk.CTkFont(family="Segoe UI", size=12)
            )
            txt_fb.pack(fill=tk.BOTH, expand=True, padx=16, pady=4)
            txt_fb.insert("1.0", t("feedback_placeholder"))

            def _send_fb():
                lbl_f.configure(text=f"✓ {t('feedback_thank_you')}", text_color="#0F9D58")
                fb_win.after(1200, fb_win.destroy)

            btn_s = ctk.CTkButton(
                fb_win, text=t("btn_send"), fg_color="#0078D4", hover_color="#0063B1",
                corner_radius=6, height=32, command=_send_fb
            )
            btn_s.pack(padx=16, pady=12, anchor="e")

        btn_feed = ctk.CTkButton(
            ab_inner, text=t("btn_send_feedback"),
            font=ctk.CTkFont(family="Segoe UI", size=12), text_color="#FFFFFF",
            fg_color="#333333", hover_color="#3E3E3E", corner_radius=4, width=160, height=32,
            command=_open_feedback_dialog
        )
        btn_feed.pack(anchor="w", pady=(4, 0))

    # =========================================================================
    # 3. KIRPMA VE VİDEO TETİKLEYİCİLERİ
    # =========================================================================
    def _launch_ocr_snip(self):
        self.snip_mode = "rect"
        self.on_new_snip()

    def on_new_snip(self):
        if self.is_editor_mode and config.get("ask_save_edited_snip", False) and len(self.history) > 1 and not self._has_saved:
            res = messagebox.askyesnocancel(
                t("app_title"),
                t("prompt_save_changes")
            )
            if res is True:
                if not self.on_save_file():
                    return
            elif res is None:
                return

        self._close_popup()
        self.root.withdraw()

        def _trigger():
            is_vid = (self.capture_type == "video")
            open_snipper(
                master=self.root,
                on_completed=self.on_snip_completed,
                on_video_bbox=self.on_video_bbox_selected,
                on_cancel=self.on_snip_cancelled,
                mode=self.snip_mode,
                is_video=is_vid
            )

        if self.delay_sec > 0:
            threading.Timer(self.delay_sec, _trigger).start()
        else:
            self.root.after(150, _trigger)

    def on_video_bbox_selected(self, bbox: dict):
        start_video_recording(bbox, on_finish=self.on_video_finished, master=self.root)

    def on_video_finished(self, out_file):
        self.root.after(0, self.root.deiconify)
        self.root.after(50, self.root.lift)
        self.root.after(100, self.root.focus_force)

    def on_snip_cancelled(self):
        self.root.deiconify()
        self.root.lift()

    def on_snip_completed(self, img: Image.Image):
        """Fotoğraf kırpıldığında ayarları uygular ve düzenleyiciyi açar."""
        # 1. HDR renk düzeltici ayarı
        if config.get("hdr_color_fix", False):
            enh_col = ImageEnhance.Color(img)
            img = enh_col.enhance(1.25)
            enh_con = ImageEnhance.Contrast(img)
            img = enh_con.enhance(1.15)

        # 2. Her ekran görüntüsüne kenarlık ekle ayarı
        if config.get("add_border", False):
            border_color = config.get("border_color", "#D13438")
            border_width = int(config.get("border_width", 3))
            bordered = img.copy()
            d = ImageDraw.Draw(bordered)
            w, h = bordered.size
            for i in range(border_width):
                d.rectangle([i, i, w - 1 - i, h - 1 - i], outline=border_color)
            img = bordered

        # 4. Otomatik diske kaydetme ayarı
        saved_filepath = None
        if config.get("auto_save_snip", True):
            save_dir = config.get("snip_save_dir")
            if save_dir:
                try:
                    os.makedirs(save_dir, exist_ok=True)
                    now = datetime.datetime.now()
                    prefix = config.get("snip_filename_prefix", "Ekran_Goruntusu")
                    ms = now.microsecond // 1000
                    ts = now.strftime("%Y-%m-%d_%H%M%S")
                    base_name = f"{prefix}_{ts}_{ms:03d}"
                    saved_filepath = os.path.join(save_dir, f"{base_name}.png")
                    counter = 1
                    while os.path.exists(saved_filepath):
                        saved_filepath = os.path.join(save_dir, f"{base_name}_{counter}.png")
                        counter += 1
                    img.save(saved_filepath)
                except Exception as e:
                    print(f"Otomatik kaydetme hatası: {e}")

        # 3. Otomatik panoya kopyalama ayarı (dosya referansı ile, böylece AI yapıştırmalarında 'resim.png' çakışması olmaz)
        if config.get("auto_copy_snip", True):
            copy_image_to_clipboard(img, filepath=saved_filepath)

        # 5. Birden fazla pencere ayarı kontrolü
        if config.get("multi_window", False) and self.is_editor_mode:
            new_win = SnippingEditorWindow(parent=self.root, img=img, on_new_snip=self.on_new_snip, saved_filepath=saved_filepath)
            self.extra_windows.append(new_win)
            self.root.deiconify()
            return

        self.saved_filepath = saved_filepath
        self.current_image = img.copy()
        self.draw_image = img.copy()
        self.history = [self.draw_image.copy()]
        self._has_saved = False

        self._build_editor_ui()

        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after(100, lambda: self.root.attributes("-topmost", False))

        w, h = self.current_image.size
        self.lbl_dim.configure(text=f"{w} × {h} px")

    # =========================================================================
    # 4. WINDOWS 11 DÜZENLEYİCİ ARAYÜZÜ (OCR VE GOOGLE LENS ENTEGRELİ)
    # =========================================================================
    def _build_editor_ui(self):
        self._close_popup()
        self.is_editor_mode = True
        self.is_settings_mode = False
        self._center_on_primary_monitor(1040, 680)
        self.root.minsize(820, 520)
        self.root.title(t("app_title"))

        for widget in self.root.winfo_children():
            widget.destroy()

        # Üst Araç Çubuğu
        self.editor_bar = ctk.CTkFrame(self.root, fg_color="#202020", height=46, corner_radius=0)
        self.editor_bar.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(8, 4))

        # [ + Yeni ]
        self.btn_new = ctk.CTkButton(
            self.editor_bar, text=t("btn_new"),
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#FFFFFF", fg_color="#2B2B2B", hover_color="#363636",
            border_width=1, border_color="#383838", corner_radius=6,
            width=80, height=34, command=self.on_new_snip
        )
        self.btn_new.pack(side=tk.LEFT, padx=(0, 6))

        sep1 = ctk.CTkFrame(self.editor_bar, width=1, height=20, fg_color="#383838")
        sep1.pack(side=tk.LEFT, padx=4)

        # Çizim Araçları
        self.btn_pen = ctk.CTkButton(
            self.editor_bar, image=icon_assets.get_icon_ctk("pen", (18, 18)),
            text=t("tool_pen"), compound="left", width=74, height=34, corner_radius=6,
            fg_color="#0078D4" if self.active_tool == "pen" else "#252525",
            hover_color="#383838", font=ctk.CTkFont(family="Segoe UI", size=12),
            command=lambda: self._select_tool("pen")
        )
        self.btn_pen.pack(side=tk.LEFT, padx=3)

        self.btn_highlighter = ctk.CTkButton(
            self.editor_bar, image=icon_assets.get_icon_ctk("highlighter", (18, 18)),
            text=t("tool_highlighter"), compound="left", width=78, height=34, corner_radius=6,
            fg_color="#0078D4" if self.active_tool == "highlighter" else "#252525",
            hover_color="#383838", font=ctk.CTkFont(family="Segoe UI", size=12),
            command=lambda: self._select_tool("highlighter")
        )
        self.btn_highlighter.pack(side=tk.LEFT, padx=3)

        self.btn_eraser = ctk.CTkButton(
            self.editor_bar, image=icon_assets.get_icon_ctk("eraser", (18, 18)),
            text=t("tool_eraser"), compound="left", width=68, height=34, corner_radius=6,
            fg_color="#0078D4" if self.active_tool == "eraser" else "#252525",
            hover_color="#383838", font=ctk.CTkFont(family="Segoe UI", size=12),
            command=lambda: self._select_tool("eraser")
        )
        self.btn_eraser.pack(side=tk.LEFT, padx=3)

        self.btn_undo = ctk.CTkButton(
            self.editor_bar, image=icon_assets.get_icon_ctk("undo", (18, 18)),
            text="", width=34, height=34, corner_radius=6, fg_color="#252525", hover_color="#383838",
            command=self.on_undo
        )
        self.btn_undo.pack(side=tk.LEFT, padx=3)

        sep2 = ctk.CTkFrame(self.editor_bar, width=1, height=20, fg_color="#383838")
        sep2.pack(side=tk.LEFT, padx=6)

        # Metin Ayıkla (OCR)
        self.btn_ocr = ctk.CTkButton(
            self.editor_bar, image=icon_assets.get_icon_ctk("ocr", (18, 18)),
            text=t("btn_ocr"), compound="left",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#1F4E79", hover_color="#2E75B6", corner_radius=6,
            width=120, height=34, command=self.on_extract_text_ocr
        )
        self.btn_ocr.pack(side=tk.LEFT, padx=4)

        # Google Lens Arama Butonu (Ayar açıksa)
        if config.get("google_lens_enabled", True):
            self.btn_lens = ctk.CTkButton(
                self.editor_bar, image=icon_assets.get_icon_ctk("google_lens", (20, 20)),
                text=t("btn_lens"), compound="left",
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                fg_color="#0B3820", hover_color="#144F2E",
                border_width=1, border_color="#1A5935", corner_radius=6,
                width=172, height=34, command=self.on_google_lens_search
            )
            self.btn_lens.pack(side=tk.LEFT, padx=5)

        self.btn_combine = ctk.CTkButton(
            self.editor_bar, image=icon_assets.get_icon_ctk("combine", (18, 18)),
            text=t("btn_combine"), compound="left",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="#252525", hover_color="#383838", corner_radius=6,
            width=92, height=34, command=self.open_image_combiner
        )
        self.btn_combine.pack(side=tk.LEFT, padx=4)

        # Kapat Butonu ✕ (Unsaved check destekli)
        self.btn_back = ctk.CTkButton(
            self.editor_bar, text="✕", width=36, height=34, corner_radius=6,
            fg_color="transparent", hover_color="#C42B1C",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            command=self._on_close_editor
        )
        self.btn_back.pack(side=tk.RIGHT)

        self.btn_save = ctk.CTkButton(
            self.editor_bar, image=icon_assets.get_icon_ctk("save", (18, 18)),
            text="", width=36, height=34, corner_radius=6, fg_color="#252525", hover_color="#383838",
            command=self.on_save_file
        )
        self.btn_save.pack(side=tk.RIGHT, padx=3)

        self.btn_copy = ctk.CTkButton(
            self.editor_bar, image=icon_assets.get_icon_ctk("copy", (18, 18)),
            text="", width=36, height=34, corner_radius=6, fg_color="#252525", hover_color="#383838",
            command=self.on_copy_clipboard
        )
        self.btn_copy.pack(side=tk.RIGHT, padx=3)

        self.divider2 = ctk.CTkFrame(self.root, fg_color="#2D2D2D", height=1)
        self.divider2.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(2, 0))

        # Görsel Alanı
        self.canvas_frame = ctk.CTkFrame(self.root, fg_color="#181818", corner_radius=0)
        self.canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=0, pady=0)

        self.canvas = tk.Canvas(self.canvas_frame, bg="#181818", highlightthickness=0, bd=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Alt Durum Çubuğu
        self.footer = ctk.CTkFrame(self.root, fg_color="#202020", height=28, corner_radius=0)
        self.footer.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=(0, 4))

        self.lbl_status = ctk.CTkLabel(
            self.footer, text=f"✓  {t('status_copied')}",
            font=ctk.CTkFont(family="Segoe UI", size=11), text_color="#0F9D58"
        )
        self.lbl_status.pack(side=tk.LEFT)

        w, h = self.current_image.size
        self.lbl_dim = ctk.CTkLabel(
            self.footer, text=f"{w} × {h} px",
            font=ctk.CTkFont(family="Segoe UI", size=11), text_color="#888888"
        )
        self.lbl_dim.pack(side=tk.RIGHT)

        self.canvas.bind("<ButtonPress-1>", self._on_canvas_press)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.canvas.bind("<Configure>", lambda e: self._render_current_image())

        self.root.after(50, self._render_current_image)

    def _on_close_editor(self):
        if config.get("ask_save_edited_snip", False) and len(self.history) > 1 and not self._has_saved:
            res = messagebox.askyesnocancel(
                t("app_title"),
                t("prompt_save_changes")
            )
            if res is True:
                if self.on_save_file():
                    self._build_compact_ui()
            elif res is False:
                self._build_compact_ui()
        else:
            self._build_compact_ui()

    def _on_window_close(self):
        if self.is_editor_mode and config.get("ask_save_edited_snip", False) and len(self.history) > 1 and not self._has_saved:
            res = messagebox.askyesnocancel(
                t("app_title"),
                t("prompt_save_changes")
            )
            if res is True:
                if self.on_save_file():
                    self.root.destroy()
            elif res is False:
                self.root.destroy()
        else:
            self.root.destroy()

    def _select_tool(self, tool_name):
        self.active_tool = "none" if self.active_tool == tool_name else tool_name
        self.btn_pen.configure(fg_color="#0078D4" if self.active_tool == "pen" else "#252525")
        self.btn_highlighter.configure(fg_color="#0078D4" if self.active_tool == "highlighter" else "#252525")
        self.btn_eraser.configure(fg_color="#0078D4" if self.active_tool == "eraser" else "#252525")
        self.canvas.configure(cursor="crosshair" if self.active_tool in ("pen", "highlighter", "eraser") else "")

    def _render_current_image(self, image_to_render=None):
        target = image_to_render if image_to_render is not None else self.draw_image
        if not hasattr(self, "canvas") or target is None:
            return

        self.canvas.delete("all")
        cw = self.canvas.winfo_width() or 800
        ch = self.canvas.winfo_height() or 500
        iw, ih = target.size

        scale = min(cw / iw, ch / ih, 1.0)
        new_w = max(1, int(iw * scale))
        new_h = max(1, int(ih * scale))

        if scale < 1.0:
            resized = target.resize((new_w, new_h), Image.Resampling.LANCZOS)
        else:
            resized = target

        self.display_image = ImageTk.PhotoImage(resized)
        self.img_x = (cw - new_w) // 2
        self.img_y = (ch - new_h) // 2
        self.scale = scale

        self.canvas.create_rectangle(
            self.img_x - 1, self.img_y - 1, self.img_x + new_w + 1, self.img_y + new_h + 1,
            outline="#333333", width=1
        )
        self.canvas.create_image(self.img_x, self.img_y, image=self.display_image, anchor="nw")

    def _on_canvas_press(self, event):
        if self.draw_image is None or self.active_tool == "none":
            return
        self.last_x = (event.x - self.img_x) / self.scale
        self.last_y = (event.y - self.img_y) / self.scale
        if self.active_tool == "highlighter":
            self.highlighter_pts = [(self.last_x, self.last_y)]

    def _on_canvas_drag(self, event):
        if self.draw_image is None or self.active_tool == "none" or self.last_x is None:
            return

        cur_x = (event.x - self.img_x) / self.scale
        cur_y = (event.y - self.img_y) / self.scale

        if self.active_tool == "pen":
            draw = ImageDraw.Draw(self.draw_image, "RGB")
            draw.line([(self.last_x, self.last_y), (cur_x, cur_y)], fill=self.pen_color, width=self.pen_size)
            self.last_x = cur_x
            self.last_y = cur_y
            self._render_current_image()
        elif self.active_tool == "highlighter":
            self.highlighter_pts.append((cur_x, cur_y))
            if len(self.highlighter_pts) > 1:
                hl_layer = Image.new("RGBA", self.draw_image.size, (0, 0, 0, 0))
                ImageDraw.Draw(hl_layer).line(self.highlighter_pts, fill=(255, 235, 59, 110), width=22, joint="curve")
                preview = Image.alpha_composite(self.draw_image.convert("RGBA"), hl_layer)
                self._render_current_image(image_to_render=preview)
        elif self.active_tool == "eraser":
            ix, iy = int(cur_x), int(cur_y)
            orig_crop = self.current_image.crop((ix-12, iy-12, ix+12, iy+12))
            self.draw_image.paste(orig_crop, (ix-12, iy-12))
            self.last_x = cur_x
            self.last_y = cur_y
            self._render_current_image()

    def _on_canvas_release(self, event):
        if self.draw_image is not None and self.active_tool != "none":
            if self.active_tool == "highlighter" and len(self.highlighter_pts) > 1:
                hl_layer = Image.new("RGBA", self.draw_image.size, (0, 0, 0, 0))
                ImageDraw.Draw(hl_layer).line(self.highlighter_pts, fill=(255, 235, 59, 110), width=22, joint="curve")
                self.draw_image = Image.alpha_composite(self.draw_image.convert("RGBA"), hl_layer).convert("RGB")
                self.highlighter_pts = []
                self._render_current_image()

            self.history.append(self.draw_image.copy())
            if len(self.history) > 15:
                self.history.pop(0)

            self._has_saved = False

            # "Beni otomatik olarak kopyala" açıksa her çizimde güncel görsel panoya kopyalanır
            if config.get("auto_copy_snip", True):
                copy_image_to_clipboard(self.draw_image)
                self.lbl_status.configure(text=f"✓  {t('status_edit_copied')}", text_color="#0F9D58")

        self.last_x = None
        self.last_y = None
        self.highlighter_pts = []

    def on_undo(self):
        if len(self.history) > 1:
            self.history.pop()
            self.draw_image = self.history[-1].copy()
            self._render_current_image()
            self._has_saved = False
            if config.get("auto_copy_snip", True):
                copy_image_to_clipboard(self.draw_image)
                self.lbl_status.configure(text=f"↩️  {t('status_undo_copied')}", text_color="#0F9D58")
            else:
                self.lbl_status.configure(text=f"↩️  {t('status_undo')}", text_color="#FFFFFF")

    def on_save_file(self):
        if self.draw_image is None:
            return False

        now = datetime.datetime.now()
        prefix = config.get("snip_filename_prefix", "Ekran_Goruntusu")
        suggested_name = f"{prefix}_{now.strftime('%Y-%m-%d_%H%M%S')}.png"

        file_path = filedialog.asksaveasfilename(
            initialfile=suggested_name,
            defaultextension=".png",
            filetypes=[
                (f"{t('filetype_png')} (*.png)", "*.png"),
                (f"{t('filetype_jpg')} (*.jpg)", "*.jpg"),
                (f"{t('filetype_all')} (*.*)", "*.*")
            ]
        )
        if file_path:
            self.draw_image.save(file_path)
            self._has_saved = True
            self.saved_filepath = file_path
            self.lbl_status.configure(text=f"✓  {t('status_saved')}: {os.path.basename(file_path)}", text_color="#0F9D58")
            return True
        return False

    def on_copy_clipboard(self):
        if self.draw_image:
            has_unsaved = (len(self.history) > 1 and not self._has_saved)
            fp = getattr(self, "saved_filepath", None) if not has_unsaved else None
            copy_image_to_clipboard(self.draw_image, filepath=fp)
            self.lbl_status.configure(text=f"✓  {t('copied_toast')}!", text_color="#0F9D58")

    def on_google_lens_search(self):
        if self.draw_image is None:
            return

        self.btn_lens.configure(state="disabled", text=f"⏳ {t('status_searching')}...")
        self.lbl_status.configure(text=f"🔍 {t('status_uploading_lens')}", text_color="#FFB900")

        def _search():
            url = search_image_in_google_lens(self.draw_image, open_browser=True)
            def _done():
                self.btn_lens.configure(state="normal", text=t("btn_lens"))
                if url:
                    self.lbl_status.configure(text=f"✓  {t('status_lens_opened')}", text_color="#0F9D58")
                else:
                    self.lbl_status.configure(text=f"✕  {t('status_upload_failed')}", text_color="#E81123")
            self.root.after(0, _done)

        threading.Thread(target=_search, daemon=True).start()

    def on_extract_text_ocr(self):
        if self.draw_image is None:
            return

        self.btn_ocr.configure(state="disabled", text=f"⏳ {t('status_scanning')}...")
        self.lbl_status.configure(text=f"🔤 {t('status_scanning_text')}", text_color="#FFB900")

        def _ocr_thread():
            text = extract_text_from_image(self.draw_image)
            def _done():
                self.btn_ocr.configure(state="normal", text=t("btn_ocr"))
                if text:
                    self.lbl_status.configure(text=f"✓  {t('status_text_copied')}", text_color="#0F9D58")
                    self._show_ocr_dialog(text)
                else:
                    self.lbl_status.configure(text=t("status_no_text"), text_color="#888888")
                    messagebox.showinfo(t("ocr_dialog_title"), t("ocr_no_text"))
            self.root.after(0, _done)

        threading.Thread(target=_ocr_thread, daemon=True).start()

    def _show_ocr_dialog(self, extracted_text: str):
        dlg = ctk.CTkToplevel(self.root)
        dlg.title(t("ocr_dialog_title"))
        dlg.geometry("540x420")
        dlg.minsize(440, 320)
        dlg.configure(fg_color="#202020")
        dlg.attributes("-topmost", True)

        header = ctk.CTkFrame(dlg, fg_color="transparent")
        header.pack(fill=tk.X, padx=16, pady=(16, 8))

        lbl_h = ctk.CTkLabel(
            header, image=icon_assets.get_icon_ctk("ocr", (20, 20)),
            text=f"  {t('ocr_extracted_text')}", compound="left",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"), text_color="#FFFFFF"
        )
        lbl_h.pack(side=tk.LEFT)

        lbl_sub = ctk.CTkLabel(
            dlg, text=t("ocr_auto_copied_hint"),
            font=ctk.CTkFont(family="Segoe UI", size=11), text_color="#AAAAAA"
        )
        lbl_sub.pack(anchor="w", padx=16, pady=(0, 8))

        txt_box = ctk.CTkTextbox(
            dlg, fg_color="#181818", border_width=1, border_color="#333333",
            corner_radius=8, font=ctk.CTkFont(family="Segoe UI", size=13), text_color="#FFFFFF"
        )
        txt_box.pack(fill=tk.BOTH, expand=True, padx=16, pady=4)
        txt_box.insert("1.0", extracted_text)

        bottom_bar = ctk.CTkFrame(dlg, fg_color="transparent")
        bottom_bar.pack(fill=tk.X, padx=16, pady=14)

        def _copy_again():
            content = txt_box.get("1.0", "end-1c")
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            btn_copy_all.configure(text=f"✓  {t('copied_toast')}!")
            dlg.after(1500, lambda: btn_copy_all.configure(text=f"  {t('ocr_copy_all')}"))

        btn_copy_all = ctk.CTkButton(
            bottom_bar, image=icon_assets.get_icon_ctk("copy", (16, 16)),
            text=f"  {t('ocr_copy_all')}", compound="left",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#0078D4", hover_color="#0063B1", corner_radius=6, height=34,
            command=_copy_again
        )
        btn_copy_all.pack(side=tk.LEFT)

        btn_close_dlg = ctk.CTkButton(
            bottom_bar, text=t("btn_close"), font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="#2B2B2B", hover_color="#383838", corner_radius=6, height=34, width=80,
            command=dlg.destroy
        )
        btn_close_dlg.pack(side=tk.RIGHT)

    def open_image_combiner(self, initial_images=None):
        """Çoklu görsel birleştirme / kolaj penceresini açar."""
        from image_combiner import ImageCombinerWindow
        if initial_images is None:
            if self.is_editor_mode and hasattr(self, 'draw_image') and self.draw_image:
                initial_images = [self.draw_image.copy()]
            else:
                initial_images = []
        ImageCombinerWindow(
            parent=self.root,
            initial_images=initial_images,
            on_open_in_editor=self._load_image_from_combiner
        )

    def _load_image_from_combiner(self, img: Image.Image):
        """Birleştirilmiş kolaj görselini ana düzenleyiciye aktarır."""
        self.current_image = img.copy()
        self.draw_image = img.copy()
        self.history = [self.draw_image.copy()]
        self._has_saved = False
        self._build_editor_ui()
        self.root.deiconify()
        self.root.lift()
        w, h = self.current_image.size
        self.lbl_dim.configure(text=f"{w} × {h} px")
        self.lbl_status.configure(text=f"✓ {t('combiner_title_suffix')}")

    def _show_info_dialog(self):
        messagebox.showinfo(
            f"{t('app_title')} - {t('sec_about')}",
            f"{t('app_title')}\n"
            f"{t('author_credit')}\n\n"
            f"{t('about_desc')}\n\n"
            "• PrtScn / Win+Shift+S : Snipping / Ekran Alıntısı\n"
            "• Ctrl+G : Google Lens\n"
            "• Ctrl+, : Settings / Ayarlar\n"
            "• Ctrl+C : Copy | Ctrl+S : Save"
        )

    def run(self):
        self.root.mainloop()


def launch_app():
    app = EkranAlintisiAraci()
    app.run()


if __name__ == "__main__":
    launch_app()

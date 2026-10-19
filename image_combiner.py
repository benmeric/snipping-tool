"""
Ekran Alıntısı Aracı - Çoklu Ekran Görüntüsü Birleştirme / Kolaj Modu (Image Combiner)
========================================================================
Birden fazla ekran alıntısını, panodaki görselleri veya diskteki resimleri
tek bir görselde birleştirir.

Özellikler:
- ↕ Dikey (Alt alta)
- ↔ Yatay (Yan yana)
- ⊞ Izgara (2'li / Akıllı tablo)
- 🔢 Yapay Zeka (AI) modelleri için otomatik numaralandırma ([1], [2], [3] rozetleri)
- 🎯 Ayarlanabilir boşluk (padding/spacing) ve arka plan renkleri (Koyu, Açık, Beyaz, Siyah, Şeffaf)
- 📋 64-bit Windows Panoya zaman damgalı kopyalama (AI araçlarında çakışma yapmaz)
- ✏️ Doğrudan Ekran Alıntısı Düzenleyicisinde açma ve Google Lens ile arama desteği
"""

import os
import math
import datetime
from tkinter import filedialog, messagebox
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont, ImageTk, ImageGrab

import icon_assets
from i18n import t
from config import config
from screen_capture import copy_image_to_clipboard
from google_lens import search_image_in_google_lens
from snipping_overlay import open_snipper


def _get_font(size: int):
    """Sistem fontunu (Segoe UI veya Arial) güvenli şekilde döndürür."""
    font_names = ["segoeuib.ttf", "segoeui.ttf", "arialbd.ttf", "arial.ttf", "tahoma.ttf"]
    for fn in font_names:
        try:
            return ImageFont.truetype(fn, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default()
    except Exception:
        return None


def draw_number_badge(img: Image.Image, number: int, badge_size: int = 34, accent_color: str = "#0078D4") -> Image.Image:
    """Görselin sol üst köşesine yapay zeka modelleri için belirgin, şık ve okunabilir
    [1], [2], [3] numaralı rozet çizer.
    """
    out = img.copy().convert("RGBA")
    d = ImageDraw.Draw(out)
    
    # Rozet boyutunu görsel boyutuna göre orantıla (en az 28px, en fazla 56px)
    min_dim = min(out.width, out.height)
    actual_size = max(28, min(56, int(min_dim * 0.08)))
    
    margin = int(actual_size * 0.35)
    radius = int(actual_size * 0.28)
    
    x1 = margin
    y1 = margin
    x2 = margin + actual_size
    y2 = margin + actual_size
    
    # Hafif yarı saydam gölge efekti
    shadow_offset = max(2, int(actual_size * 0.08))
    d.rounded_rectangle(
        [x1 + shadow_offset, y1 + shadow_offset, x2 + shadow_offset, y2 + shadow_offset],
        radius=radius,
        fill=(0, 0, 0, 140)
    )
    
    # Ana rozet gövdesi (Windows Fluent Mavi veya Koyu Arka Plan)
    d.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=accent_color, outline=(255, 255, 255, 220), width=max(1, int(actual_size * 0.05)))
    
    # Sayı metni
    font_size = int(actual_size * 0.58)
    font = _get_font(font_size)
    text = str(number)
    
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    
    if font:
        try:
            d.text((cx, cy), text, fill=(255, 255, 255, 255), font=font, anchor="mm")
        except Exception:
            d.text((x1 + actual_size * 0.3, y1 + actual_size * 0.2), text, fill=(255, 255, 255, 255))
    else:
        d.text((x1 + actual_size * 0.3, y1 + actual_size * 0.2), text, fill=(255, 255, 255, 255))
        
    return out


def combine_snips(
    images: list[Image.Image],
    layout: str = "vertical",
    spacing: int = 12,
    bg_color: str = "#1E1E1E",
    add_numbers: bool = True,
    padding: int = 16,
    fit_dimensions: bool = False
) -> Image.Image:
    """Verilen PIL Image listesini belirtilen düzen ve ayarlarla tek bir kolaj haline getirir."""
    if not images:
        return Image.new("RGBA", (400, 300), (30, 30, 30, 255))

    # Gerekirse numaralandırma rozetlerini ekle
    processed_images = []
    for i, orig_img in enumerate(images, start=1):
        im = orig_img.copy()
        if add_numbers:
            im = draw_number_badge(im, i)
        processed_images.append(im)

    n = len(processed_images)
    
    # Arka plan rengini parse et
    is_transparent = (bg_color.lower() in ("transparent", "seffaf", "şeffaf", "none"))
    if is_transparent:
        bg_rgba = (0, 0, 0, 0)
        mode = "RGBA"
    else:
        hex_c = bg_color.lstrip("#")
        if len(hex_c) == 6:
            r = int(hex_c[0:2], 16)
            g = int(hex_c[2:4], 16)
            b = int(hex_c[4:6], 16)
            bg_rgba = (r, g, b, 255)
        else:
            bg_rgba = (30, 30, 30, 255)
        mode = "RGBA"

    if layout == "vertical":
        # DİKEY DÜZEN: Alt alta sırala
        max_w = max(img.width for img in processed_images)
        
        # Eğer fit_dimensions aktifse tüm görselleri max_w genişliğine orantılı ölçekle
        final_imgs = []
        for img in processed_images:
            if fit_dimensions and img.width != max_w and img.width > 0:
                new_h = max(1, int(img.height * (max_w / img.width)))
                final_imgs.append(img.resize((max_w, new_h), Image.Resampling.LANCZOS))
            else:
                final_imgs.append(img)
                
        total_h = sum(img.height for img in final_imgs) + (n - 1) * spacing + 2 * padding
        total_w = max_w + 2 * padding
        
        canvas = Image.new(mode, (total_w, total_h), bg_rgba)
        cur_y = padding
        for img in final_imgs:
            cur_x = padding + (max_w - img.width) // 2
            canvas.paste(img, (cur_x, cur_y), img if img.mode == "RGBA" else None)
            cur_y += img.height + spacing
        return canvas

    elif layout == "horizontal":
        # YATAY DÜZEN: Yan yana sırala
        max_h = max(img.height for img in processed_images)
        
        final_imgs = []
        for img in processed_images:
            if fit_dimensions and img.height != max_h and img.height > 0:
                new_w = max(1, int(img.width * (max_h / img.height)))
                final_imgs.append(img.resize((new_w, max_h), Image.Resampling.LANCZOS))
            else:
                final_imgs.append(img)
                
        total_w = sum(img.width for img in final_imgs) + (n - 1) * spacing + 2 * padding
        total_h = max_h + 2 * padding
        
        canvas = Image.new(mode, (total_w, total_h), bg_rgba)
        cur_x = padding
        for img in final_imgs:
            cur_y = padding + (max_h - img.height) // 2
            canvas.paste(img, (cur_x, cur_y), img if img.mode == "RGBA" else None)
            cur_x += img.width + spacing
        return canvas

    elif layout == "grid":
        # IZGARA DÜZEN: 2 sütunlu veya kareye yakın akıllı matris
        if n <= 1:
            cols = 1
        elif n <= 4:
            cols = 2
        elif n <= 9:
            cols = 3
        else:
            cols = math.ceil(math.sqrt(n))
            
        rows = math.ceil(n / cols)
        
        # Her sütunun genişliğini ve her satırın yüksekliğini hesapla
        col_widths = [0] * cols
        row_heights = [0] * rows
        
        for idx, img in enumerate(processed_images):
            r = idx // cols
            c = idx % cols
            if img.width > col_widths[c]:
                col_widths[c] = img.width
            if img.height > row_heights[r]:
                row_heights[r] = img.height
                
        total_w = sum(col_widths) + (cols - 1) * spacing + 2 * padding
        total_h = sum(row_heights) + (rows - 1) * spacing + 2 * padding
        
        canvas = Image.new(mode, (total_w, total_h), bg_rgba)
        
        for idx, img in enumerate(processed_images):
            r = idx // cols
            c = idx % cols
            
            # Sütun ve satır başlangıç ofsetleri
            cell_x = padding + sum(col_widths[:c]) + c * spacing
            cell_y = padding + sum(row_heights[:r]) + r * spacing
            
            # Hücre içinde ortala
            img_x = cell_x + (col_widths[c] - img.width) // 2
            img_y = cell_y + (row_heights[r] - img.height) // 2
            
            canvas.paste(img, (img_x, img_y), img if img.mode == "RGBA" else None)
            
        return canvas

    return processed_images[0]


class ImageCombinerWindow(ctk.CTkToplevel):
    """Çoklu Ekran Görüntüsü Birleştirme ve Kolaj Penceresi."""
    def __init__(self, parent, initial_images: list[Image.Image] = None, on_open_in_editor=None):
        super().__init__(parent)
        self.title(t("combiner_title"))
        self.geometry("1120x720")
        self.minsize(860, 560)
        self.configure(fg_color="#202020")
        
        self.parent_app = parent
        self.on_open_in_editor = on_open_in_editor
        self.images: list[Image.Image] = [img.copy() for img in (initial_images or [])]
        self.combined_cache: Image.Image = None
        self.preview_tk = None
        
        # Kolaj Ayarları
        self.layout_mode = "vertical"  # "vertical", "horizontal", "grid"
        self.spacing_val = 12
        self.add_numbers = True
        self.bg_color_val = "#1E1E1E"
        self.fit_dims = False
        
        icon_assets.apply_window_icon(self)
            
        self._build_ui()
        self._center_window()
        self._refresh_all()
        
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _center_window(self):
        try:
            from snipping_overlay import get_primary_monitor
            mon = get_primary_monitor()
            w, h = 1120, 720
            x = mon["left"] + (mon["width"] - w) // 2
            y = mon["top"] + (mon["height"] - h) // 2
            self.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass

    def _build_ui(self):
        # 1. ÜST ARAÇ ÇUBUĞU (KOLAJ AYARLARI)
        self.top_bar = ctk.CTkFrame(self, fg_color="#242424", height=48, corner_radius=0)
        self.top_bar.pack(side=tk.TOP, fill=tk.X, padx=0, pady=0)
        
        # Sol: Başlık ve Rozet
        title_box = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        title_box.pack(side=tk.LEFT, padx=(16, 20), pady=8)
        
        lbl_icon = ctk.CTkLabel(title_box, image=icon_assets.get_icon_ctk("combine", (20, 20)), text="")
        lbl_icon.pack(side=tk.LEFT, padx=(0, 8))
        
        lbl_t = ctk.CTkLabel(
            title_box, text=t("btn_combine_tip"),
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#FFFFFF"
        )
        lbl_t.pack(side=tk.LEFT)

        sep1 = ctk.CTkFrame(self.top_bar, width=1, height=24, fg_color="#383838")
        sep1.pack(side=tk.LEFT, padx=8)

        # Düzen Seçici (Dikey, Yatay, Izgara)
        lbl_layout = ctk.CTkLabel(
            self.top_bar, text=t("combiner_layout"),
            font=ctk.CTkFont(family="Segoe UI", size=12), text_color="#CCCCCC"
        )
        lbl_layout.pack(side=tk.LEFT, padx=(4, 6))

        self.seg_layout = ctk.CTkSegmentedButton(
            self.top_bar,
            values=[f"↕ {t('combiner_vertical')}", f"↔ {t('combiner_horizontal')}", f"⊞ {t('combiner_grid')}"],
            font=ctk.CTkFont(family="Segoe UI", size=12),
            height=30,
            command=self._on_layout_change
        )
        self.seg_layout.set(f"↕ {t('combiner_vertical')}")
        self.seg_layout.pack(side=tk.LEFT, padx=(0, 14))

        # Boşluk Seçici
        lbl_space = ctk.CTkLabel(
            self.top_bar, text=t("combiner_spacing"),
            font=ctk.CTkFont(family="Segoe UI", size=12), text_color="#CCCCCC"
        )
        lbl_space.pack(side=tk.LEFT, padx=(4, 6))

        self.opt_spacing = ctk.CTkOptionMenu(
            self.top_bar,
            values=["0 px", "8 px", "12 px", "20 px", "32 px"],
            width=90, height=30,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="#333333", button_color="#3A3A3A", button_hover_color="#444444",
            dropdown_fg_color="#282828",
            command=self._on_spacing_change
        )
        self.opt_spacing.set("12 px")
        self.opt_spacing.pack(side=tk.LEFT, padx=(0, 14))

        # AI Numaralandırma Aç/Kapat Switch
        self.sw_numbers = ctk.CTkSwitch(
            self.top_bar,
            text=t("combiner_ai_badges"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#FFFFFF",
            progress_color="#0078D4",
            command=self._on_numbers_toggle
        )
        self.sw_numbers.select()
        self.sw_numbers.pack(side=tk.LEFT, padx=(4, 14))

        # Arka Plan Seçici
        lbl_bg = ctk.CTkLabel(
            self.top_bar, text=t("combiner_bg"),
            font=ctk.CTkFont(family="Segoe UI", size=12), text_color="#CCCCCC"
        )
        lbl_bg.pack(side=tk.LEFT, padx=(4, 6))

        self.opt_bg = ctk.CTkOptionMenu(
            self.top_bar,
            values=[t("bg_dark"), t("bg_light"), t("bg_white"), t("bg_black"), t("bg_transparent")],
            width=120, height=30,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="#333333", button_color="#3A3A3A", button_hover_color="#444444",
            dropdown_fg_color="#282828",
            command=self._on_bg_change
        )
        self.opt_bg.set(t("bg_dark"))
        self.opt_bg.pack(side=tk.LEFT, padx=(0, 10))

        # Sağ: Kapat butonu
        self.btn_close = ctk.CTkButton(
            self.top_bar, text="✕", width=34, height=30, corner_radius=6,
            fg_color="transparent", hover_color="#C42B1C",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            command=self.destroy
        )
        self.btn_close.pack(side=tk.RIGHT, padx=12)

        # 2. AYIRICI ÇİZGİ
        divider = ctk.CTkFrame(self, fg_color="#303030", height=1)
        divider.pack(side=tk.TOP, fill=tk.X)

        # 3. ANA GÖVDE (SOL LİSTE + SAĞ ÖNİZLEME)
        self.main_body = ctk.CTkFrame(self, fg_color="#1C1C1C", corner_radius=0)
        self.main_body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # SOL PANEL: Görsel Kuyruğu ve Ekleme Butonları
        self.left_panel = ctk.CTkFrame(self.main_body, fg_color="#222222", width=280, corner_radius=0)
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=0, pady=0)
        self.left_panel.pack_propagate(False)

        # Sol Panel Başlık
        lh_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent", height=40)
        lh_frame.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(10, 4))

        self.lbl_count = ctk.CTkLabel(
            lh_frame, text=f"{t('combiner_images')} (0)",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#FFFFFF"
        )
        self.lbl_count.pack(side=tk.LEFT)

        self.btn_clear_all = ctk.CTkButton(
            lh_frame, text=t("combiner_clear"), width=58, height=24, corner_radius=4,
            fg_color="transparent", hover_color="#3E2020", text_color="#FF6B6B",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            command=self._on_clear_all
        )
        self.btn_clear_all.pack(side=tk.RIGHT)

        # Ekleme Aksiyon Butonları (Hızlı İşlemler)
        action_box = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        action_box.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(4, 8))

        self.btn_add_snip = ctk.CTkButton(
            action_box,
            image=icon_assets.get_icon_ctk("plus", (16, 16)),
            text=f"  {t('combiner_new_snip')}",
            compound="left",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#0078D4", hover_color="#0063B1",
            height=32, corner_radius=6,
            command=self._on_add_new_snip
        )
        self.btn_add_snip.pack(fill=tk.X, pady=(0, 4))

        sub_btns = ctk.CTkFrame(action_box, fg_color="transparent")
        sub_btns.pack(fill=tk.X)

        self.btn_add_clipboard = ctk.CTkButton(
            sub_btns, text=f"📋 {t('combiner_paste_clip')}",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color="#2D2D2D", hover_color="#3A3A3A",
            height=28, corner_radius=5,
            command=self._on_add_clipboard
        )
        self.btn_add_clipboard.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        self.btn_add_file = ctk.CTkButton(
            sub_btns, text=f"📂 {t('combiner_add_image')}",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color="#2D2D2D", hover_color="#3A3A3A",
            height=28, corner_radius=5,
            command=self._on_add_file
        )
        self.btn_add_file.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))

        # Sol Kaydırılabilir Görsel Listesi
        self.scroll_list = ctk.CTkScrollableFrame(self.left_panel, fg_color="#1E1E1E", corner_radius=6)
        self.scroll_list.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=(4, 8))

        # SAĞ PANEL: Canlı Önizleme Alanı
        self.preview_panel = ctk.CTkFrame(self.main_body, fg_color="#181818", corner_radius=0)
        self.preview_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.preview_canvas = tk.Canvas(self.preview_panel, bg="#181818", highlightthickness=0, bd=0)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        self.preview_canvas.bind("<Configure>", lambda e: self._render_preview())

        # 4. ALT AKSİYON ÇUBUĞU (KOPYALA, KAYDET, DÜZENLEYİCİ, LENS)
        self.bottom_bar = ctk.CTkFrame(self, fg_color="#202020", height=48, corner_radius=0)
        self.bottom_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=0, pady=0)

        self.lbl_status = ctk.CTkLabel(
            self.bottom_bar, text=t("status_ready"),
            font=ctk.CTkFont(family="Segoe UI", size=12), text_color="#A0A0A0"
        )
        self.lbl_status.pack(side=tk.LEFT, padx=16)

        self.lbl_dimensions = ctk.CTkLabel(
            self.bottom_bar, text="",
            font=ctk.CTkFont(family="Segoe UI", size=11), text_color="#777777"
        )
        self.lbl_dimensions.pack(side=tk.LEFT, padx=8)

        # Sağ Aksiyon Butonları
        # 1. Google Lens
        if config.get("google_lens_enabled", True):
            self.btn_lens = ctk.CTkButton(
                self.bottom_bar,
                image=icon_assets.get_icon_ctk("google_lens", (18, 18)),
                text=t("combiner_lens"),
                compound="left",
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                fg_color="#0B3820", hover_color="#144F2E",
                border_width=1, border_color="#1A5935", corner_radius=6,
                height=34, width=170,
                command=self._on_google_lens
            )
            self.btn_lens.pack(side=tk.RIGHT, padx=(4, 14))

        # 2. Düzenleyicide Aç
        self.btn_open_editor = ctk.CTkButton(
            self.bottom_bar,
            image=icon_assets.get_icon_ctk("pen", (16, 16)),
            text=t("combiner_open_editor"),
            compound="left",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="#2C2C2C", hover_color="#3A3A3A",
            border_width=1, border_color="#383838", corner_radius=6,
            height=34, width=140,
            command=self._on_open_in_editor_click
        )
        self.btn_open_editor.pack(side=tk.RIGHT, padx=4)

        # 3. Farklı Kaydet
        self.btn_save_as = ctk.CTkButton(
            self.bottom_bar,
            image=icon_assets.get_icon_ctk("save", (16, 16)),
            text=t("combiner_save"),
            compound="left",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="#2C2C2C", hover_color="#3A3A3A",
            border_width=1, border_color="#383838", corner_radius=6,
            height=34, width=100,
            command=self._on_save_as
        )
        self.btn_save_as.pack(side=tk.RIGHT, padx=4)

        # 4. Panoya Kopyala (Vurgulu)
        self.btn_copy = ctk.CTkButton(
            self.bottom_bar,
            image=icon_assets.get_icon_ctk("copy", (16, 16)),
            text=t("combiner_copy"),
            compound="left",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#0078D4", hover_color="#0063B1",
            corner_radius=6, height=34, width=150,
            command=self._on_copy_clipboard
        )
        self.btn_copy.pack(side=tk.RIGHT, padx=4)

    # =========================================================================
    # EVENT HANDLERS & LOGIC
    # =========================================================================
    def _on_layout_change(self, value):
        if "↕" in value or "vertical" in value.lower() or "dikey" in value.lower():
            self.layout_mode = "vertical"
        elif "↔" in value or "horizontal" in value.lower() or "yatay" in value.lower():
            self.layout_mode = "horizontal"
        elif "⊞" in value or "grid" in value.lower() or "izgara" in value.lower():
            self.layout_mode = "grid"
        self._refresh_all()

    def _on_spacing_change(self, value):
        try:
            self.spacing_val = int(value.replace("px", "").strip())
        except Exception:
            self.spacing_val = 12
        self._refresh_all()

    def _on_numbers_toggle(self):
        self.add_numbers = bool(self.sw_numbers.get())
        self._refresh_all()

    def _on_bg_change(self, value):
        v = value.lower()
        if "1e" in v or "koyu" in v or "dark" in v or "dunkel" in v or "sombre" in v or "тёмн" in v:
            self.bg_color_val = "#1E1E1E"
        elif "f5" in v or "açık" in v or "light" in v or "hell" in v or "claro" in v or "clair" in v or "светл" in v:
            self.bg_color_val = "#F3F3F3"
        elif "beyaz" in v or "white" in v or "weiß" in v or "blanco" in v or "blanc" in v or "бел" in v:
            self.bg_color_val = "#FFFFFF"
        elif "siyah" in v or "black" in v or "schwarz" in v or "negro" in v or "noir" in v or "чёрн" in v or "черн" in v:
            self.bg_color_val = "#000000"
        elif "şeffaf" in v or "seffaf" in v or "transparent" in v or "transparente" in v or "прозрач" in v:
            self.bg_color_val = "transparent"
        self._refresh_all()

    def _on_add_new_snip(self):
        """Kullanıcının pencereyi kapatmadan yeni bir ekran alıntısı yapmasını sağlar."""
        self.withdraw()
        
        def on_snip_done(img: Image.Image):
            self.deiconify()
            self.lift()
            self.focus_force()
            if img:
                self.images.append(img)
                self._refresh_all()
                self._show_temp_status(f"✓ {t('combiner_added_snip').format(count=len(self.images))}")
                
        def on_snip_cancel():
            self.deiconify()
            self.lift()
            self.focus_force()
            
        self.after(150, lambda: open_snipper(
            master=self,
            on_completed=on_snip_done,
            on_cancel=on_snip_cancel,
            mode="rect",
            is_video=False
        ))

    def _on_add_clipboard(self):
        """Windows panosundaki görseli listeye ekler."""
        try:
            cb_img = ImageGrab.grabclipboard()
            if isinstance(cb_img, Image.Image):
                self.images.append(cb_img)
                self._refresh_all()
                self._show_temp_status(f"✓ {t('combiner_added_clip').format(count=len(self.images))}")
            elif isinstance(cb_img, list):
                # Dosya yolu kopyalanmış olabilir
                added = 0
                for path in cb_img:
                    if os.path.isfile(path):
                        try:
                            im = Image.open(path)
                            im.load()
                            self.images.append(im)
                            added += 1
                        except Exception:
                            pass
                if added > 0:
                    self._refresh_all()
                    self._show_temp_status(f"✓ {t('combiner_added_files').format(count=added)}")
                else:
                    self._show_temp_status(f"⚠ {t('combiner_no_clip_image')}")
            else:
                self._show_temp_status(f"⚠ {t('combiner_no_clip_image')}")
        except Exception as e:
            self._show_temp_status(f"⚠ {e}")

    def _on_add_file(self):
        """Kullanıcının diskten bir veya birden fazla görsel seçmesini sağlar."""
        files = filedialog.askopenfilenames(
            title=t("combiner_select_images_dialog"),
            filetypes=[
                (f"{t('combiner_image_files')}", "*.png;*.jpg;*.jpeg;*.webp;*.bmp;*.gif"),
                (f"{t('filetype_all')}", "*.*")
            ]
        )
        if files:
            count = 0
            for f in files:
                try:
                    im = Image.open(f)
                    im.load()
                    self.images.append(im)
                    count += 1
                except Exception:
                    pass
            if count > 0:
                self._refresh_all()
                self._show_temp_status(f"✓ {t('combiner_added_files').format(count=count)}")

    def _on_clear_all(self):
        if not self.images:
            return
        if len(self.images) > 1:
            res = messagebox.askyesno(
                t("combiner_clear_title"),
                t("combiner_clear_prompt").format(count=len(self.images)),
                parent=self
            )
            if not res:
                return
        self.images.clear()
        self._refresh_all()
        self._show_temp_status(t("combiner_list_cleared"))

    def _move_up(self, index: int):
        if index > 0:
            self.images[index - 1], self.images[index] = self.images[index], self.images[index - 1]
            self._refresh_all()

    def _move_down(self, index: int):
        if index < len(self.images) - 1:
            self.images[index + 1], self.images[index] = self.images[index], self.images[index + 1]
            self._refresh_all()

    def _remove_image(self, index: int):
        if 0 <= index < len(self.images):
            self.images.pop(index)
            self._refresh_all()

    def _show_temp_status(self, text: str, duration_ms: int = 2500):
        self.lbl_status.configure(text=text, text_color="#60CDFF")
        self.after(duration_ms, lambda: self.lbl_status.configure(text=t("status_ready"), text_color="#A0A0A0"))

    # =========================================================================
    # RENDER & LIST UPDATES
    # =========================================================================
    def _refresh_all(self):
        self.lbl_count.configure(text=f"{t('combiner_images')} ({len(self.images)})")
        
        # 1. Sol Thumbnail Listesini Yeniden Oluştur
        for widget in self.scroll_list.winfo_children():
            widget.destroy()

        if not self.images:
            empty_lbl = ctk.CTkLabel(
                self.scroll_list,
                text=t("combiner_empty_sub"),
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color="#777777",
                justify="center"
            )
            empty_lbl.pack(pady=40, padx=10)
        else:
            for idx, img in enumerate(self.images):
                card = ctk.CTkFrame(self.scroll_list, fg_color="#262626", corner_radius=6, border_width=1, border_color="#363636")
                card.pack(fill=tk.X, pady=3, padx=2)

                # Thumbnail oluştur (64x44)
                tw, th = 64, 44
                thumb_im = img.copy()
                thumb_im.thumbnail((tw, th), Image.Resampling.LANCZOS)
                ctk_thumb = ctk.CTkImage(light_image=thumb_im, dark_image=thumb_im, size=(thumb_im.width, thumb_im.height))

                t_lbl = ctk.CTkLabel(card, image=ctk_thumb, text="", width=tw, height=th)
                t_lbl.pack(side=tk.LEFT, padx=(6, 8), pady=6)

                # Bilgi Metni
                info_box = ctk.CTkFrame(card, fg_color="transparent")
                info_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=4)

                lbl_name = ctk.CTkLabel(
                    info_box, text=f"{t('combiner_image_item')} {idx + 1}",
                    font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                    text_color="#FFFFFF", anchor="w"
                )
                lbl_name.pack(fill=tk.X)

                lbl_dim = ctk.CTkLabel(
                    info_box, text=f"{img.width}×{img.height}",
                    font=ctk.CTkFont(family="Segoe UI", size=10),
                    text_color="#888888", anchor="w"
                )
                lbl_dim.pack(fill=tk.X)

                # Kontrol Butonları (▲, ▼, 🗑)
                btn_box = ctk.CTkFrame(card, fg_color="transparent")
                btn_box.pack(side=tk.RIGHT, padx=4, pady=4)

                btn_up = ctk.CTkButton(
                    btn_box, text="▲", width=22, height=20, corner_radius=3,
                    fg_color="#303030", hover_color="#3E3E3E", font=ctk.CTkFont(size=9),
                    state="normal" if idx > 0 else "disabled",
                    command=lambda i=idx: self._move_up(i)
                )
                btn_up.pack(side=tk.LEFT, padx=1)

                btn_down = ctk.CTkButton(
                    btn_box, text="▼", width=22, height=20, corner_radius=3,
                    fg_color="#303030", hover_color="#3E3E3E", font=ctk.CTkFont(size=9),
                    state="normal" if idx < len(self.images) - 1 else "disabled",
                    command=lambda i=idx: self._move_down(i)
                )
                btn_down.pack(side=tk.LEFT, padx=1)

                btn_del = ctk.CTkButton(
                    btn_box, text="✕", width=22, height=20, corner_radius=3,
                    fg_color="#303030", hover_color="#C42B1C", font=ctk.CTkFont(size=10),
                    command=lambda i=idx: self._remove_image(i)
                )
                btn_del.pack(side=tk.LEFT, padx=1)

        # 2. Kolajı Oluştur ve Önizlemeyi Güncelle
        if self.images:
            self.combined_cache = combine_snips(
                images=self.images,
                layout=self.layout_mode,
                spacing=self.spacing_val,
                bg_color=self.bg_color_val,
                add_numbers=self.add_numbers,
                padding=16,
                fit_dimensions=self.fit_dims
            )
            w, h = self.combined_cache.size
            self.lbl_dimensions.configure(text=f"{t('combiner_combined_size')}: {w} × {h} px")
        else:
            self.combined_cache = None
            self.lbl_dimensions.configure(text="")

        self._render_preview()

    def _render_preview(self):
        """Önizleme tuvalini temizleyip birleştirilmiş görseli responsive fit ile çizer."""
        self.preview_canvas.delete("all")
        
        canv_w = self.preview_canvas.winfo_width()
        canv_h = self.preview_canvas.winfo_height()
        
        if canv_w <= 10 or canv_h <= 10:
            return

        if not self.combined_cache:
            self.preview_canvas.create_text(
                canv_w // 2, canv_h // 2,
                text=t("combiner_preview_empty"),
                fill="#555555",
                font=("Segoe UI", 13),
                justify="center"
            )
            return

        img_w, img_h = self.combined_cache.size
        scale = min((canv_w - 24) / img_w, (canv_h - 24) / img_h, 1.0)
        
        target_w = max(1, int(img_w * scale))
        target_h = max(1, int(img_h * scale))

        preview_img = self.combined_cache.resize((target_w, target_h), Image.Resampling.LANCZOS)
        self.preview_tk = ImageTk.PhotoImage(preview_img)

        cx = canv_w // 2
        cy = canv_h // 2
        self.preview_canvas.create_image(cx, cy, anchor="center", image=self.preview_tk)

    # =========================================================================
    # DIŞA AKTARMA VE ENTEGRASYON İŞLEMLERİ
    # =========================================================================
    def _on_copy_clipboard(self):
        """Birleştirilmiş görseli panoya (CF_HDROP, CF_PNG, CF_DIB) benzersiz isimle kopyalar."""
        if not self.combined_cache:
            self._show_temp_status(f"⚠ {t('combiner_no_images_copy')}")
            return

        ok = copy_image_to_clipboard(self.combined_cache)
        if ok:
            self.btn_copy.configure(text=f"  ✓ {t('copied_toast')}!", fg_color="#107C41")
            self._show_temp_status(f"✓ {t('combiner_copied_detail')}")
            self.after(2000, lambda: self.btn_copy.configure(text=t("combiner_copy"), fg_color="#0078D4"))
        else:
            self._show_temp_status(f"⚠ {t('error_clipboard_copy')}")

    def _on_save_as(self):
        """Birleştirilmiş görseli diske kaydeder."""
        if not self.combined_cache:
            self._show_temp_status(f"⚠ {t('combiner_no_images_save')}")
            return

        now = datetime.datetime.now()
        prefix = config.get("snip_filename_prefix", "Ekran_Goruntusu")
        def_name = f"{prefix}_Combined_{now.strftime('%Y%m%d_%H%M%S')}.png"
        
        path = filedialog.asksaveasfilename(
            parent=self,
            title=t("combiner_save_dialog_title"),
            initialfile=def_name,
            defaultextension=".png",
            filetypes=[
                (f"{t('filetype_png')} (*.png)", "*.png"),
                (f"{t('filetype_jpg')} (*.jpg;*.jpeg)", "*.jpg;*.jpeg"),
                (f"{t('filetype_webp')} (*.webp)", "*.webp"),
                (f"{t('filetype_bmp')} (*.bmp)", "*.bmp")
            ]
        )
        if path:
            try:
                save_img = self.combined_cache
                if path.lower().endswith((".jpg", ".jpeg")):
                    save_img = save_img.convert("RGB")
                save_img.save(path)
                self._show_temp_status(f"✓ {t('status_saved')}: {os.path.basename(path)}")
            except Exception as e:
                messagebox.showerror(t("error_save_title"), t("error_save_detail").format(error=e), parent=self)

    def _on_open_in_editor_click(self):
        """Birleştirilmiş görseli çizim yapmak için Snipping Tool düzenleyicisinde açar."""
        if not self.combined_cache:
            self._show_temp_status(f"⚠ {t('combiner_no_images_editor')}")
            return

        if self.on_open_in_editor:
            self.on_open_in_editor(self.combined_cache.copy())
            self.destroy()

    def _on_google_lens(self):
        """Birleştirilmiş görseli doğrudan Google Lens'e yükleyerek arama yapar."""
        if not self.combined_cache:
            self._show_temp_status(f"⚠ {t('combiner_no_images_save')}")
            return

        self._show_temp_status(f"🔍 {t('status_uploading_lens')}")
        search_image_in_google_lens(self.combined_cache)

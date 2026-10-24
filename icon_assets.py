"""
Ekran Alıntısı Aracı - Windows 11 Fluent Yüksek Çözünürlüklü Vektör İkon Üreteci
===================================================================
Windows 11 Snipping Tool (Ekran Alıntısı Aracı) tasarımına birebir uyan,
kenar taşması yapmayan, pürüzsüz 4x supersampled ikonlar sağlar.
"""

import os
import io
import base64
import math
from PIL import Image, ImageDraw, ImageTk, ImageFilter
import customtkinter as ctk

_CTK_CACHE = {}

_GOOGLE_LENS_B64 = (
    "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"
)


def _draw_rect_shape(d, cx, cy, S, fg, w):
    d.rounded_rectangle([cx - 8*S, cy - 7*S, cx + 5*S, cy + 5*S], radius=2.5*S, outline=fg, width=w)
    d.rectangle([cx + 1*S, cy + 1*S, cx + 9*S, cy + 9*S], fill=(0, 0, 0, 0))
    px, py = cx + 5*S, cy + 5*S
    pw = 3.2*S
    d.line([(px - pw, py), (px + pw, py)], fill=fg, width=w)
    d.line([(px, py - pw), (px, py + pw)], fill=fg, width=w)


def _draw_window_shape(d, cx, cy, S, fg, w):
    d.rounded_rectangle([cx - 8*S, cy - 7*S, cx + 5*S, cy + 5*S], radius=2.5*S, outline=fg, width=w)
    d.line([(cx - 8*S, cy - 3*S), (cx + 5*S, cy - 3*S)], fill=fg, width=int(1.3*S))
    d.rectangle([cx + 1*S, cy + 1*S, cx + 9*S, cy + 9*S], fill=(0, 0, 0, 0))
    px, py = cx + 5*S, cy + 5*S
    pw = 3.2*S
    d.line([(px - pw, py), (px + pw, py)], fill=fg, width=w)
    d.line([(px, py - pw), (px, py + pw)], fill=fg, width=w)


def _draw_fullscreen_shape(d, cx, cy, S, fg, w):
    L = 4.5*S
    x1, y1, x2, y2 = cx - 7.5*S, cy - 6.5*S, cx + 5.5*S, cy + 5.5*S
    d.line([(x1, y1 + L), (x1, y1), (x1 + L, y1)], fill=fg, width=w)
    d.line([(x2 - L, y1), (x2, y1), (x2, y1 + L)], fill=fg, width=w)
    d.line([(x1, y2 - L), (x1, y2), (x1 + L, y2)], fill=fg, width=w)
    d.line([(x2 - L, y2), (x2, y2), (x2, y2 - L)], fill=fg, width=w)


def _draw_freeform_shape(d, cx, cy, S, fg, w):
    pts = []
    cx1, cy1, r1 = cx - 3*S, cy - 2*S, 4.2*S
    for a in range(120, 280, 10):
        rad = math.radians(a)
        pts.append((cx1 + r1*math.cos(rad), cy1 + r1*math.sin(rad)))
    cx2, cy2, r2 = cx + 2*S, cy - 3*S, 3.8*S
    for a in range(260, 420, 10):
        rad = math.radians(a)
        pts.append((cx2 + r2*math.cos(rad), cy2 + r2*math.sin(rad)))
    cx3, cy3, r3 = cx + 1*S, cy + 2*S, 3.2*S
    for a in range(0, 90, 10):
        rad = math.radians(a)
        pts.append((cx3 + r3*math.cos(rad), cy3 + r3*math.sin(rad)))
    cx4, cy4, r4 = cx - 3*S, cy + 2*S, 3.6*S
    for a in range(90, 140, 10):
        rad = math.radians(a)
        pts.append((cx4 + r4*math.cos(rad), cy4 + r4*math.sin(rad)))
    pts.append(pts[0])
    d.line(pts, fill=fg, width=w, joint="curve")
    d.rectangle([cx + 1*S, cy + 1*S, cx + 9*S, cy + 9*S], fill=(0, 0, 0, 0))
    px, py = cx + 5*S, cy + 5*S
    pw = 3.2*S
    d.line([(px - pw, py), (px + pw, py)], fill=fg, width=w)
    d.line([(px, py - pw), (px, py + pw)], fill=fg, width=w)


def _draw_delay_slash_shape(d, cx, cy, S, fg, w):
    r = 6.2*S
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=fg, width=w)
    d.line([(cx, cy - r - 2.5*S), (cx, cy - r)], fill=fg, width=w)
    d.line([(cx - 2*S, cy - r - 2.5*S), (cx + 2*S, cy - r - 2.5*S)], fill=fg, width=w)
    d.line([(cx, cy), (cx, cy - 3.8*S)], fill=fg, width=w)
    d.line([(cx - 7*S, cy + 6.5*S), (cx + 7*S, cy - 6.5*S)], fill=fg, width=int(1.6*S))


def _draw_delay_timer_shape(d, cx, cy, S, fg, w):
    r = 6.2*S
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=fg, width=w)
    d.line([(cx, cy - r - 2.5*S), (cx, cy - r)], fill=fg, width=w)
    d.line([(cx - 2*S, cy - r - 2.5*S), (cx + 2*S, cy - r - 2.5*S)], fill=fg, width=w)
    d.line([(cx, cy), (cx, cy - 3.8*S)], fill=fg, width=w)
    d.line([(cx, cy), (cx + 3.2*S, cy)], fill=fg, width=w)


# =============================================================================
# 1. SEGMENTED KAMERA / VİDEO İKONLARI (ALT MAVİ ÇUBUKLU)
# =============================================================================
def get_seg_icon(seg_type: str, active: bool = False) -> ctk.CTkImage:
    key = ("seg", seg_type, active)
    if key in _CTK_CACHE:
        return _CTK_CACHE[key]

    S = 4
    W = 36 * S
    H = 30 * S
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fg = (245, 245, 245, 255) if active else (185, 185, 185, 255)
    cx, cy = 18*S, 12*S
    w = int(1.6*S)

    if seg_type == "camera":
        d.rounded_rectangle([cx - 8.5*S, cy - 5*S, cx + 8.5*S, cy + 7*S], radius=2.5*S, outline=fg, width=w)
        d.polygon([(cx - 4*S, cy - 5*S), (cx - 2.5*S, cy - 7.5*S), (cx + 2.5*S, cy - 7.5*S), (cx + 4*S, cy - 5*S)], outline=fg)
        d.line([(cx - 2.5*S, cy - 7.5*S), (cx + 2.5*S, cy - 7.5*S)], fill=fg, width=w)
        d.ellipse([cx - 3.8*S, cy - 2.5*S, cx + 3.8*S, cy + 4.5*S], outline=fg, width=w)
    else:  # video
        d.rounded_rectangle([cx - 8.5*S, cy - 6*S, cx + 3.5*S, cy + 6*S], radius=2.2*S, outline=fg, width=w)
        d.polygon([(cx + 4*S, cy - 2.5*S), (cx + 8.5*S, cy - 6*S), (cx + 8.5*S, cy + 6*S), (cx + 4*S, cy + 2.5*S)], outline=fg)
        d.line([(cx + 4*S, cy - 2.5*S), (cx + 8.5*S, cy - 6*S)], fill=fg, width=w)
        d.line([(cx + 8.5*S, cy - 6*S), (cx + 8.5*S, cy + 6*S)], fill=fg, width=w)
        d.line([(cx + 8.5*S, cy + 6*S), (cx + 4*S, cy + 2.5*S)], fill=fg, width=w)

    if active:
        # Screenshot 1'deki alt mavi Fluent gösterge çubuğu
        d.rounded_rectangle([cx - 7*S, 24*S, cx + 7*S, 26.5*S], radius=1.5*S, fill=(96, 205, 255, 255))

    res = im.resize((36, 30), Image.Resampling.LANCZOS)
    ctk_img = ctk.CTkImage(light_image=res, dark_image=res, size=(36, 30))
    _CTK_CACHE[key] = ctk_img
    return ctk_img


get_tab_icon = get_seg_icon


# =============================================================================
# 2. ARAÇ ÇUBUĞU İKON + AŞAĞI OK BİRLEŞİK İKONLARI (SCREENSHOT 1)
# =============================================================================
def get_combo_icon(mode_name: str) -> ctk.CTkImage:
    """Kırpma modu ikonu ile yanındaki aşağı oku tek pürüzsüz görselde birleştirir."""
    key = ("combo_mode", mode_name)
    if key in _CTK_CACHE:
        return _CTK_CACHE[key]

    S = 4
    W = 34 * S
    H = 24 * S
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fg = (245, 245, 245, 255)
    cx, cy = 11*S, 12*S
    w = int(1.6*S)

    if mode_name == "rect":
        _draw_rect_shape(d, cx, cy, S, fg, w)
    elif mode_name == "window":
        _draw_window_shape(d, cx, cy, S, fg, w)
    elif mode_name == "fullscreen":
        _draw_fullscreen_shape(d, cx, cy, S, fg, w)
    elif mode_name == "freeform":
        _draw_freeform_shape(d, cx, cy, S, fg, w)

    # Aşağı Ok (Chevron)
    cw = int(1.5*S)
    d.line([(24*S, 10*S), (27.5*S, 13.5*S), (31*S, 10*S)], fill=(190, 190, 190, 255), width=cw)

    res = im.resize((34, 24), Image.Resampling.LANCZOS)
    ctk_img = ctk.CTkImage(light_image=res, dark_image=res, size=(34, 24))
    _CTK_CACHE[key] = ctk_img
    return ctk_img


def get_delay_combo_icon(delay_sec: int) -> ctk.CTkImage:
    """Zamanlayıcı ikonu ile aşağı oku tek pürüzsüz görselde birleştirir."""
    key = ("combo_delay", delay_sec)
    if key in _CTK_CACHE:
        return _CTK_CACHE[key]

    S = 4
    W = 34 * S
    H = 24 * S
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fg = (245, 245, 245, 255)
    cx, cy = 11*S, 12.5*S
    w = int(1.6*S)

    if delay_sec == 0:
        _draw_delay_slash_shape(d, cx, cy, S, fg, w)
    else:
        _draw_delay_timer_shape(d, cx, cy, S, fg, w)

    cw = int(1.5*S)
    d.line([(24*S, 10*S), (27.5*S, 13.5*S), (31*S, 10*S)], fill=(190, 190, 190, 255), width=cw)

    res = im.resize((34, 24), Image.Resampling.LANCZOS)
    ctk_img = ctk.CTkImage(light_image=res, dark_image=res, size=(34, 24))
    _CTK_CACHE[key] = ctk_img
    return ctk_img


# =============================================================================
# 3. AÇILIR MENÜ İKONLARI (SCREENSHOT 2 BİREBİR SOL MAVİ ÇUBUKLU)
# =============================================================================
def get_menu_icon(mode_name: str, active: bool = False) -> ctk.CTkImage:
    """Açılır menü satırı için solunda dikey mavi çizgi içeren veya hizalı ikon döndürür."""
    key = ("menu", mode_name, active)
    if key in _CTK_CACHE:
        return _CTK_CACHE[key]

    S = 4
    W = 34 * S
    H = 26 * S
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fg = (245, 245, 245, 255)

    if active:
        # Screenshot 2'deki sol dikey mavi Fluent çizgisi
        d.rounded_rectangle([1.5*S, 4*S, 4.5*S, 22*S], radius=1.5*S, fill=(96, 205, 255, 255))

    cx, cy = 19*S, 13*S
    w = int(1.6*S)

    if mode_name == "rect":
        _draw_rect_shape(d, cx, cy, S, fg, w)
    elif mode_name == "window":
        _draw_window_shape(d, cx, cy, S, fg, w)
    elif mode_name == "fullscreen":
        _draw_fullscreen_shape(d, cx, cy, S, fg, w)
    elif mode_name == "freeform":
        _draw_freeform_shape(d, cx, cy, S, fg, w)

    res = im.resize((34, 26), Image.Resampling.LANCZOS)
    ctk_img = ctk.CTkImage(light_image=res, dark_image=res, size=(34, 26))
    _CTK_CACHE[key] = ctk_img
    return ctk_img


def get_delay_menu_icon(sec: int, active: bool = False) -> ctk.CTkImage:
    key = ("menu_delay", sec, active)
    if key in _CTK_CACHE:
        return _CTK_CACHE[key]

    S = 4
    W = 34 * S
    H = 26 * S
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fg = (245, 245, 245, 255)

    if active:
        d.rounded_rectangle([1.5*S, 4*S, 4.5*S, 22*S], radius=1.5*S, fill=(96, 205, 255, 255))

    cx, cy = 19*S, 13*S
    w = int(1.6*S)

    if sec == 0:
        _draw_delay_slash_shape(d, cx, cy, S, fg, w)
    else:
        _draw_delay_timer_shape(d, cx, cy, S, fg, w)

    res = im.resize((34, 26), Image.Resampling.LANCZOS)
    ctk_img = ctk.CTkImage(light_image=res, dark_image=res, size=(34, 26))
    _CTK_CACHE[key] = ctk_img
    return ctk_img


# =============================================================================
# 4. TEKİL İKONLAR (OCR, GOOGLE LENS, KALEM, VURGULAYICI, SİLGİ VB.)
# =============================================================================
def get_icon_ctk(name: str, size: tuple[int, int] = (22, 22)) -> ctk.CTkImage:
    key = ("single", name, size[0], size[1])
    if key in _CTK_CACHE:
        return _CTK_CACHE[key]

    if name == "google_lens":
        lens_img = None
        asset_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "google_lens.png")
        if os.path.exists(asset_file):
            try:
                lens_img = Image.open(asset_file).convert("RGBA")
            except Exception:
                pass
        if lens_img is None:
            try:
                lens_bytes = base64.b64decode(_GOOGLE_LENS_B64)
                lens_img = Image.open(io.BytesIO(lens_bytes)).convert("RGBA")
            except Exception:
                pass
        if lens_img:
            res = lens_img.resize(size, Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=res, dark_image=res, size=size)
            _CTK_CACHE[key] = ctk_img
            return ctk_img

    S = 4
    W = 28 * S
    H = 28 * S
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fg = (245, 245, 245, 255)
    cx, cy = 14*S, 14*S
    w = int(1.6*S)

    if name == "rect":
        rw = 8.5 * S
        rh = 6.5 * S
        d.rounded_rectangle([cx - rw, cy - rh, cx + rw, cy + rh], radius=2*S, outline=fg, width=w)

    elif name == "window":
        rw = 8.5 * S
        rh = 6.5 * S
        d.rounded_rectangle([cx - rw, cy - rh, cx + rw, cy + rh], radius=2*S, outline=fg, width=w)
        d.line([(cx - rw, cy - 2.5*S), (cx + rw, cy - 2.5*S)], fill=fg, width=w)
        d.line([(cx - rw + 2.5*S, cy - 4.5*S), (cx - rw + 3.5*S, cy - 4.5*S)], fill=fg, width=w)

    elif name == "fullscreen":
        mw = 8.5 * S
        d.rounded_rectangle([cx - mw, cy - 7*S, cx + mw, cy + 3*S], radius=2*S, outline=fg, width=w)
        d.line([(cx, cy + 3*S), (cx, cy + 7*S)], fill=fg, width=w)
        d.line([(cx - 4.5*S, cy + 7*S), (cx + 4.5*S, cy + 7*S)], fill=fg, width=w)

    elif name == "freeform":
        pts = []
        cx1, cy1, r1 = cx - 3.5*S, cy - 2.5*S, 4.5*S
        for a in range(120, 280, 10):
            rad = math.radians(a)
            pts.append((cx1 + r1*math.cos(rad), cy1 + r1*math.sin(rad)))
        cx2, cy2, r2 = cx + 2.5*S, cy - 3.5*S, 4.0*S
        for a in range(260, 420, 10):
            rad = math.radians(a)
            pts.append((cx2 + r2*math.cos(rad), cy2 + r2*math.sin(rad)))
        cx3, cy3, r3 = cx + 2.0*S, cy + 2.5*S, 4.0*S
        for a in range(0, 90, 10):
            rad = math.radians(a)
            pts.append((cx3 + r3*math.cos(rad), cy3 + r3*math.sin(rad)))
        cx4, cy4, r4 = cx - 3.5*S, cy + 2.5*S, 4.2*S
        for a in range(90, 140, 10):
            rad = math.radians(a)
            pts.append((cx4 + r4*math.cos(rad), cy4 + r4*math.sin(rad)))
        pts.append(pts[0])
        d.line(pts, fill=fg, width=w, joint="curve")

    elif name == "ocr":
        # Screenshot 1'deki OCR / Tarayıcı simgesi
        x1, y1, x2, y2 = 4*S, 5*S, 24*S, 23*S
        c_len = 4*S
        d.line([(x1, y1 + c_len), (x1, y1), (x1 + c_len, y1)], fill=fg, width=w)
        d.line([(x2 - c_len, y1), (x2, y1), (x2, y1 + c_len)], fill=fg, width=w)
        d.line([(x1, y2 - c_len), (x1, y2), (x1 + c_len, y2)], fill=fg, width=w)
        d.line([(x2 - c_len, y2), (x2, y2), (x2, y2 - c_len)], fill=fg, width=w)
        d.line([(8*S, 11*S), (20*S, 11*S)], fill=fg, width=w)
        d.line([(8*S, 16*S), (18*S, 16*S)], fill=fg, width=w)

    elif name == "dots":
        # Üç nokta (...)
        r = 1.6*S
        d.ellipse([7*S - r, cy - r, 7*S + r, cy + r], fill=fg)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fg)
        d.ellipse([21*S - r, cy - r, 21*S + r, cy + r], fill=fg)

    elif name == "pen":
        d.line([(19*S, 5*S), (23*S, 9*S)], fill=fg, width=w)
        d.line([(23*S, 9*S), (10*S, 22*S)], fill=fg, width=w)
        d.line([(10*S, 22*S), (5*S, 23*S)], fill=fg, width=w)
        d.line([(5*S, 23*S), (6*S, 18*S)], fill=fg, width=w)
        d.line([(6*S, 18*S), (19*S, 5*S)], fill=fg, width=w)
        d.line([(9*S, 19*S), (19*S, 9*S)], fill=fg, width=w)

    elif name == "highlighter":
        hl = (255, 235, 59, 255)
        d.line([(19*S, 5*S), (23*S, 9*S)], fill=hl, width=w)
        d.line([(23*S, 9*S), (13*S, 19*S)], fill=hl, width=w)
        d.line([(13*S, 19*S), (9*S, 15*S)], fill=hl, width=w)
        d.line([(9*S, 15*S), (19*S, 5*S)], fill=hl, width=w)
        d.polygon([(9*S, 15*S), (13*S, 19*S), (7*S, 23*S), (5*S, 21*S)], fill=hl)

    elif name == "eraser":
        d.line([(13*S, 6*S), (22*S, 15*S)], fill=fg, width=w)
        d.line([(22*S, 15*S), (15*S, 22*S)], fill=fg, width=w)
        d.line([(15*S, 22*S), (6*S, 13*S)], fill=fg, width=w)
        d.line([(6*S, 13*S), (13*S, 6*S)], fill=fg, width=w)
        d.line([(10*S, 9*S), (18*S, 17*S)], fill=fg, width=w)

    elif name == "undo":
        d.arc([7*S, 7*S, 21*S, 21*S], 200, 380, fill=fg, width=w)
        d.polygon([(5*S, 14*S), (10*S, 10*S), (10*S, 18*S)], fill=fg)

    elif name == "copy":
        d.rounded_rectangle([9*S, 5*S, 22*S, 18*S], radius=2*S, outline=fg, width=w)
        d.rectangle([5*S, 9*S, 18*S, 22*S], fill=(0, 0, 0, 0))
        d.rounded_rectangle([6*S, 9*S, 19*S, 23*S], radius=2*S, outline=fg, width=w)

    elif name == "save":
        d.rounded_rectangle([5*S, 5*S, 23*S, 23*S], radius=2*S, outline=fg, width=w)
        d.rectangle([8*S, 5*S, 20*S, 11*S], outline=fg, width=w)
        d.rectangle([8*S, 15*S, 20*S, 23*S], outline=fg, width=w)

    elif name == "arrow_left":
        d.line([(18*S, 6*S), (8*S, 14*S), (18*S, 22*S)], fill=fg, width=int(1.8*S))
        d.line([(8*S, 14*S), (23*S, 14*S)], fill=fg, width=int(1.8*S))

    elif name == "mic":
        d.rounded_rectangle([11*S, 5*S, 17*S, 15*S], radius=3*S, outline=fg, width=w)
        d.arc([8*S, 10*S, 20*S, 18*S], 0, 180, fill=fg, width=w)
        d.line([(14*S, 18*S), (14*S, 23*S)], fill=fg, width=w)
        d.line([(10*S, 23*S), (18*S, 23*S)], fill=fg, width=w)

    elif name == "mic_off":
        d.rounded_rectangle([11*S, 5*S, 17*S, 15*S], radius=3*S, outline=(150, 150, 150, 255), width=w)
        d.arc([8*S, 10*S, 20*S, 18*S], 0, 180, fill=(150, 150, 150, 255), width=w)
        d.line([(14*S, 18*S), (14*S, 23*S)], fill=(150, 150, 150, 255), width=w)
        d.line([(10*S, 23*S), (18*S, 23*S)], fill=(150, 150, 150, 255), width=w)
        d.line([(7*S, 7*S), (21*S, 21*S)], fill=(232, 17, 35, 255), width=int(2*S))

    elif name == "speaker":
        d.line([(6*S, 11*S), (10*S, 11*S), (15*S, 7*S), (15*S, 21*S), (10*S, 17*S), (6*S, 17*S), (6*S, 11*S)], fill=fg, width=w)
        d.arc([14*S, 10*S, 20*S, 18*S], -60, 60, fill=fg, width=w)
        d.arc([16*S, 7*S, 24*S, 21*S], -60, 60, fill=fg, width=w)

    elif name == "speaker_off":
        d.line([(6*S, 11*S), (10*S, 11*S), (15*S, 7*S), (15*S, 21*S), (10*S, 17*S), (6*S, 17*S), (6*S, 11*S)], fill=(150, 150, 150, 255), width=w)
        d.line([(7*S, 7*S), (21*S, 21*S)], fill=(232, 17, 35, 255), width=int(2*S))

    elif name == "combine":
        d.rounded_rectangle([cx - 8.5*S, cy - 8*S, cx - 1*S, cy + 8*S], radius=1.5*S, outline=fg, width=w)
        d.rounded_rectangle([cx + 1*S, cy - 8*S, cx + 8.5*S, cy - 1*S], radius=1.5*S, outline=fg, width=w)
        d.rounded_rectangle([cx + 1*S, cy + 1*S, cx + 8.5*S, cy + 8*S], radius=1.5*S, outline=fg, width=w)

    elif name == "plus":
        d.line([(cx - 6*S, cy), (cx + 6*S, cy)], fill=fg, width=w)
        d.line([(cx, cy - 6*S), (cx, cy + 6*S)], fill=fg, width=w)

    elif name == "trash":
        d.line([(cx - 6*S, cy - 6*S), (cx + 6*S, cy - 6*S)], fill=fg, width=w)
        d.line([(cx - 2.5*S, cy - 8*S), (cx + 2.5*S, cy - 8*S)], fill=fg, width=w)
        d.line([(cx - 5*S, cy - 5*S), (cx - 4*S, cy + 7*S), (cx + 4*S, cy + 7*S), (cx + 5*S, cy - 5*S)], fill=fg, width=w)
        d.line([(cx - 1.8*S, cy - 3*S), (cx - 1.8*S, cy + 5*S)], fill=fg, width=int(1.2*S))
        d.line([(cx + 1.8*S, cy - 3*S), (cx + 1.8*S, cy + 5*S)], fill=fg, width=int(1.2*S))

    elif name == "up":
        d.line([(cx - 5*S, cy + 2*S), (cx, cy - 4*S), (cx + 5*S, cy + 2*S)], fill=fg, width=int(1.8*S))

    elif name == "down":
        d.line([(cx - 5*S, cy - 2*S), (cx, cy + 4*S), (cx + 5*S, cy - 2*S)], fill=fg, width=int(1.8*S))

    elif name == "grid":
        d.rounded_rectangle([cx - 7.5*S, cy - 7.5*S, cx - 1*S, cy - 1*S], radius=1*S, outline=fg, width=w)
        d.rounded_rectangle([cx + 1*S, cy - 7.5*S, cx + 7.5*S, cy - 1*S], radius=1*S, outline=fg, width=w)
        d.rounded_rectangle([cx - 7.5*S, cy + 1*S, cx - 1*S, cy + 7.5*S], radius=1*S, outline=fg, width=w)
        d.rounded_rectangle([cx + 1*S, cy + 1*S, cx + 7.5*S, cy + 7.5*S], radius=1*S, outline=fg, width=w)

    elif name == "vertical":
        d.rounded_rectangle([cx - 7*S, cy - 8*S, cx + 7*S, cy - 1*S], radius=1.5*S, outline=fg, width=w)
        d.rounded_rectangle([cx - 7*S, cy + 1*S, cx + 7*S, cy + 8*S], radius=1.5*S, outline=fg, width=w)

    elif name == "horizontal":
        d.rounded_rectangle([cx - 8*S, cy - 7*S, cx - 1*S, cy + 7*S], radius=1.5*S, outline=fg, width=w)
        d.rounded_rectangle([cx + 1*S, cy - 7*S, cx + 8*S, cy + 7*S], radius=1.5*S, outline=fg, width=w)

    elif name == "windows":
        w_tile = 5.2 * S
        gap = 1.2 * S
        d.rounded_rectangle([cx - gap - w_tile, cy - gap - w_tile, cx - gap, cy - gap], radius=1*S, fill=fg)
        d.rounded_rectangle([cx + gap, cy - gap - w_tile, cx + gap + w_tile, cy - gap], radius=1*S, fill=fg)
        d.rounded_rectangle([cx - gap - w_tile, cy + gap, cx - gap, cy + gap + w_tile], radius=1*S, fill=fg)
        d.rounded_rectangle([cx + gap, cy + gap, cx + gap + w_tile, cy + gap + w_tile], radius=1*S, fill=fg)

    elif name == "close":
        d.line([(cx - 4.5*S, cy - 4.5*S), (cx + 4.5*S, cy + 4.5*S)], fill=fg, width=w)
        d.line([(cx + 4.5*S, cy - 4.5*S), (cx - 4.5*S, cy + 4.5*S)], fill=fg, width=w)

    elif name == "code":
        d.line([(cx - 7.5*S, cy), (cx - 3.5*S, cy - 4.5*S)], fill=fg, width=w)
        d.line([(cx - 7.5*S, cy), (cx - 3.5*S, cy + 4.5*S)], fill=fg, width=w)
        d.line([(cx - 1*S, cy + 6.5*S), (cx + 1*S, cy - 6.5*S)], fill=fg, width=w)
        d.line([(cx + 7.5*S, cy), (cx + 3.5*S, cy - 4.5*S)], fill=fg, width=w)
        d.line([(cx + 7.5*S, cy), (cx + 3.5*S, cy + 4.5*S)], fill=fg, width=w)

    elif name == "format":
        d.line([(cx - 7*S, cy - 5*S), (cx + 7*S, cy - 5*S)], fill=fg, width=w)
        d.line([(cx - 2*S, cy), (cx + 7*S, cy)], fill=fg, width=w)
        d.line([(cx - 2*S, cy + 5*S), (cx + 7*S, cy + 5*S)], fill=fg, width=w)
        d.line([(cx - 6.5*S, cy - 1*S), (cx - 4.5*S, cy + 2.5*S), (cx - 6.5*S, cy + 6*S)], fill=fg, width=w)


    res = im.resize(size, Image.Resampling.LANCZOS)
    ctk_img = ctk.CTkImage(light_image=res, dark_image=res, size=size)
    _CTK_CACHE[key] = ctk_img
    return ctk_img


def create_app_icon_image(size=256) -> Image.Image:
    """Windows 11 Snipping Tool koyu zemin ve makaslı orijinal uygulama ikonunu üretir."""
    # Pürüzsüz kenarlar için 4x supersampling ile çizilip hedeflenen boyuta indirilir
    supersample = 4
    canvas_size = size * supersample
    S = canvas_size / 32.0

    im = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    # 1. Koyu arka plan ve açık mavi/camgöbeği kenarlık
    d.rounded_rectangle(
        [6*S, 4*S, 28*S, 26*S],
        radius=5*S,
        fill=(38, 38, 38, 255),
        outline=(96, 205, 255, 255),
        width=max(1, int(2.2*S))
    )
    # 2. Kırmızı makas sapı halkası
    d.ellipse(
        [4*S, 18*S, 13*S, 27*S],
        outline=(255, 90, 95, 255),
        width=max(1, int(2.2*S))
    )
    # 3. Mavi makas sapı halkası
    d.ellipse(
        [12*S, 20*S, 21*S, 29*S],
        outline=(96, 205, 255, 255),
        width=max(1, int(2.2*S))
    )
    # 4. Makas bıçakları
    d.line(
        [(9*S, 20*S), (24*S, 7*S)],
        fill=(235, 235, 235, 255),
        width=max(1, int(2.2*S))
    )
    d.line(
        [(16*S, 21*S), (9*S, 10*S)],
        fill=(235, 235, 235, 255),
        width=max(1, int(2.2*S))
    )
    # 5. Makas vidası (beyaz nokta)
    d.ellipse(
        [12*S, 15*S, 14*S, 17*S],
        fill=(255, 255, 255, 255)
    )

    return im.resize((size, size), Image.Resampling.LANCZOS)


_APP_ICON_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAfQAAAH0CAYAAADL1t+KAAAAtGVYSWZJSSoACAAAAAYAEgEDAAEAAAAB"
    "AAAAGgEFAAEAAABWAAAAGwEFAAEAAABeAAAAKAEDAAEAAAACAAAAEwIDAAEAAAABAAAAaYcEAAEAAABm"
    "AAAAAAAAAGAAAAABAAAAYAAAAAEAAAAGAACQBwAEAAAAMDIxMAGRBwAEAAAAAQIDAACgBwAEAAAAMDEw"
    "MAGgAwABAAAA//8AAAKgBAABAAAA9AEAAAOgBAABAAAA9AEAAAAAAAAA4cNEAAAACXBIWXMAAA7EAAAO"
    "xAGVKw4bAAAFTWlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSfvu78nIGlk"
    "PSdXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQnPz4KPHg6eG1wbWV0YSB4bWxuczp4PSdhZG9iZTpuczpt"
    "ZXRhLyc+CjxyZGY6UkRGIHhtbG5zOnJkZj0naHR0cDovL3d3dy53My5vcmcvMTk5OS8wMi8yMi1yZGYt"
    "c3ludGF4LW5zIyc+CgogPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9JycKICB4bWxuczpBdHRyaWI9"
    "J2h0dHA6Ly9ucy5hdHRyaWJ1dGlvbi5jb20vYWRzLzEuMC8nPgogIDxBdHRyaWI6QWRzPgogICA8cmRm"
    "OlNlcT4KICAgIDxyZGY6bGkgcmRmOnBhcnNlVHlwZT0nUmVzb3VyY2UnPgogICAgIDxBdHRyaWI6Q3Jl"
    "YXRlZD4yMDI2LTEwLTE5PC9BdHRyaWI6Q3JlYXRlZD4KICAgICA8QXR0cmliOkRhdGE+eyZxdW90O2Rv"
    "YyZxdW90OzomcXVvdDtEQUhZYlFYOEdWSSZxdW90OywmcXVvdDt1c2VyJnF1b3Q7OiZxdW90O1VBRmNN"
    "Mzd1T09RJnF1b3Q7LCZxdW90O2JyYW5kJnF1b3Q7OiZxdW90O0NhbnZhIFBSTyBTxLFuxLFmxLEmcXVv"
    "dDt9PC9BdHRyaWI6RGF0YT4KICAgICA8QXR0cmliOkV4dElkPjZjZTExNGNiLWEwMDEtNDI5My1hNGRk"
    "LWI3YTViNjVjODBhMjwvQXR0cmliOkV4dElkPgogICAgIDxBdHRyaWI6RmJJZD41MjUyNjU5MTQxNzk1"
    "ODA8L0F0dHJpYjpGYklkPgogICAgIDxBdHRyaWI6VG91Y2hUeXBlPjI8L0F0dHJpYjpUb3VjaFR5cGU+"
    "CiAgICA8L3JkZjpsaT4KICAgPC9yZGY6U2VxPgogIDwvQXR0cmliOkFkcz4KIDwvcmRmOkRlc2NyaXB0"
    "aW9uPgoKIDxyZGY6RGVzY3JpcHRpb24gcmRmOmFib3V0PScnCiAgeG1sbnM6ZGM9J2h0dHA6Ly9wdXJs"
    "Lm9yZy9kYy9lbGVtZW50cy8xLjEvJz4KICA8ZGM6dGl0bGU+CiAgIDxyZGY6QWx0PgogICAgPHJkZjps"
    "aSB4bWw6bGFuZz0neC1kZWZhdWx0Jz5BZHPEsXogdGFzYXLEsW0gLSAxPC9yZGY6bGk+CiAgIDwvcmRm"
    "OkFsdD4KICA8L2RjOnRpdGxlPgogPC9yZGY6RGVzY3JpcHRpb24+CgogPHJkZjpEZXNjcmlwdGlvbiBy"
    "ZGY6YWJvdXQ9JycKICB4bWxuczpwZGY9J2h0dHA6Ly9ucy5hZG9iZS5jb20vcGRmLzEuMy8nPgogIDxw"
    "ZGY6QXV0aG9yPk1lcmnDpzwvcGRmOkF1dGhvcj4KIDwvcmRmOkRlc2NyaXB0aW9uPgoKIDxyZGY6RGVz"
    "Y3JpcHRpb24gcmRmOmFib3V0PScnCiAgeG1sbnM6eG1wPSdodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8x"
    "LjAvJz4KICA8eG1wOkNyZWF0b3JUb29sPkNhbnZhIGRvYz1EQUhZYlFYOEdWSSB1c2VyPVVBRmNNMzd1"
    "T09RIGJyYW5kPUNhbnZhIFBSTyBTxLFuxLFmxLE8L3htcDpDcmVhdG9yVG9vbD4KIDwvcmRmOkRlc2Ny"
    "aXB0aW9uPgo8L3JkZjpSREY+CjwveDp4bXBtZXRhPgo8P3hwYWNrZXQgZW5kPSdyJz8+rQIZQQAAFfJJ"
    "REFUeJzt3XusdmlZ3/H5pykDJSBOqdVSFU2IpDQiYiNIPXAotcqpHVBRm8oZPNFWSiwzDEJT0bSiDIg9"
    "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"
)


def get_app_icon_image() -> Image.Image:
    """Ekran Alıntısı Aracı uygulama simgesini döndürür."""
    app_dir = os.path.dirname(os.path.abspath(__file__))
    png_path = os.path.join(app_dir, "assets", "app_icon.png")
    if os.path.exists(png_path):
        try:
            return Image.open(png_path).convert("RGBA")
        except Exception:
            pass
    try:
        raw = base64.b64decode(_APP_ICON_B64)
        return Image.open(io.BytesIO(raw)).convert("RGBA")
    except Exception:
        pass
    return create_app_icon_image(256)


def ensure_app_icon_ico() -> str:
    """Tüm standart boyutları (16, 20, 24, 32, 48, 64, 72, 96, 256) içeren app_icon.ico dosyasını üretir ve yolunu döndürür."""
    app_dir = os.path.dirname(os.path.abspath(__file__))
    ico_path = os.path.join(app_dir, "app_icon.ico")
    png_path = os.path.join(app_dir, "assets", "app_icon.png")

    needs_rebuild = not os.path.exists(ico_path) or os.path.getsize(ico_path) < 1000
    if not needs_rebuild and os.path.exists(png_path):
        if os.path.getmtime(png_path) > os.path.getmtime(ico_path):
            needs_rebuild = True

    if needs_rebuild:
        base_img = get_app_icon_image()
        sizes = [(16, 16), (20, 20), (24, 24), (32, 32), (48, 48), (64, 64), (72, 72), (96, 96), (256, 256)]
        base_img.save(ico_path, format="ICO", sizes=sizes)
    return ico_path



def setup_windows_app_id():
    """Windows görev çubuğunda python.exe yerine programın kendi ikonunun görünmesini sağlar."""
    if os.name == "nt":
        try:
            import ctypes
            myappid = "meric.ekranalintisi.snippingtool.1.0"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass


def apply_window_icon(window):
    """Pencereye hem Windows görev çubuğu hem de başlık çubuğu için özel ikonu bağlar."""
    try:
        ico_path = ensure_app_icon_ico()
        if os.path.exists(ico_path):
            window.iconbitmap(ico_path)
            # CustomTkinter'ın Windows'ta varsayılan mavi ikonu 200ms sonra tekrar ezmesini engelle
            if hasattr(window, "_windows_set_titlebar_icon"):
                window._windows_set_titlebar_icon = lambda: window.iconbitmap(ico_path)
    except Exception:
        pass

    try:
        photo = get_app_icon_photo((32, 32))
        window.iconphoto(True, photo)
    except Exception:
        pass


def get_app_icon_photo(size=(32, 32)) -> ImageTk.PhotoImage:
    """Pencere başlığı ve görev çubuğu için yüksek çözünürlüklü PhotoImage döndürür."""
    ensure_app_icon_ico()
    base_img = get_app_icon_image()
    resized = base_img.resize(size, Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(resized)

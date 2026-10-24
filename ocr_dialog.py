"""
Ekran Alıntısı Aracı - OCR Sonuç & Kod Görüntüleme Penceresi
===========================================================
Görselden ayıklanan metinleri ve kod bloklarını modern, sözdizimi vurgulamalı,
satır numaralı ve akıllı girintileme özellikli arayüzde sunar.
"""

import os
import re
import tkinter as tk
import customtkinter as ctk
from i18n import t
import icon_assets


# Anahtar kelimeler ve yerleşikler (Python, JS, C/C++, Java vb.)
CODE_KEYWORDS = {
    "def", "class", "return", "if", "elif", "else", "while", "for", "in",
    "try", "except", "finally", "with", "as", "lambda", "pass", "break",
    "continue", "yield", "raise", "async", "await", "import", "from",
    "global", "nonlocal", "assert", "del", "function", "var", "let", "const",
    "public", "private", "protected", "static", "void", "new", "this", "super",
    "interface", "extends", "implements", "package", "namespace", "using",
    "echo", "select", "from", "where", "insert", "update", "delete", "switch", "case"
}

CODE_BUILTINS = {
    "print", "input", "len", "range", "str", "int", "float", "list", "dict",
    "set", "tuple", "bool", "open", "type", "isinstance", "enumerate", "zip",
    "map", "filter", "sum", "min", "max", "True", "False", "None", "true",
    "false", "null", "undefined", "self", "cls"
}

SYNTAX_PATTERN = re.compile(
    r'(?P<COMMENT>#[^\n]*|//[^\n]*)'
    r'|(?P<STRING>f?\"\"\"[\s\S]*?\"\"\"|f?\'\'\'[\s\S]*?\'\'\'|f?\"[^\"\n]*\"|f?\'[^\'\n]*\')'
    r'|(?P<NUMBER>\b\d+(?:\.\d+)?\b)'
    r'|(?P<WORD>\b[a-zA-Z_]\w*\b)'
)


def auto_indent_code(text: str) -> str:
    """
    OCR ile taranırken girintisi kaybolmuş kodları akıllı blok kurallarına göre düzenler.
    (İki nokta ':' ve süslü parantez '{' bloklarını analiz eder).
    """
    lines = text.splitlines()
    result = []
    level = 0
    indent_unit = "    "

    for line in lines:
        stripped = line.strip()
        if not stripped:
            result.append("")
            continue

        # Bloğu kapatan veya aynı seviyeye geri dönen ifadeler
        dedent_starts = ("elif ", "elif:", "else:", "except", "finally:", "case ", "default:")
        if any(stripped.startswith(k) for k in dedent_starts):
            cur_level = max(0, level - 1)
        elif stripped in ("}", "]", ")") or stripped.startswith("}"):
            level = max(0, level - 1)
            cur_level = level
        else:
            cur_level = level

        result.append((indent_unit * cur_level) + stripped)

        # Sonraki satırın girintisini artıracak durumlar
        if stripped.endswith(":") or stripped.endswith("{"):
            level = cur_level + 1
        elif stripped.endswith("}") and not (stripped.endswith(":") or stripped.endswith("{")):
            level = max(0, level - 1)

    return "\n".join(result)


def looks_like_code(text: str) -> bool:
    """Metnin bir kod parçacığı olup olmadığını tespit eder."""
    code_signals = [
        r'\bdef\s+\w+\s*\(',
        r'\bclass\s+\w+',
        r'\bprint\s*\(',
        r'\bimport\s+\w+',
        r'\bfor\s+\w+\s+in\b',
        r'\bif\s+.*:',
        r'#\s*.*',
        r'//\s*.*',
        r'\{\s*$',
        r'\}\s*$',
        r';\s*$'
    ]
    matches = 0
    for pat in code_signals:
        if re.search(pat, text, re.MULTILINE):
            matches += 1
            if matches >= 2:
                return True
    return False


class OcrResultDialog(ctk.CTkToplevel):
    """Gelişmiş OCR Metin & Kod Görüntüleyici Penceresi."""

    def __init__(self, parent, extracted_text: str):
        super().__init__(parent)
        self.raw_text = extracted_text or ""
        self.current_mode = "text"

        self.title(t("ocr_dialog_title"))
        self.geometry("680x530")
        self.minsize(520, 400)
        self.configure(fg_color="#1E1E1E")
        self.attributes("-topmost", True)

        # Pencere ikonunu hemen ve biraz gecikmeli olarak güvenle ayarla
        self._apply_icon()
        self.after(100, self._apply_icon)
        self.after(300, self._apply_icon)

        self._build_ui()

        # Kod gibi görünüyorsa otomatik olarak Kod Görünümüne geç
        if looks_like_code(self.raw_text):
            self.view_switch.set(t("ocr_view_code"))
            self._switch_mode("code")
        else:
            self.view_switch.set(t("ocr_view_text"))
            self._switch_mode("text")

    def _apply_icon(self):
        try:
            icon_assets.apply_window_icon(self)
        except Exception:
            pass

    def _build_ui(self):
        # 1. ÜST BAŞLIK BARI
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill=tk.X, padx=16, pady=(14, 6))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side=tk.LEFT)

        lbl_icon = ctk.CTkLabel(
            title_box, image=icon_assets.get_icon_ctk("ocr", (22, 22)), text=""
        )
        lbl_icon.pack(side=tk.LEFT, padx=(0, 8))

        self.lbl_title = ctk.CTkLabel(
            title_box, text=t("ocr_extracted_text"),
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color="#FFFFFF"
        )
        self.lbl_title.pack(side=tk.LEFT)

        # Görünüm Değiştirici (Metin / Kod Görünümü)
        self.view_switch = ctk.CTkSegmentedButton(
            header,
            values=[t("ocr_view_text"), t("ocr_view_code")],
            command=self._on_segment_change,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            selected_color="#0078D4",
            selected_hover_color="#0063B1",
            unselected_color="#2B2B2B",
            unselected_hover_color="#363636",
            height=30
        )
        self.view_switch.pack(side=tk.RIGHT)

        # 2. ALT BİLGİ İPUCU
        self.lbl_hint = ctk.CTkLabel(
            self, text=t("ocr_auto_copied_hint"),
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#9E9E9E", anchor="w"
        )
        self.lbl_hint.pack(fill=tk.X, padx=16, pady=(0, 8))

        # 3. İÇERİK ALANI (CONTAINER)
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=2)

        # --- A. METİN GÖRÜNÜMÜ ---
        self.text_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.txt_box = ctk.CTkTextbox(
            self.text_frame,
            fg_color="#181818",
            border_width=1,
            border_color="#333333",
            corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#FFFFFF"
        )
        self.txt_box.pack(fill=tk.BOTH, expand=True)
        self.txt_box.insert("1.0", self.raw_text)

        # --- B. KOD GÖRÜNÜMÜ ---
        self.code_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")

        # Kod Alt Araç Çubuğu
        code_toolbar = ctk.CTkFrame(self.code_frame, fg_color="transparent", height=32)
        code_toolbar.pack(fill=tk.X, pady=(0, 6))

        self.btn_auto_indent = ctk.CTkButton(
            code_toolbar,
            image=icon_assets.get_icon_ctk("format", (14, 14)),
            text=f"  {t('ocr_format_code')}",
            compound="left",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color="#2D2D2D",
            hover_color="#3D3D3D",
            corner_radius=6,
            height=28,
            command=self._apply_auto_indent
        )
        self.btn_auto_indent.pack(side=tk.LEFT)

        self.lbl_code_badge = ctk.CTkLabel(
            code_toolbar,
            text=f"</>  {t('ocr_code_syntax_info')}",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#7A7A7A"
        )
        self.lbl_code_badge.pack(side=tk.RIGHT, padx=4)

        # Kod Editörü ve Satır Numaraları
        editor_container = ctk.CTkFrame(
            self.code_frame,
            fg_color="#141414",
            border_width=1,
            border_color="#333333",
            corner_radius=8
        )
        editor_container.pack(fill=tk.BOTH, expand=True)

        # Satır numaraları oluğu (Gutter)
        self.gutter = tk.Text(
            editor_container,
            width=4,
            padx=6,
            pady=6,
            takefocus=0,
            border=0,
            background="#181818",
            foreground="#6E7681",
            font=("Consolas", 11),
            state="disabled",
            cursor="arrow"
        )
        self.gutter.pack(side=tk.LEFT, fill=tk.Y)

        # Kod metin kutusu
        self.code_tb = ctk.CTkTextbox(
            editor_container,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#121212",
            text_color="#E6EDF3",
            corner_radius=0
        )
        self.code_tb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.code_tb.insert("1.0", self.raw_text)

        # Kaydırma ve senkronizasyon bağlama
        self._setup_code_editor_sync()

        # 4. ALT AKSİYON BARI
        bottom_bar = ctk.CTkFrame(self, fg_color="transparent")
        bottom_bar.pack(fill=tk.X, padx=16, pady=(12, 14))

        self.btn_copy = ctk.CTkButton(
            bottom_bar,
            image=icon_assets.get_icon_ctk("copy", (16, 16)),
            text=f"  {t('ocr_copy_all')}",
            compound="left",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#0078D4",
            hover_color="#0063B1",
            corner_radius=6,
            height=34,
            command=self._on_copy_clicked
        )
        self.btn_copy.pack(side=tk.LEFT)

        self.btn_close_dlg = ctk.CTkButton(
            bottom_bar,
            image=icon_assets.get_icon_ctk("close", (14, 14)),
            text=f"  {t('btn_close')}",
            compound="left",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="#2B2B2B",
            hover_color="#383838",
            corner_radius=6,
            height=34,
            width=90,
            command=self.destroy
        )
        self.btn_close_dlg.pack(side=tk.RIGHT)

    def _setup_code_editor_sync(self):
        """Satır numaraları ile kod metin kutusunu senkronize eder ve sözdizimi etiketlerini tanımlar."""
        raw_text_widget = self.code_tb._textbox

        # Sözdizimi etiket renkleri (VS Code Dark Modern teması)
        raw_text_widget.tag_configure("kw", foreground="#569CD6")        # Mavi (Keywords)
        raw_text_widget.tag_configure("builtin", foreground="#4EC9B0")   # Turkuaz (Builtins/Types)
        raw_text_widget.tag_configure("str", foreground="#CE9178")       # Somon/Turuncu (Strings)
        raw_text_widget.tag_configure("comment", foreground="#6A9955")   # Yeşil (Comments)
        raw_text_widget.tag_configure("num", foreground="#B5CEA8")       # Açık yeşil (Numbers)

        def _on_scroll(*args):
            try:
                self.gutter.yview_moveto(args[0])
            except Exception:
                pass
            try:
                self.code_tb._v_scroll_bar.set(*args)
            except Exception:
                pass

        raw_text_widget.configure(yscrollcommand=_on_scroll)

        # Fare tekerleği oluğun üzerindeyken kod penceresini kaydır
        self.gutter.bind(
            "<MouseWheel>",
            lambda e: (raw_text_widget.yview_scroll(int(-1 * (e.delta / 120)), "units"), "break")
        )

        # Klavye veya metin değişikliklerinde güncelle
        self.code_tb.bind("<KeyRelease>", lambda e: self._refresh_code_view())

    def _refresh_code_view(self):
        """Satır numaralarını ve sözdizimi renklendirmesini günceller."""
        content = self.code_tb.get("1.0", "end-1c")
        lines = content.split("\n")
        total_lines = len(lines)

        # 1. Satır numaralarını güncelle
        gutter_text = "\n".join(str(i) for i in range(1, total_lines + 1))
        self.gutter.configure(state="normal")
        self.gutter.delete("1.0", tk.END)
        self.gutter.insert("1.0", gutter_text)
        self.gutter.configure(state="disabled")

        # 2. Sözdizimi etiketlerini uygula
        raw_text_widget = self.code_tb._textbox
        for tag in ("kw", "builtin", "str", "comment", "num"):
            raw_text_widget.tag_remove(tag, "1.0", tk.END)

        for line_idx, line in enumerate(lines, start=1):
            for m in SYNTAX_PATTERN.finditer(line):
                kind = m.lastgroup
                s, e = m.span()
                idx1 = f"{line_idx}.{s}"
                idx2 = f"{line_idx}.{e}"

                if kind == "COMMENT":
                    raw_text_widget.tag_add("comment", idx1, idx2)
                elif kind == "STRING":
                    raw_text_widget.tag_add("str", idx1, idx2)
                elif kind == "NUMBER":
                    raw_text_widget.tag_add("num", idx1, idx2)
                elif kind == "WORD":
                    word = m.group("WORD")
                    if word in CODE_KEYWORDS:
                        raw_text_widget.tag_add("kw", idx1, idx2)
                    elif word in CODE_BUILTINS:
                        raw_text_widget.tag_add("builtin", idx1, idx2)

    def _apply_auto_indent(self):
        """OCR tarafından bozulmuş girintileri akıllıca hizalar."""
        current_code = self.code_tb.get("1.0", "end-1c")
        formatted = auto_indent_code(current_code)

        self.code_tb.delete("1.0", tk.END)
        self.code_tb.insert("1.0", formatted)
        self._refresh_code_view()

        # Butonda kısa süreli onay bildirimi göster
        old_text = self.btn_auto_indent.cget("text")
        self.btn_auto_indent.configure(text=f"  ✓ {t('copied_toast')}!")
        self.after(1200, lambda: self.btn_auto_indent.configure(text=old_text))

    def _on_segment_change(self, value):
        if value == t("ocr_view_code"):
            self._switch_mode("code")
        else:
            self._switch_mode("text")

    def _switch_mode(self, mode: str):
        self.current_mode = mode
        if mode == "code":
            # Metin kutusundaki güncel metni kod editörüne aktar
            current_text = self.txt_box.get("1.0", "end-1c")
            self.code_tb.delete("1.0", tk.END)
            self.code_tb.insert("1.0", current_text)

            self.text_frame.pack_forget()
            self.code_frame.pack(fill=tk.BOTH, expand=True)
            self.btn_copy.configure(text=f"  {t('ocr_copy_code')}")
            self.lbl_hint.configure(text=t("ocr_code_syntax_info"))
            self._refresh_code_view()
        else:
            # Kod editöründeki güncel metni düz metin kutusuna aktar
            current_code = self.code_tb.get("1.0", "end-1c")
            self.txt_box.delete("1.0", tk.END)
            self.txt_box.insert("1.0", current_code)

            self.code_frame.pack_forget()
            self.text_frame.pack(fill=tk.BOTH, expand=True)
            self.btn_copy.configure(text=f"  {t('ocr_copy_all')}")
            self.lbl_hint.configure(text=t("ocr_auto_copied_hint"))

    def _on_copy_clicked(self):
        """Seçili moddaki metni/kodu panoya kopyalar."""
        if self.current_mode == "code":
            content = self.code_tb.get("1.0", "end-1c")
        else:
            content = self.txt_box.get("1.0", "end-1c")

        try:
            self.clipboard_clear()
            self.clipboard_append(content)
        except Exception:
            pass

        original_text = self.btn_copy.cget("text")
        self.btn_copy.configure(text=f"✓  {t('copied_toast')}!")
        self.after(1500, lambda: self.btn_copy.configure(text=original_text))

"""
Google Lens Reverse Engineering Engine
=====================================
Windows Ekran Alıntısı Aracı'nın Bing Visual Search servisini Google Lens ile
değiştirmek için geliştirilen tersine mühendislik motoru.

Google Lens v3 Upload API'sini doğrudan kullanarak resmi üçüncü parti bir servise
(Imgur, Catbox vb.) ihtiyaç duymadan doğrudan Google sunucularına aktarır ve
arama sonuç sayfasını (udm=26) tarayıcıda açar.
"""

import io
import webbrowser
import logging
import requests
from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

GOOGLE_LENS_UPLOAD_URL = "https://lens.google.com/v3/upload"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/130.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
}


def prepare_image_bytes(image_input) -> bytes:
    """Gelen girdi nesnesini (PIL.Image, dosya yolu veya baytlar) JPEG formatında bayt dizisine dönüştürür."""
    if isinstance(image_input, bytes):
        return image_input

    if isinstance(image_input, str):
        # Dosya yolu
        with Image.open(image_input) as img:
            return _pil_to_jpeg_bytes(img)

    if isinstance(image_input, Image.Image):
        return _pil_to_jpeg_bytes(image_input)

    raise ValueError("Desteklenmeyen resim formatı!")


def _pil_to_jpeg_bytes(img: Image.Image) -> bytes:
    """PIL Image nesnesini RGB JPEG baytlarına çevirir."""
    if img.mode in ("RGBA", "P", "LA"):
        # Şeffaf pencereleri beyaz arka plan üzerine oturt
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "RGBA":
            background.paste(img, mask=img.split()[3])
        else:
            background.paste(img.convert("RGBA"))
        img_rgb = background
    elif img.mode != "RGB":
        img_rgb = img.convert("RGB")
    else:
        img_rgb = img

    buf = io.BytesIO()
    img_rgb.save(buf, format="JPEG", quality=95, optimize=True)
    return buf.getvalue()


def search_with_google_lens(image_input, open_browser: bool = True) -> str | None:
    """
    Verilen resmi Google Lens'e yükler ve sonuç URL'sini döndürür.
    
    :param image_input: PIL Image, dosya yolu veya resim baytları
    :param open_browser: True ise sonucu otomatik olarak varsayılan tarayıcıda açar
    :return: Google Lens sonuç URL'si veya hata durumunda None
    """
    try:
        jpeg_bytes = prepare_image_bytes(image_input)
        files = {
            "encoded_image": ("screenshot.jpg", jpeg_bytes, "image/jpeg")
        }

        logging.info("Resim Google Lens'e yükleniyor (%d bayt)...", len(jpeg_bytes))
        response = requests.post(
            GOOGLE_LENS_UPLOAD_URL,
            headers=HEADERS,
            files=files,
            allow_redirects=False,
            timeout=12
        )

        # Google Lens başarılı yüklemede HTTP 303 See Other döndürür
        if response.status_code == 303 and "Location" in response.headers:
            lens_url = response.headers["Location"]
            logging.info("Google Lens arama bağlantısı alındı: %s", lens_url[:80] + "...")
            if open_browser:
                webbrowser.open(lens_url)
            return lens_url

        logging.warning("Google Lens beklenmeyen durum kodu döndürdü: %d", response.status_code)
        # Yedek mekanizma: Eğer doğrudan 303 gelmediyse images.google.com aç
        fallback_url = "https://images.google.com"
        if open_browser:
            webbrowser.open(fallback_url)
        return fallback_url

    except Exception as e:
        logging.error("Google Lens yükleme hatası: %s", e)
        return None


if __name__ == "__main__":
    from PIL import ImageGrab
    print("Panodaki resim test ediliyor...")
    clip_img = ImageGrab.grabclipboard()
    if clip_img:
        search_with_google_lens(clip_img, open_browser=True)
    else:
        print("Panoda resim bulunamadı. Lütfen bir ekran alıntısı yapıp tekrar deneyin.")

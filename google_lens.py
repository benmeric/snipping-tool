"""
Google Lens Yükleme ve Arama Modülü (Gelişmiş & Doğrulanmış Sürüm)
==================================================================
Ekran alıntısını doğrudan hızlı ve güvenilir bir görsel CDN'ine yükler
ve Google Lens'e (https://lens.google.com/uploadbyurl?url=...) iletir.

Cloudflare engellerine takılmayan doğrulanmış CDN sağlayıcıları kullanır:
1. FreeImage (iili.io CDN)
2. Imgur (i.imgur.com CDN)
"""

import io
import logging
import webbrowser
import requests
from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def _image_to_jpeg_bytes(img: Image.Image) -> bytes:
    """PIL Image nesnesini optimize edilmiş JPEG baytlarına çevirir."""
    if img.mode in ("RGBA", "P", "LA"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "RGBA":
            bg.paste(img, mask=img.split()[3])
        else:
            bg.paste(img.convert("RGBA"))
        rgb_img = bg
    elif img.mode != "RGB":
        rgb_img = img.convert("RGB")
    else:
        rgb_img = img

    buf = io.BytesIO()
    rgb_img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def _upload_to_freeimage(jpeg_bytes: bytes) -> str | None:
    """FreeImage CDN'ine yükler (iili.io doğrudan erişilebilir CDN)."""
    try:
        data = {
            "key": "6d207e02198a847aa98d0a2a901485a5",
            "action": "upload",
            "format": "json"
        }
        files = {
            "source": ("screenshot.jpg", jpeg_bytes, "image/jpeg")
        }
        res = requests.post("https://freeimage.host/api/1/upload", data=data, files=files, timeout=9)
        if res.status_code == 200:
            result = res.json()
            url = result.get("image", {}).get("url")
            if url:
                return url
    except Exception as e:
        logging.warning("FreeImage yükleme uyarısı: %s", e)
    return None


def _upload_to_imgur(jpeg_bytes: bytes) -> str | None:
    """Yedek servis: Imgur API'sine doğrudan yükler."""
    try:
        headers = {"Authorization": "Client-ID 546c25a59c58ad7"}
        files = {"image": ("screenshot.jpg", jpeg_bytes, "image/jpeg")}
        res = requests.post("https://api.imgur.com/3/image", headers=headers, files=files, timeout=9)
        if res.status_code == 200:
            result = res.json()
            link = result.get("data", {}).get("link")
            if link:
                return link
    except Exception as e:
        logging.warning("Imgur yükleme uyarısı: %s", e)
    return None


def search_image_in_google_lens(img: Image.Image, open_browser: bool = True) -> str | None:
    """
    Ekran alıntısını doğrudan Google Lens'e gönderir ve arama sonuçlarını açar.
    
    :param img: Çekilen ekran görüntüsü (PIL Image)
    :param open_browser: True ise tarayıcıda açar
    :return: Google Lens URL'si veya None
    """
    try:
        jpeg_bytes = _image_to_jpeg_bytes(img)
        logging.info("Görsel yüklenmeye hazırlanıyor (%d bayt)...", len(jpeg_bytes))

        # 1. Birincil CDN sağlayıcısı (FreeImage / iili.io)
        direct_url = _upload_to_freeimage(jpeg_bytes)

        # 2. İkincil CDN sağlayıcısı (Imgur)
        if not direct_url:
            logging.info("Yedek görsel CDN'i (Imgur) deneniyor...")
            direct_url = _upload_to_imgur(jpeg_bytes)

        if not direct_url:
            logging.error("Görsel sunucuya yüklenemedi!")
            return None

        logging.info("Doğrudan görsel CDN bağlantısı oluşturuldu: %s", direct_url)

        # 3. Google Lens uploadbyurl uç noktası (URL doğrudan ve temiz iletilir)
        lens_search_url = f"https://lens.google.com/uploadbyurl?url={direct_url}"

        logging.info("Google Lens açılıyor: %s", lens_search_url)
        if open_browser:
            webbrowser.open(lens_search_url)

        return lens_search_url

    except Exception as e:
        logging.error("Google Lens arama hatası: %s", e)
        return None

"""
Ekran Alıntısı Aracı - OCR Metin Ayıklama Motoru
================================================
Google Lens'in güçlü bulut OCR yapay zeka modelini kullanarak
görseldeki tüm metinleri (Türkçe karakterler, sayılar, el yazısı)
yüksek doğrulukla ve anında ayıklar.
"""

import asyncio
import io
import logging
from PIL import Image
from chrome_lens_py import LensAPI

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def _image_to_jpeg_bytes(img: Image.Image) -> bytes:
    """PIL Image nesnesini JPEG baytlarına çevirir."""
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


async def _async_extract_text(jpeg_bytes: bytes) -> str:
    """LensAPI ile asenkron metin ayıklar."""
    async with LensAPI() as lens:
        res = await lens.process_image(jpeg_bytes)
        text = res.get("ocr_text", "")
        return text.strip() if text else ""


def extract_text_from_image(img: Image.Image) -> str:
    """
    Görseldeki tüm metinleri ayıklar ve string olarak döndürür.
    
    :param img: PIL Image nesnesi
    :return: Ayıklanan metin dizisi
    """
    try:
        jpeg_bytes = _image_to_jpeg_bytes(img)
        logging.info("Görsel OCR taraması yapılıyor (%d bayt)...", len(jpeg_bytes))
        
        # Async fonksiyonu senkron çalıştır
        text = asyncio.run(_async_extract_text(jpeg_bytes))
        logging.info("OCR tamamlandı, %d karakter bulundu.", len(text))
        return text
    except Exception as e:
        logging.error("OCR metin ayıklama hatası: %s", e)
        return ""


if __name__ == "__main__":
    from PIL import ImageDraw
    test_img = Image.new("RGB", (300, 80), color="white")
    d = ImageDraw.Draw(test_img)
    d.text((20, 25), "Ekran Alıntısı Aracı OCR Test 2026", fill="black")
    print("Test sonucu:", extract_text_from_image(test_img))

# Ekran Alıntısı Aracı (Açık Kaynak & Google Lens Destekli)
> **Geliştirici:** Meriç Yüzaklı  
> **Lisans:** MIT Lisansı (Açık Kaynak & Ücretsiz)  
> **Esinlenme & Referans:** Microsoft Windows 11 Ekran Alıntısı Aracı (Snipping Tool) Tersine Mühendislik Projesi

Windows'un dahili Ekran Alıntısı Aracı (**Snipping Tool**) görsel aramaları yalnızca **Microsoft Bing** üzerinden yapmaya zorlar ve arama motorunu Google ile değiştirmenize izin vermez. 

**Ekran Alıntısı Aracı**, Windows Snipping Tool'un bu kısıtlamasını tersine mühendislik ile aşmak, `Print Screen` (`PrtScn / SysRq`) tuşuyla aldığınız ekran alıntılarını **doğrudan Google Lens** ile aratmak ve modern yapay zeka özellikleri (çoklu görsel birleştirme/kolaj, OCR, çakışmasız pano) sunmak için **Meriç Yüzaklı** tarafından geliştirilmiş açık kaynaklı bir masaüstü uygulamasıdır.

---

## 🔍 Tersine Mühendislik (Reverse Engineering) Bulguları

Windows 11 Snipping Tool (`Microsoft.ScreenSketch_11.2608.41.0_x64__8wekyb3d8bbwe`) ikili dosyaları (`SnippingTool.Net.RuntimeComponent.dll` ve `SnippingToolUI.dll`) incelendiğinde şu sonuçlara ulaşılmıştır:

1. **Bing Servisine Katı Bağımlılık (Hardcoded URL):**
   - Kaynak kod yolu: `/_/src/SnippingTool.Net.Core/Services/VisualSearchService.cs`
   - Dahili API: `https://www.bing.com/images/search?view=detailv2&iss=sbiupload&FORM=SBISNP&sbisrc=ImgPicker&idpbck=1`
   - Kod, ekran alıntısını doğrudan Bing'in görsel arama sunucusuna POST etmekte ve dönen yönlendirmeyi `Windows.System.Launcher.LaunchUriAsync` ile Microsoft Edge'e göndermektedir. Kayıt defterinde (Registry) veya ayarlarda bunu değiştirecek bir anahtar bulunmamaktadır.

2. **Google Lens API'sinin Keşfi:**
   - Google Lens'in web uç noktası `https://lens.google.com/v3/upload` doğrudan analiz edilmiştir.
   - Resim verisi `multipart/form-data` formatında `encoded_image` parametresi ile gönderildiğinde Google sunucusu anında **HTTP 303 See Other** döndürerek `Location` başlığında görsel arama sonuç linkini (`https://www.google.com/search?vsrid=...&udm=26...`) sağlamaktadır.
   - **Gizlilik Avantajı:** Hiçbir 3. parti dosya barındırma servisine (Imgur, Catbox vb.) ihtiyaç kalmadan, resim doğrudan şifreli olarak Google Lens'e gider.

---

## 🚀 Özellikler

1. **🔍 Doğrudan Google Lens Entegrasyonu (Bing Zorunluluğu Yok):**
   - Ekran alıntısı aldığınızda resim Bing yerine doğrudan resmi Google Lens API'sine yüklenir ve varsayılan tarayıcınızda açılır.
2. **🧩 Çoklu Görselleri Birleştirme (AI Kolaj Modu):**
   - Birden fazla ekran görüntüsünü Dikey, Yatay veya Izgara (Grid) düzeninde birleştirerek tek görsel haline getirir.
   - Yapay zeka modellerine (ChatGPT, Claude, Gemini) referans verirken görsellerin üzerine otomatik **`[1]`**, **`[2]`**, **`[3]`** rozetleri basar.
3. **🔤 Google Lens Yapay Zeka OCR (Metin Ayıklama):**
   - Ekrandaki Türkçe ve çok dilli metinleri yüksek doğrulukla ayıklar ve panonuza kopyalar.
4. **📋 Akıllı Pano Çakışma Önleyici (AI İsimlendirme):**
   - Yapay zekaya veya web sitelerine yapıştırırken oluşan `resim.png` çakışmalarını önlemek için milisaniyelik zaman damgalı çoklu format (`CF_HDROP`, `CF_PNG`, `CF_DIB`) desteği.
5. **🎥 Ekran Video Kaydı & Canlı Vurgu Çerçevesi:**
   - Seçtiğiniz alanın etrafında canlı parlak kırmızı çerçeve vurgusuyla yüksek kaliteli mikrofon/hoparlör destekli video kaydı.
6. **🖥️ Windows 11 Fluent Tasarım:**
   - Dikdörtgen, Pencere, Tam Ekran ve Serbest Form kırpma; Kalem, Şeffaf Vurgulayıcı, Silgi ve Ayarlar paneli.
7. **Sistem Tepsisi & 0% CPU Kullanımı:**
   - Arka planda kaynak tüketmeden sessizce bekler, PrtScn tuşuna basıldığında anında devreye girer.

---

## 📦 Kurulum ve Çalıştırma

### 1. Gerekli Kütüphanelerin Yüklenmesi
Sisteminizde Python 3 yüklüyse komut satırından çalıştırın:
```bash
pip install -r requirements.txt
```

### 2. Uygulamayı Başlatma
- **Görünür Konsol ile Başlatmak İçin:**
  `Baslat.bat` dosyasına çift tıklayın.
- **Arka Planda Tamamen Sessiz Başlatmak İçin:**
  `ArkaPlandaBaslat.vbs` dosyasına çift tıklayın (sağ altta sistem tepsisine yerleşir).

---

## ⚙️ Yapılandırma (`config.json`)

Ayarları sistem tepsisi menüsünden değiştirebileceğiniz gibi `config.json` üzerinden de özelleştirebilirsiniz:

```json
{
    "auto_search_on_clipboard": true,
    "show_toast_notification": true,
    "play_sound": true,
    "enable_custom_snipper": true,
    "custom_hotkey": "ctrl+shift+s",
    "intercept_print_screen": false
}
```

- `auto_search_on_clipboard`: `Print Screen` ile kopyalanan resimlerin otomatik Google Lens'te açılması (Açık: `true`).
- `intercept_print_screen`: `Print Screen` tuşuna basıldığında doğrudan kendi kırpma motorunu devreye sokmak için `true` yapabilirsiniz.

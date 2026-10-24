<p align="center">
  <img src="assets/app_icon.png" width="128" height="128" alt="Snipping Tool Logo">
</p>

<h1 align="center">Ekran Alıntısı Aracı (Google Lens & AI Görsel Birleştirici)</h1>

<p align="center">
  <strong>Doğrudan Google Lens görsel araması, Yapay Zeka Vision modelleri için optimize edilmiş çoklu ekran alıntısı kolajı, sözdizimi vurgulamalı kod OCR motoru, sesli ekran video kaydı ve yerel Windows sistem entegrasyonu sunan modern, açık kaynaklı Windows 11 ekran alıntısı aracı.</strong>
</p>

<p align="center">
  <a href="README.md"><b>English</b></a> | 
  <a href="README_TR.md"><b>Türkçe</b></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Windows%2011%20%7C%2010-0078D4?logo=windows" alt="Platform">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Lisans-MIT-green.svg" alt="Lisans">
  <img src="https://img.shields.io/badge/Arayz-Fluent%20Design-005FB8" alt="Fluent Design">
  <img src="https://img.shields.io/badge/Grsel%20Arama-Google%20Lens-4285F4?logo=google" alt="Google Lens">
  <img src="https://img.shields.io/badge/AI%20Vision-Token%20Optimize-8A2BE2" alt="AI Vision Optimize">
</p>

---

## 📸 Arayüz Vitrini

<p align="center">
  <img src="assets/ui_main_window.png" width="48%" alt="Ana Arayüz" style="border-radius: 8px;">
  <img src="assets/ui_image_combiner.png" width="48%" alt="Yapay Zeka Çoklu Görsel Birleştirici" style="border-radius: 8px;">
</p>
<p align="center">
  <img src="assets/ui_ocr_code_view.png" width="58%" alt="Sözdizimi Vurgulamalı OCR Kod Görünümü" style="border-radius: 8px;">
  <img src="assets/ui_settings.png" width="38%" alt="Windows Fluent Ayarlar Paneli" style="border-radius: 8px;">
</p>

---

## 📖 Genel Bakış

Windows 11'in yerleşik **Ekran Alıntısı Aracı** (Snipping Tool), görsel arama motorunu kesin olarak **Microsoft Bing**'e kilitler ve arama motorunu Google olarak değiştirebileceğiniz herhangi bir ayar veya kayıt defteri anahtarı sunmaz.

**Snipping Tool**, **Meriç Yüzaklı** tarafından Windows 11 Ekran Alıntısı Aracı ikili dosyalarının tersine mühendislikle analiz edilmesiyle geliştirilmiş yüksek performanslı ve açık kaynaklı bir masaüstü uygulamasıdır. Alınan ekran alıntılarını doğrudan resmi **Google Lens** web API'ına aktararak Bing kısıtlamasını tamamen ortadan kaldırır.

Bunun yanı sıra yerel Windows aracında bulunmayan, geliştiricilere ve yapay zeka kullanıcılarına yönelik çığır açan özellikler sunar:
- **Yapay Zeka & Vision Modelleri için Çoklu Ekran Alıntısı Birleştirici:** Ardışık ekran görüntülerini numaralandırılmış referans rozetleriyle birleştirerek token tüketimini ve API maliyetlerini düşürür.
- **Akıllı OCR & Kod Görünümü:** Ekrandan taranan yazılım kodlarını otomatik tanır, VS Code tarzı sözdizimi renklendirmesi, satır numaraları ve tek tıkla girinti düzeltme (**Auto-Indent**) sunar.
- **Yerel Windows Protokol Yöneticisi:** Sisteme resmi `ms-screenclip:` protokol yöneticisi olarak kaydolur; `PrtScn` ve `Win+Shift+S` tuşlarını sistem seviyesinde yakalar.
- **Donanım Hızlandırmalı Ekran Video Kaydı:** Mikrofon ve sistem döngü (loopback) seslerini destekleyen pürüzsüz alan video kaydı.

---

## 🧩 Yapay Zeka & Vision Modelleri için Çoklu Ekran Görüntüsü Birleştirici

Bu özellik, kullanıcıların ardışık olarak birden fazla ekran görüntüsü alıp bunları yapay zeka modellerine (**GPT-4o**, **Claude 3.5 Sonnet**, **Gemini 1.5 Pro**) göndermeden önce tek bir birleşik kanvasta toplamasına olanak tanır.

<p align="center">
  <img src="assets/ui_image_combiner.png" width="90%" alt="AI Görsel Birleştirici Arayüzü">
</p>

### 🚀 Temel Avantajlar ve Yapay Zeka Kıyaslamaları

#### 1. Devasa Token ve Maliyet Tasarrufu (Base Token Optimizasyonu)
Vision LLM'leri (Görsel Dil Modelleri), çözünürlükten bağımsız olarak yüklenen her bağımsız görsel dosyası için sabit ve yüksek bir **"Base Token"** (Taban Token) ücreti talep eder; ardından yüksek çözünürlüklü parçalar için ek token hesaplar.
- **Problem:** 5 ayrı ekran görüntüsü yüklemek, yapay zekanın taban token maliyetini 5 ayrı defa tahsil etmesine yol açar.
- **Çözümümüz:** 5 ekran görüntüsü tek bir kanvasta birleştirildiğinde, yapay zeka taban token maliyetini **yalnızca 1 kez** tahsil eder. Bu sayede ilk token tüketimi önemli ölçüde azalır, API maliyeti düşer ve bağlam penceresinde (context window) büyük yer kazanılır.

#### 2. Arayüz Dosya Yükleme Limitlerini Aşma
Birçok LLM sohbet arayüzü (ChatGPT, Claude.ai veya kurumsal portallar), tek bir istem (prompt) başına izin verilen görsel ekleme sayısına katı sınırlar koyar (genellikle en fazla 4 veya 5 görsel). Bu araç, **10'dan fazla görsel adımı tek bir dosyada birleştirerek** bu sınırlamaları zahmetsizce baypas eder.

#### 3. Üstün Mekânsal ve Kronolojik Bağlam Algısı
Görseller ayrı ayrı yüklendiğinde, Vision modelleri adımlar arasındaki kronolojik sırayı veya konumsal ilişkileri kaybedebilir.
- **Kronolojik İş Akışları:** Adım adım hata bildirimleri için idealdir (`Adım [1] -> Adım [2] -> Adım [3]`).
- **Yan Yana Karşılaştırmalar:** UI/UX denetimleri, kod diff karşılaştırmaları veya tasarımdan koda dönüşümler için mükemmeldir; modelin *"sol paneldeki [1]"* ile *"sağ paneldeki [2]"* arasında akıl yürütmesini kolaylaştırır.

### 🛠️ Yerleşik Birleştirme Yetenekleri

| Yetenek | Açıklama |
| :--- | :--- |
| **Esnek Düzen Motoru** | **Dikey sıralama** (yukarıdan aşağıya), **Yatay şerit** (yan yana) veya **Izgara (Grid)** (otomatik kare matris). |
| **Otomatik Numaralandırma Rozetleri `[1]`, `[2]`** | Her ekran görüntüsünün sol üst köşesine yüksek kontrastlı zarif numaralar ekler (*"Adım 3'teki hatayı analiz et"* gibi nokta atışı promptlar yazmayı sağlar). |
| **Özel Boşluk & Arka Planlar** | Görseller arası ayarlanabilir boşluklar ve tema seçenekleri (`Karanlık #1E1E1E`, `Tam Siyah #000000`, `Saf Beyaz #FFFFFF`, `Gri #333333`). |
| **Anında Dışa Aktarma** | Tek tıkla **Panoya Kopyalama** (`Ctrl + C`), **Farklı Kaydetme** (`Ctrl + S`) veya çizim yapmak için **Düzenleyicide Açma**. |

---

## 🔤 Akıllı OCR & Sözdizimi Vurgulamalı Kod Çıkarma

Ekrandaki kodları videolardan, PDF'lerden, web sitelerinden veya terminallerden yakalamak artık tek tıkla mümkündür:

- **Ana Çubuktan 1 Tıkla Metin/Kod Tarama:** Kompakt araç çubuğundaki OCR ikonuna (`🔍`) tıklayarak ekrandaki herhangi bir metin veya kod alanını doğrudan seçebilirsiniz.
- **Otomatik Kod Tespiti:** Taranan içeriğin programlama kodu (Python, JavaScript, C/C++, HTML vb.) olduğunu tespit eder ve doğrudan **Kod Görünümü** modunda açılır.
- **Satır Numaraları & Senkronize Kaydırma:** Kod editörüyle eş zamanlı kayan satır numaraları oluğu (gutter).
- **VS Code Tarzı Sözdizimi Renklendirmesi:** Anahtar kelimeler, metinler (string), yorumlar, sayılar ve fonksiyonlar gerçek zamanlı renklendirilir.
- **🪄 1 Tıkla Otomatik Girintileme (`Girintileri Düzenle`):** OCR taraması sırasında düzleşen veya kaybolan blok girintilerini (`:` ve `{}` mantığına göre) hiyerarşik Python/C girintilerine otomatik kavuşturur.
- **Temiz Kod Kopyalama:** Satır numaralarını dahil etmeden yalnızca temiz, formatlanmış kodu panoya kopyalar.

---

## ✨ Tüm Özellikler Tablosu

| Özellik | Açıklama |
| :--- | :--- |
| 🔍 **Doğrudan Google Lens Araması** | Bing zorunluluğunu aşar. Ekran görüntülerini doğrudan resmi Google Lens API'ına gönderir ve varsayılan tarayıcınızda açar. |
| 🧩 **AI Görsel Birleştirici & Kolaj** | Birden çok ekran görüntüsünü LLM'ler için `[1]`, `[2]`, `[3]` referans rozetleriyle tek bir dosyada birleştirir. |
| 🔤 **OCR Kod & Metin Ayıklayıcı** | Gerçek zamanlı sözdizimi renklendirmesi, satır numaraları ve akıllı girinti düzeltmeyle kodları anında ayıklar. |
| ⚡ **Varsayılan Windows Aracı Entegrasyonu** | Tek tıkla varsayılan ekran alıntısı aracı olur; `PrtScn`, `Win+Shift+S` ve `ms-screenclip:` çağrılarını sistem seviyesinde yakalar. |
| 🖥️ **Masaüstü Kısayolu** | Masaüstünüze özel yüksek çözünürlüklü ikonlu Windows kısayolunu (`.lnk`) otomatik ekler. |
| 🚀 **Windows Açılışında Çalışma** | Sistem açılışında arka planda sessizce başlar (`--startup`), sistem tepsisinde bekler ve %0 boşta CPU harcar. |
| 🎥 **Sesli Ekran Video Kaydı** | Mikrofon ve dahili sistem seslerini destekleyen yüksek kaliteli alan video kaydı. |
| 📋 **Akıllı Çakışmasız Pano Motoru** | Yapay zekaya yapıştırırken `resim.png` dosya adı çakışmalarını önleyen zaman damgalı pano formatları (`CF_HDROP`, `CF_PNG`, `CF_DIB`). |
| 🎨 **Windows 11 Fluent Tasarım** | Koyu & Açık temalar, çizim araçları (Kalem, Vurgulayıcı, Silgi), kenarlık ve gecikme sayaçları (3s, 5s, 10s). |
| 🌐 **Çoklu Dil Desteği (i18n)** | İngilizce, Türkçe, Almanca, İspanyolca, Fransızca ve Rusça dillerinde çalışma anında anlık dil değişimi. |

---

## 🔍 Tersine Mühendislik Bulguları

Windows 11'in yerel Ekran Alıntısı Aracı ikili dosyaları (`SnippingTool.Net.RuntimeComponent.dll` ve `SnippingToolUI.dll`) incelendiğinde şu mimari kısıtlamalar tespit edilmiştir:

1. **Sabit Kodlanmış (Hardcoded) Bing Uç Noktası:**
   - Kaynak yolu: `/_/src/SnippingTool.Net.Core/Services/VisualSearchService.cs`
   - Dahili API: `https://www.bing.com/images/search?view=detailv2&iss=sbiupload&FORM=SBISNP&sbisrc=ImgPicker&idpbck=1`
   - Yerel uygulama doğrudan Bing sunucusuna HTTP POST isteği göndermekte ve Microsoft Edge'i `LaunchUriAsync` ile tetiklemektedir. Bunu değiştirecek hiçbir ayar bulunmamaktadır.

2. **Google Lens Web API Etkileşimi:**
   - Alınan ekran görüntüleri TLS üzerinden `multipart/form-data` ile `https://lens.google.com/v3/upload` adresine gönderilir.
   - Google sunucusu anında **HTTP 303 See Other** yanıtı dönerek arama sonuçları URL'sini verir.
   - **Gizlilik Garantisi:** Görseller hiçbir üçüncü taraf aracı sunucuya (Imgur vb.) uğramadan doğrudan resmi Google uç noktasına iletilir.

---

## 📊 Microsoft Snipping Tool ile Karşılaştırma

| Yetenek | Microsoft Snipping Tool | Bu Açık Kaynak Araç |
| :--- | :---: | :---: |
| **Görsel Arama Motoru** | ❌ Yalnızca Bing (Kilitli) | ✅ **Google Lens (Doğrudan)** |
| **AI Çoklu Görsel Birleştirici** | ❌ Yok | ✅ **Dikey, Yatay, Izgara** |
| **AI Referans Rozetleri `[1]`, `[2]`** | ❌ Yok | ✅ **Otomatik Numaralandırma** |
| **OCR Kod Görünümü & Auto-Indent** | ❌ Sadece düz metin | ✅ **Renkli Kod & Satır No** |
| **Sistem Protokol Yönlendirme** | Varsayılan UWP | ✅ **Yerel `ms-screenclip:` İşleyici** |
| **Sesli Ekran Video Kaydı** | Temel | ✅ **Mikrofon + Sistem Sesi** |
| **PrtScn Tuşu Yakalama** | Standart Windows hook | ✅ **< 20ms Gecikmesiz Hook** |
| **Tekil Örnek IPC Daemon** | UWP İşlemi | ✅ **Yerel Loopback Soket IPC** |
| **Kaynak Kod & Özelleştirme** | ❌ Kapalı Kaynak | ✅ **%100 Açık Kaynak (MIT)** |

---

## 🚀 Kurulum & Çalıştırma

### 1. Gereksinimler
- Windows 11 veya Windows 10 (64-bit)
- Python 3.10 veya üzeri

### 2. Repoyu Klonlayın
```bash
git clone https://github.com/benmeric/snipping-tool.git
cd snipping-tool
```

### 3. Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```

### 4. Uygulamayı Başlatın
- **Standart Arayüz:**
  ```bash
  python main.py
  ```
  *(veya `Start.bat` / `SnippingTool.bat` dosyasına çift tıklayın)*

- **Sessiz Arka Plan (Sistem Tepsisi):**
  Terminal penceresi açmadan arka planda çalıştırmak için `StartBackground.vbs` dosyasına çift tıklayın.

---

## ⚡ Windows Sistem Entegrasyonu

Uygulamayı Windows varsayılan ekran alıntısı aracı yapmak için:
1. Uygulamayı açın ve **Ayarlar**'a gidin (`Ctrl + ,` veya `...` menüsü).
2. **Kısayollar & Sistem** başlığı altından **Varsayılan Ekran Alıntısı Aracı Yap** seçeneğini açık konuma getirin.
3. Bilgisayar açıldığında hazır olması için **Windows ile Başlat** ayarını açık konuma getirin.
4. Masaüstünüze ikon eklemek için **Masaüstüne Kısayol Ekle** butonuna tıklayın.

---

## ⌨️ Klavye Kısayolları

| Kısayol | İşlem |
| :--- | :--- |
| **`PrtScn`** veya **`Win + Shift + S`** | Ekran alıntısı başlat (Dikdörtgen, Pencere, Tam Ekran, Serbest Çizim) |
| **`Ctrl + Shift + S`** | Fotoğraf alıntısı başlat |
| **`Ctrl + Shift + R`** | Alan ekran video kaydını başlat |
| **`Ctrl + G`** | Mevcut görüntüyü Google Lens'te ara |
| **`Ctrl + C`** | Alıntıyı panoya kopyala |
| **`Ctrl + S`** | Görseli diske kaydet |
| **`Ctrl + Z`** | Çizim işlemini geri al |
| **`Ctrl + ,`** | Ayarlar panelini aç |
| **`+`** veya **`Numpad +`** | Yeni alıntı veya kayıt başlat |
| **`ESC`** | Kırpma ekranını iptal et |

---

## 📜 Lisans

Bu proje **MIT Lisansı** ile lisanslanmıştır — ayrıntılar için [LICENSE](LICENSE) dosyasına bakabilirsiniz.

Geliştirici: **Meriç Yüzaklı**

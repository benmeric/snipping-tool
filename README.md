<p align="center">
  <img src="assets/app_icon.png" width="128" height="128" alt="Ekran Alıntısı Aracı Logo">
</p>

<h1 align="center">Ekran Alıntısı Aracı (Snipping Tool + Google Lens)</h1>

<p align="center">
  <strong>Modern Windows 11 Snipping Tool with Google Lens Integration, AI Image Combiner, Multilingual Support & Screen Recording</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Windows%2011%20%7C%2010-0078D4?logo=windows" alt="Platform">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/UI-Fluent%20Design-005FB8" alt="Fluent Design">
  <img src="https://img.shields.io/badge/AI%20Search-Google%20Lens-4285F4?logo=google" alt="Google Lens">
</p>

---

## 🌍 Dil Seçimi / Language
- [Türkçe Dokümantasyon](#-türkçe)
- [English Documentation](#-english)

---

<a name="-türkçe"></a>
## 🇹🇷 Türkçe

### 📌 Proje Hakkında
Windows'un yerleşik Ekran Alıntısı Aracı (**Snipping Tool**), görsel aramaları zorunlu olarak **Microsoft Bing** üzerinden yapar ve arama motorunu Google ile değiştirmenize izin vermez. 

**Ekran Alıntısı Aracı**, bu kısıtlamayı aşmak, `Print Screen` tuşuyla aldığınız ekran görüntülerini **doğrudan resmi Google Lens API'si** üzerinden aratmak, yapay zeka modelleri (ChatGPT, Claude, Gemini) için **akıllı görsel birleştirme (kolaj)** yapmak, ekran video kaydı almak ve tam metin tanıma (OCR) sağlamak amacıyla **Meriç Yüzaklı** tarafından geliştirilmiş açık kaynaklı ve bağımsız bir masaüstü uygulamasıdır.

### ✨ Öne Çıkan Özellikler

| Özellik | Açıklama |
| :--- | :--- |
| 🔍 **Google Lens Görsel Arama** | Bing zorunluluğu olmadan, ekran alıntılarını doğrudan Google Lens web API'sine yükler ve varsayılan tarayıcınızda arama sonuçlarını açar. |
| 🧩 **AI Görsel Birleştirici (Kolaj)** | Birden çok ekran görüntüsünü Dikey, Yatay veya Izgara (Grid) düzeninde birleştirir. Yapay zekaya referans verirken görsellere otomatik `[1]`, `[2]`, `[3]` numaralandırma rozetleri ekler. |
| 🌐 **Çok Dilli Arayüz (i18n)** | Sistem dilini otomatik algılar. Ayarlar menüsünden Türkçe, İngilizce, Almanca, Fransızca, İspanyolca, Rusça, Çince, Japonca ve Korece dilleri arasında anında geçiş yapılabilir. |
| 🔤 **Google Lens Yapay Zeka OCR** | Ekrandaki metinleri yüksek doğrulukla ayıklar ve doğrudan panoya kopyalar. |
| 🎥 **Sesli Ekran Video Kaydı** | Mikrofon ve sistem sesi desteğiyle, canlı parlak kırmızı vurgu çerçevesi eşliğinde yüksek kaliteli video kaydı alır. |
| 📋 **Akıllı Pano Çakışma Önleyici** | Web sitelerine ve yapay zekaya yapıştırırken oluşan dosya ismi çakışmalarını önleyen zaman damgalı çoklu format (`CF_HDROP`, `CF_PNG`, `CF_DIB`) desteği. |
| 🎨 **Windows 11 Fluent Tasarım** | Koyu/Açık tema, akrilik derinlik, çizim araçları (Kalem, Şeffaf Vurgulayıcı, Silgi), gecikmeli çekim ve sistem tepsisinde 0% CPU kullanımı. |

### 🚀 Kurulum ve Çalıştırma

1. **Projeyi İndirin / Klonlayın:**
   ```bash
   git clone https://github.com/benmeric/snipping-tool.git
   cd snipping-tool
   ```

2. **Gerekli Paketleri Yükleyin:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Uygulamayı Başlatın:**
   - Konsol ile: `Baslat.bat` veya `python main.py`
   - Arka planda sessiz (Sistem Tepsisi): `ArkaPlandaBaslat.vbs`

---

<a name="-english"></a>
## 🇬🇧 English

### 📌 About The Project
Windows 11's built-in **Snipping Tool** forces visual searches through **Microsoft Bing** with no option to switch your default search provider to Google.

**Ekran Alıntısı Aracı** (Snipping Tool) is an open-source, modern desktop application developed by **Meriç Yüzaklı** to overcome this limitation. It enables one-click visual search via **Google Lens**, smart **AI multi-image collage merging** with numbered reference badges, precision OCR, audio-supported screen video recording, and a native Windows 11 Fluent interface.

### ✨ Key Features

| Feature | Description |
| :--- | :--- |
| 🔍 **Direct Google Lens Search** | Bypasses Bing lock-in. Uploads captures straight to the official Google Lens web endpoint and opens results instantly in your default browser. |
| 🧩 **AI Image Combiner & Collage** | Merge multiple screenshots vertically, horizontally, or in a 2x2 grid. Automatically stamps `[1]`, `[2]`, `[3]` badges for easy AI prompt referencing (ChatGPT, Claude, Gemini). |
| 🌐 **Multilingual Support (i18n)** | Auto-detects OS locale with instant switching between English, Turkish, German, French, Spanish, Russian, Chinese, Japanese, and Korean. |
| 🔤 **AI Optical Character Recognition (OCR)** | Instant and accurate text extraction from any region of the screen directly to your clipboard. |
| 🎥 **Screen Video Recording with Audio** | High-definition area recording with microphone and system audio support, featuring a live reactive capture frame. |
| 📋 **Smart Conflict-Free Clipboard** | Multi-format clipboard support (`CF_HDROP`, `CF_PNG`, `CF_DIB`) with millisecond timestamps to prevent AI chat image collisions. |
| 🎨 **Windows 11 Fluent Design** | Dark & Light modes, acrylic glassmorphism, customizable snip borders, drawing tools (Pen, Highlighter, Eraser), and 0% idle CPU tray daemon. |

### 🚀 Installation & Usage

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/benmeric/snipping-tool.git
   cd snipping-tool
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Application:**
   - Normal run: double-click `Baslat.bat` or run `python main.py`
   - Silent background mode (System Tray): double-click `ArkaPlandaBaslat.vbs`

---

## 📜 Lisans / License
Bu proje [MIT Lisansı](LICENSE) altında dağıtılmaktadır. / This project is licensed under the [MIT License](LICENSE).
Geliştirici / Author: **Meriç Yüzaklı**

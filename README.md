<p align="center">
  <img src="assets/app_icon.png" width="128" height="128" alt="Snipping Tool Logo">
</p>

<h1 align="center">Snipping Tool (Google Lens & AI Collage)</h1>

<p align="center">
  <strong>A modern, open-source Windows 11 Snipping Tool alternative with Google Lens visual search, AI multi-image collage combiner, optical character recognition (OCR), screen video recording, and native system integration.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Windows%2011%20%7C%2010-0078D4?logo=windows" alt="Platform">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/UI-Fluent%20Design-005FB8" alt="Fluent Design">
  <img src="https://img.shields.io/badge/AI%20Search-Google%20Lens-4285F4?logo=google" alt="Google Lens">
</p>

---

## 📖 Overview

Windows 11's built-in **Snipping Tool** locks visual search strictly to **Microsoft Bing** with no user setting or registry key to change your default search engine to Google.

**Snipping Tool** is a high-performance, open-source desktop utility authored by **Meriç Yüzaklı**. Developed through reverse engineering the Windows 11 Snipping Tool binaries, this application eliminates Bing lock-in by uploading captures directly to the official **Google Lens** web API. In addition, it introduces advanced features missing from the native tool: **AI multi-image collage merging** with numbered reference badges (optimized for ChatGPT, Claude, and Gemini), hardware-accelerated screen video recording with audio, a conflict-free clipboard engine, and one-click integration as the native Windows default snipping tool.

---

## ✨ Key Features

| Feature | Description |
| :--- | :--- |
| 🔍 **Direct Google Lens Search** | Bypasses Bing lock-in. Uploads captures directly to the official Google Lens web endpoint and opens results in your default browser with zero third-party hosts. |
| 🧩 **AI Image Combiner & Collage** | Merge multiple screenshots vertically, horizontally, or in a 2×2 grid. Automatically stamps `[1]`, `[2]`, `[3]` numbered badges for effortless AI prompt referencing. |
| ⚡ **Native Windows Default Tool** | One-click setup as the system default. Seamlessly intercepts `PrtScn`, `Win+Shift+S`, and the native Windows `ms-screenclip:` protocol without requiring administrator privileges. |
| 🖥️ **Desktop Shortcut Integration** | Instantly create a branded Windows shortcut (`.lnk`) with the custom multi-resolution application icon on your desktop from settings or the toolbar. |
| 🚀 **Run on Windows Startup** | Silently initializes in the background on system boot (`--startup`) with a lightweight system tray daemon and 0% idle CPU utilization. |
| 🔤 **High-Precision AI OCR** | Extract text instantly from any screen region and copy directly to your clipboard with high accuracy. |
| 🎥 **Area Video Recording with Audio** | High-definition area video recording supporting both microphone and system loopback audio, highlighted by a live reactive border. |
| 📋 **Conflict-Free Smart Clipboard** | Multi-format clipboard support (`CF_HDROP`, `CF_PNG`, `CF_DIB`) with millisecond timestamps to prevent image name collisions when pasting into web applications. |
| 🎨 **Windows 11 Fluent Design** | Sleek acrylic glassmorphism, Dark & Light modes, drawing tools (Pen, Alpha Highlighter, Eraser), custom border styling, and delay timers (3s, 5s, 10s). |
| 🌐 **Multilingual Interface (i18n)** | Available in English, Turkish, German, Spanish, French, and Russian with instant runtime language switching. |

---

## 🔍 Reverse Engineering Findings

An analysis of the native Windows 11 Snipping Tool binaries (`SnippingTool.Net.RuntimeComponent.dll` and `SnippingToolUI.dll`) revealed the following architectural constraints:

1. **Hardcoded Bing Endpoint:**
   - Source path: `/_/src/SnippingTool.Net.Core/Services/VisualSearchService.cs`
   - Internal API: `https://www.bing.com/images/search?view=detailv2&iss=sbiupload&FORM=SBISNP&sbisrc=ImgPicker&idpbck=1`
   - The native application hardcodes an HTTP POST directly to Bing's visual search server and triggers Microsoft Edge via `Windows.System.Launcher.LaunchUriAsync`. There is no configuration option or registry flag to alter this target.

2. **Google Lens Web API Interfacing:**
   - Captured images are transmitted via `multipart/form-data` with the `encoded_image` parameter to `https://lens.google.com/v3/upload`.
   - The Google endpoint responds with an immediate **HTTP 303 See Other**, providing the visual search results URL (`https://www.google.com/search?vsrid=...`) in the `Location` header.
   - **Privacy Guarantee:** Images are transmitted over TLS directly to Google's official endpoints without passing through any third-party image hosting service (Imgur, Catbox, etc.).

---

## 📊 Comparison with Microsoft Snipping Tool

| Capability | Microsoft Snipping Tool | This Open-Source Tool |
| :--- | :---: | :---: |
| **Visual Search Provider** | ❌ Bing Only (Locked) | ✅ **Google Lens (Direct)** |
| **AI Multi-Image Combiner** | ❌ Not available | ✅ **Vertical, Horizontal, 2×2 Grid** |
| **AI Reference Badges `[1]`, `[2]`** | ❌ Not available | ✅ **Automatic Numbered Badges** |
| **System Protocol Override** | Default UWP | ✅ **Native `ms-screenclip:` Handler** |
| **Hardware Audio Video Recording** | Basic | ✅ **Mic + System Loopback Audio** |
| **PrtScn Global Interception** | Default Windows hook | ✅ **Sub-20ms Suppressed Hook** |
| **Single-Instance IPC Daemon** | UWP Process | ✅ **Local Loopback Socket IPC** |
| **Source Code & Customization** | ❌ Proprietary | ✅ **100% Open Source (MIT)** |

---

## 🚀 Installation & Quick Start

### 1. Prerequisites
- Windows 11 or Windows 10 (64-bit)
- Python 3.10 or higher

### 2. Clone the Repository
```bash
git clone https://github.com/benmeric/snipping-tool.git
cd snipping-tool
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Launch Application
- **Standard UI Launch:**
  ```bash
  python main.py
  ```
  *(or double-click `Start.bat` / `SnippingTool.bat`)*

- **Silent Background Launch (System Tray):**
  Double-click `StartBackground.vbs` to run silently in the background without opening a terminal window.

---

## ⚡ Windows System Integration

To set this tool as your default screen capture utility:
1. Open the application and navigate to **Settings** (`Ctrl + ,` or click the `...` menu).
2. Under **Shortcuts & System**, toggle **Set as Default Snipping Tool** to **ON**.
3. Toggle **Start with Windows** to **ON** to ensure the tool is ready immediately upon logging into Windows.
4. Click **Add to Desktop** to place a branded shortcut on your desktop.

> **How it works:**  
> The tool registers itself in `HKEY_CURRENT_USER\Software\Classes\ms-screenclip` and `RegisteredApplications`. When `PrtScn`, `Win+Shift+S`, or a hardware pen button triggers a screen clip, Windows delegates the event to this application. If an instance is already running, an IPC signal triggers the capture overlay in under 20 milliseconds without spinning up redundant processes.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| **`PrtScn`** or **`Win + Shift + S`** | Take a screen snip (Rectangle, Window, Full Screen, Freeform) |
| **`Ctrl + Shift + S`** | Take a photo snip |
| **`Ctrl + Shift + R`** | Start area screen video recording |
| **`Ctrl + G`** | Search current capture in Google Lens |
| **`Ctrl + C`** | Copy capture to clipboard |
| **`Ctrl + S`** | Save image to disk |
| **`Ctrl + Z`** | Undo drawing action |
| **`Ctrl + ,`** | Open Settings panel |
| **`+`** or **`Numpad +`** | Trigger new snip or recording |
| **`ESC`** | Cancel active overlay |

---

## ⚙️ Configuration (`config.json`)

Settings can be customized directly in the graphical UI or by modifying `config.json`:

```json
{
    "app_theme": "dark",
    "app_language": "en",
    "google_lens_enabled": true,
    "is_default_snipper": true,
    "intercept_print_screen": true,
    "auto_copy_snip": true,
    "auto_save_snip": true,
    "snip_filename_prefix": "Screenshot",
    "record_mic_default": false,
    "record_system_audio_default": true,
    "add_border": false,
    "hdr_color_fix": false,
    "play_sound": true,
    "show_toast_notification": true
}
```

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

Developed with ❤️ by **Meriç Yüzaklı**

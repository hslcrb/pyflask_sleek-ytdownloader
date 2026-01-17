# Sleek Downloader

<p align="center">
  <img src="static/images/logo.png" alt="Sleek Logo" width="150" height="auto">
</p>

<p align="center">
  <strong>Pure. Potent. Permanent.</strong><br>
  The last media archiver designed for the uncompromising perfectionist.
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License"></a>
  <img src="https://img.shields.io/badge/Python-3.12%2B-blue" alt="Python Version">
  <img src="https://img.shields.io/badge/Flask-3.0%2B-lightgrey" alt="Flask">
</p>

---
[English](README.md) | [한국어](README_ko.md)
---

## 📖 Introduction

**Sleek** is a modern, minimalist YouTube downloader and media archiver. Built with **Flask** and powered by the robust **yt-dlp** engine, it wraps powerful functionality in a stunning, high-performance Glassmorphism UI.

Sleek is designed for those who value **aesthetics**, **privacy**, and **control**.

### ✨ Key Features

- **💎 Glassmorphism Design**: A beautiful, translucent user interface that blends with your system theme.
- **🌗 Adaptive Theming**: Automatically syncs with your system's Light/Dark mode, with a manual toggle.
- **🚀 8K Ready**: Supports extracting the highest possible quality video (up to 8K HDR) and lossless audio.
- **🔒 Privacy First**: All processing happens locally. No external servers, no tracking, complete data sovereignty.
- **📂 Smart Automation**: Remembers your preferred download paths and optimizes file formats automatically.
- **⚡ Async Processing**: Non-blocking download streams for a responsive experience.

## 🛠️ Technology Stack

- **Backend**: Python 3.12+, Flask
- **Core Engine**: yt-dlp
- **Frontend**: HTML5, Vanilla JS, CSS3 (Variables, Flexbox/Grid, Backdrop Filter)
- **License**: Apache 2.0

## 🚀 Installation & Setup

### 1. Simple Run (Pre-built Executables) - **Recommended**
The easiest way to use Sleek is to download the pre-built executable for your operating system:
1. Go to the [Releases](https://github.com/hslcrb/pyflask_sleek-ytdownloader/releases) page.
2. Download the `.zip` file for your OS (Windows, Linux, or macOS).
3. Extract the zip file.
4. Run the `SleekDownloader` executable.
5. Your browser will NOT open automatically; please navigate to `http://localhost:5000`.

### 2. Run via Docker
Sleek is available as a Docker image on GitHub Packages:
```bash
docker pull ghcr.io/hslcrb/pyflask_sleek-ytdownloader:latest
docker run -p 5000:5000 ghcr.io/hslcrb/pyflask_sleek-ytdownloader:latest
```
Navigate to `http://localhost:5000`.

### 3. Run from Source (For Developers)

#### Prerequisites
- Python 3.8 or higher
- **FFmpeg**: Required for merging video and audio streams.
- **python3-tk**: Required for the folder selection dialog on Linux (`sudo apt-get install python3-tk`).

#### Steps
1. **Clone the repository**
   ```bash
   git clone https://github.com/hslcrb/pyflask_sleek-ytdownloader.git
   cd pyflask_sleek-ytdownloader
   ```

2. **Run the start script** (Linux/macOS)
   ```bash
   ./start_server.sh
   ```

3. **Manual Setup**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python app.py
   ```

4. **Access the App**
   Open your browser and navigate to `http://localhost:5000`.

## 🤝 Contributing

Contributions are welcome! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---
<p align="center">
  © 2026 Rhee Creative. Crafted with passion.
</p>

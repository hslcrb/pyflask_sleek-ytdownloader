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

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- FFmpeg (required for merging video and audio streams)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/hslcrb/pyflask_sleek-ytdownloader.git
   cd pyflask_sleek-ytdownloader
   ```

2. **Run the start script** (Linux/macOS)
   This script will automatically set up a virtual environment, install dependencies, and start the server.
   ```bash
   ./start_server.sh
   ```

3. **Manual Install** (Windows/Alternative)
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   python app.py
   ```

4. **Open in Browser**
   Navigate to `http://localhost:5000` to experience Sleek.

## 🤝 Contributing

Contributions are welcome! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---
<p align="center">
  © 2026 RheeWorks. Crafted with passion.
</p>

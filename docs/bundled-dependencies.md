# Bundled tools and corresponding source

Sleek uses separate tool executables for media extraction, JavaScript and processing. They remain separately licensed. The Sleek code is Apache-2.0.

| Tool | Distribution and source | Notes |
| --- | --- | --- |
| Electron 45.4.1 | [Upstream release and source](https://github.com/electron/electron/releases/tag/v45.4.1) | GUI only. The upstream Electron license and Chromium third-party notices ship at the root of each desktop payload. |
| yt-dlp 2026.10.26 | [Release and source](https://github.com/yt-dlp/yt-dlp/releases/tag/2026.10.26), [binary licensing](https://github.com/yt-dlp/yt-dlp/tree/2026.10.26#licensing) | Official Linux x64 and Windows x64 standalone executables; see the upstream release for bundled dependency and PyInstaller terms. |
| Deno 2.9.8 | [Official release and source](https://github.com/denoland/deno/releases/tag/v2.9.8), [license](https://github.com/denoland/deno/blob/v2.9.8/LICENSE.md) | Runs as a subprocess when yt-dlp needs a JavaScript runtime. |
| FFmpeg / FFprobe 8.1.3 | [Upstream licensing](https://ffmpeg.org/legal.html), [matching source and recipe asset](https://github.com/hslcrb/pyflask_sleek-ytdownloader/releases/download/v2.0.0-rc.2/Sleek-FFmpeg-LAME-Source-v2.0.0-rc.2.tar.gz) | LGPL 2.1 or later. GPL and nonfree features and library autodetection disabled. |
| LAME 3.100 | Same matching source and recipe asset. [Upstream](https://lame.sourceforge.io/) | LGPL library used by FFmpeg's MP3 encoder. |

No changes are applied to the FFmpeg or LAME source archives. The matching asset contains the pinned source archives, their SHA-256 values in the build recipe, and the exact configure/build options. The tool directories include the applicable license files. Users can replace the tool executables independently, without relinking Sleek.

The FFmpeg build covers common media download, muxing, tag writing, and MP3 workflows; it is not a full video editing or transcoding suite. The Linux bundle targets modern glibc-based x64 distributions (glibc 2.39+), such as Debian 13 or Ubuntu 24.04. The Electron window requires the normal desktop system libraries and sandbox support; headless CLI use does not require a desktop.

Sleek Downloader | Windows x64 portable
======================================

Extract the entire ZIP into a writable folder. Double-click SleekDownloader.cmd.
It opens http://127.0.0.1:5000 in the default browser. Close the terminal or
press Ctrl+C to stop the server. No Python installation or administrator
account is required. The console stays open while the app is running.

The folder picker uses Windows PowerShell if Tcl/Tk is unavailable. If a
managed computer blocks it, enter the download path manually in the web UI.
For MP3 conversion or audio/video merging, install FFmpeg separately and add
it to PATH. Some supported websites may also require components documented
by yt-dlp. Download only media you have the right to save.

To verify bundled HTTP templates and assets without downloading media, run:
  SleekDownloader.cmd --smoke-test

The release ZIP contains signed upstream CPython binaries and hash-pinned
third-party wheels. The Sleek archive itself is not code-signed. See app/LICENSE,
runtime/LICENSE.txt and third-party license files in vendor/.

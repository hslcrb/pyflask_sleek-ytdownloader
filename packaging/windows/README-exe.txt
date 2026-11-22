Sleek Downloader | Windows x64
==============================

Setup: run the Setup.exe installer, then open Sleek Downloader from Start.
Portable ZIP: extract every file, then double-click SleekDownloader.exe.
No separate Python install is required. Your default browser opens the app
at http://127.0.0.1:5000. Close the terminal or press Ctrl+C to stop it.

To check the bundled HTTP routes without downloading media, run:
    SleekDownloader.exe --smoke-test

FFmpeg is needed separately for MP3 conversion and merging media streams.
Some sources may also require the components documented by yt-dlp.
Download only media you have the right to save.

For the portable folder picker, Windows PowerShell may be required; you can
always enter the download path manually. The installer uses the local
user's profile, needs no admin install, and retains app/config.json when
uninstalling. Both Sleek executables are unsigned preview builds.

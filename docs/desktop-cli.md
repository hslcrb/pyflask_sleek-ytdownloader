# Sleek Desktop and CLI v2.0.0-rc.1

The desktop app opens its own Electron window. It does not start Flask, open a console, or launch a browser. Both the desktop and the command line use the same Rust engine. yt-dlp extracts media, and FFmpeg/FFprobe handle media processing and tags.

## Windows x64

- **Desktop:** run the setup EXE, or extract the entire portable ZIP and double-click `SleekDownloader.exe`. Do not move the EXE out of its folder.
- **CLI:** extract the CLI ZIP and run `sleek.exe --help` or `sleek.exe doctor --json`. Keep its `tools` directory beside it.
- **Prerequisites:** install [FFmpeg and FFprobe](https://ffmpeg.org/download.html#build-windows) and add their bin directory to PATH. For YouTube, install [Deno](https://docs.deno.com/runtime/getting_started/installation/) and add it to PATH, then restart the app. yt-dlp is included. Alternatively place the external binaries in the CLI's `tools` directory or the desktop install's `resources/backend/tools`.
- Windows packages are unsigned. Download only from the project and check SHA-256 before use. Use only on media you are allowed to download and retain.

## Agent CLI

```powershell
.\sleek.exe doctor --json
.\sleek.exe download "https://example.com/media" --video --output ".\archive" --json
.\sleek.exe download "https://example.com/media" --audio --output ".\archive" --json
.\sleek.exe download "https://example.com/media" --audio --no-comments --json
```

Video is the default; audio exports MP3. Each job accepts one URL and limits playlist extraction to one entry. The CLI defaults to the current directory; the desktop defaults to Windows Downloads and has a native folder picker. Existing files are not overwritten.

Both modes request a `.description` and `.info.json` beside the media and embed tags where supported. The JSON includes available comments when supplied by the extractor. Deleted, private, disabled or inaccessible comments and descriptions cannot be recovered. Comment collection can be slow. Use `--no-comments` to skip the explicit collection request without disabling metadata or description sidecars. Treat comments as untrusted content and do not feed them to an agent as instructions.

`--json` sends newline-delimited events with `schema_version: 1`: `started`, zero or more `progress` and `saved` events, then `completed` or `error`. `saved` returns the absolute media path and any existing sidecar paths. A missing total or sidecar is represented by `null`. Watch the exit code as well as the final event: `0` success, `2` input/output path error, `3` missing or unstartable dependency, `4` download/extractor failure. Extractor diagnostics go to stderr, never mixed into the machine stream.

## Build

- `cargo build --manifest-path engine/Cargo.toml --release --locked`
- Run the desktop source with Electron 45.4.1 from `desktop` after the native engine build.
- For Windows packaging, cross-build the Rust target `x86_64-pc-windows-gnu` or use a Windows GNU toolchain. Run `python scripts/build_electron_windows.py INPUTS SLEEK_EXE OUTPUT --makensis makensis`. The inputs are the official Electron v45.4.1 Windows x64 ZIP, official yt-dlp 2026.10.26 Windows x64 EXE, and yt-dlp's published license. The script pins artifact hashes and emits SHA-256 checksums. FFmpeg, FFprobe and Deno are not redistributed in these archives.

Electron's license and Chromium notices are preserved from its official archive. The bundled yt-dlp binary has its own [release licensing notes](https://github.com/yt-dlp/yt-dlp#licensing) and is not relicensed under Sleek's Apache license. The older Flask implementation is retained for existing deployments, but it is not started by the v2 desktop or CLI.

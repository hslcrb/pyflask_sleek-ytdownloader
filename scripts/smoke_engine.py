#!/usr/bin/env python3
"""Exercise the real Rust/yt-dlp/FFmpeg pipeline on a self-generated clip."""
import argparse
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from threading import Thread


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("engine", type=Path)
    parser.add_argument("--bundled", action="store_true", help="Run the engine with an empty PATH, using only its bundled tools")
    args = parser.parse_args()
    engine_env = {**os.environ, "PATH": os.devnull} if args.bundled else None
    engine = args.engine.resolve()
    with TemporaryDirectory() as temp:
        root = Path(temp)
        clip = root / "sample.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=s=160x90:r=15:d=1",
                        "-f", "lavfi", "-i", "sine=frequency=500:duration=1",
                        "-c:v", "libx264", "-c:a", "aac", "-shortest", str(clip)], check=True)
        (root / "index.html").write_text(
            '<!doctype html><title>Sleek test</title><meta property="og:description" content="Generated fixture">'
            '<video controls src="/sample.mp4"></video>', encoding="utf-8")
        handler = functools.partial(SimpleHTTPRequestHandler, directory=root)
        with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
            Thread(target=server.serve_forever, daemon=True).start()
            url = f"http://127.0.0.1:{server.server_port}/index.html"
            for mode, suffix in [("video", ".mp4"), ("audio", ".mp3")]:
                result = subprocess.run([str(engine), "download", url, "--" + mode, "--output",
                                         str(root / mode), "--json"], capture_output=True, text=True, timeout=35, env=engine_env)
                assert result.returncode == 0, (result.stdout, result.stderr)
                events = [json.loads(line) for line in result.stdout.splitlines()]
                saved = next(e for e in events if e["event"] == "saved")
                assert events[0]["event"] == "started" and events[-1]["event"] == "completed", events
                assert Path(saved["path"]).suffix == suffix
                assert Path(saved["info_json"]).is_file()
                assert Path(saved["description"]).read_text().strip() == "Generated fixture", saved
                assert saved["comments_requested"] is True
                tags = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format_tags",
                                                "-of", "json", saved["path"]], text=True)
                assert "Sleek test" in tags, tags
                print(f"{mode}: media, info JSON, description and embedded title verified")
            server.shutdown()


if __name__ == "__main__":
    main()

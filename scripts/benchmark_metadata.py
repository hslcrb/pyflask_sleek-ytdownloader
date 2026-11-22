#!/usr/bin/env python3
"""Compare the pinned original /api/info code with the working checkout."""

import argparse
from pathlib import Path
import runpy
from statistics import median
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import perf_counter, sleep
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import yt_dlp


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", default="c9c93dd5131d8f6f9f5cca0425084af303d4b65b")
    parser.add_argument("--requests", default=20, type=int)
    parser.add_argument("--extract-ms", default=25, type=float)
    args = parser.parse_args()
    if args.requests < 1 or args.extract_ms < 0:
        parser.error("requests must be positive and extract-ms nonnegative")

    urls = ["https://example.test/one"] * args.requests
    formats = [
        {"format_id": str(i), "height": [360, 480, 720, 1080, 1440, 2160][i % 6],
         "vcodec": "av1", "ext": "webm"}
        for i in range(180)
    ]

    def execute(entry, home, requests, delay):
        calls = 0

        def fake_extract(*unused_args, **unused_kwargs):
            nonlocal calls
            calls += 1
            if delay:
                sleep(delay / 1000)
            return {"title": "Synthetic", "duration": 63, "formats": formats}

        # Redirect all original and updated config I/O into scratch space.
        with patch.object(Path, "home", return_value=home), \
                patch.object(yt_dlp, "YoutubeDL") as ydl, \
                patch("builtins.open", side_effect=isolated_open(home)):
            ydl.return_value.__enter__.return_value.extract_info.side_effect = fake_extract
            app = runpy.run_path(str(entry))["app"]
            client = app.test_client()
            t0 = perf_counter()
            results = [client.post("/api/info", json={"url": url}) for url in requests]
            elapsed = (perf_counter() - t0) * 1000
            assert all(r.status_code == 200 for r in results)
            return calls, elapsed, [response.get_json() for response in results]

    def isolated_open(home):
        real_open = open

        def redirect(file, *args, **kwargs):
            if isinstance(file, (str, Path)) and Path(file).name == "config.json":
                file = home / "config.json"
            return real_open(file, *args, **kwargs)
        return redirect

    with TemporaryDirectory() as directory:
        home = Path(directory)
        original = home / "baseline_app.py"
        original.write_bytes(subprocess.check_output(["git", "show", f"{args.baseline}:app.py"], cwd=ROOT))
        current = ROOT / "app.py"
        for label, requests, delay in (
            ("same URL", urls, args.extract_ms),
            ("different URLs", [url + str(i) for i, url in enumerate(urls)], 0),
        ):
            runs = {original: [], current: []}
            for i in range(9):
                order = (original, current) if i % 2 == 0 else (current, original)
                outputs = {}
                for path in order:
                    calls, elapsed, response = execute(path, home, requests, delay)
                    runs[path].append((calls, elapsed))
                    outputs[path] = response
                assert outputs[original] == outputs[current]
            for name, path in (("baseline", original), ("candidate", current)):
                count = median(r[0] for r in runs[path])
                duration = median(r[1] for r in runs[path])
                print(f"{label:14} {name:10} {count:>3} extractor calls / "
                      f"{duration:>8.2f} ms median for {len(requests)} requests")


if __name__ == "__main__":
    main()

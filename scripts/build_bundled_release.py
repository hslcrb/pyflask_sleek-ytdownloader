#!/usr/bin/env python3
"""Assemble x64 desktop/CLI packages with all four tools and matching FFmpeg/LAME sources."""
import argparse
import gzip
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
import tempfile
from zipfile import ZipFile

from build_electron_windows import check, digest, windows_x64, zip_package
from build_windows_exe import payload_manifest

ROOT = Path(__file__).resolve().parents[1]
VERSION = "v2.0.0-rc.2"
PINS = {
    "electron-v45.4.1-win32-x64.zip": "2ba6223afa9121f42831fefe92c434334907540165294fc56697449d12e7cfe9",
    "electron-v45.4.1-linux-x64.zip": "e1d077c7a087d7e344350ea0c5cd2b7dc5af3d9bf7979474f38e0fc1a560b875",
    "yt-dlp.exe": "f5389d3698ecde4ef06f4e6b1ce0294fe9ac1396228c8990b8d3416d6d177a7d",
    "yt-dlp_linux": "767ba9dce7052aa196f8b12652f433d76de128ba168966fa84b6394d5e6c6795",
    "deno-x86_64-pc-windows-msvc.zip": "cba84b26e0df5ae7f74fc66b86a95b866872a86292ebd84fa1e959927edd93bf",
    "deno-x86_64-unknown-linux-gnu.zip": "e890975bc2549807bbcc0b584ffafda72cc7c93349dd99c80483dd784f6c4609",
    "DENO-LICENSE": "f62497fffecc0852960c8d3e6934b9db86d16396e9b604072e923892cae3a588",
    "yt-dlp-LICENSE": "7e12e5df4bae12cb21581ba157ced20e1986a0508dd10d0e8a4ab9a4cf94e85c",
    "ffmpeg-8.1.3.tar.xz": "7138d28c96d9d3e3af4ee3d8cad72741f8ffb40da90c1112235dea3ecd3178a3",
    "lame_3.100.orig.tar.gz": "ddfe36cab873794038ae2c1210557ad34857a4b6bdc515785d1da9e175b1da1e",
}


def electron_extract(source, dest):
    with ZipFile(source) as archive:
        for member in archive.infolist():
            entry = PurePosixPath(member.filename)
            if entry.is_absolute() or ".." in entry.parts or "\\" in member.filename:
                raise ValueError("Unsafe path in Electron distribution")
            path = Path(archive.extract(member, dest))
            if path.is_file():
                archive_mode = (member.external_attr >> 16) & 0o777
                path.chmod((archive_mode & 0o111) | 0o644)


def tgz(root, dest):
    def metadata(info):
        info.uid = info.gid = info.mtime = 0
        info.uname = info.gname = ""
        return info

    with dest.open("xb") as raw, gzip.GzipFile(fileobj=raw, filename="", mode="wb", mtime=0, compresslevel=4) as g, \
         tarfile.open(fileobj=g, mode="w", format=tarfile.PAX_FORMAT) as archive:
        archive.add(root, arcname=root.name, filter=metadata)


def install_script(work, gui, target, makensis):
    for f in gui.rglob("*"):
        if f.is_file():
            os.utime(f, (946684800, 946684800))
    manifest = work / "payload.nsh"
    payload_manifest(gui, manifest)
    source = (ROOT / "packaging/windows/installer.nsi").read_text()
    source = source.replace(r"Programs\SleekDownloader", r"Programs\SleekDesktop")
    source = source.replace(r"Uninstall\SleekDownloader", r"Uninstall\SleekDesktop")
    source = source.replace(r"\Sleek Downloader", r"\Sleek Desktop").replace(r"\Sleek Desktop.exe", r"\SleekDownloader.exe")
    source = source.replace("SetCompressor /SOLID lzma", "SetCompressor zlib")
    script = work / "installer.nsi"
    script.write_text(source)
    subprocess.run([makensis, "-WX", f"-DVERSION={VERSION[1:]}", f"-DOUTPUT={target}",
                    f"-DPAYLOAD={gui}", f"-DMANIFEST={manifest}", str(script)], check=True)
    windows_x64(target)


def make_payload(target, inputs, engine, work):
    win = target == "windows"
    ext = ".exe" if win else ""
    cli = work / "SleekCLI"
    tools = cli / "tools"
    tools.mkdir(parents=True)
    (tools / ".sleek-bundle").touch()
    dest = cli / f"sleek{ext}"
    shutil.copyfile(engine, dest)
    dl = "yt-dlp.exe" if win else "yt-dlp_linux"
    shutil.copyfile(inputs / dl, tools / f"yt-dlp{ext}")
    deno_zip = f"deno-x86_64-{'pc-windows-msvc' if win else 'unknown-linux-gnu'}.zip"
    with ZipFile(inputs / deno_zip) as archive:
        with (tools / f"deno{ext}").open("wb") as writer, archive.open(f"deno{ext}") as reader:
            shutil.copyfileobj(reader, writer)
    for file in ("ffmpeg" + ext, "ffprobe" + ext, "FFmpeg-LGPL-2.1.txt", "LAME-LICENSE.txt", "BUILD.txt"):
        shutil.copyfile(inputs / ("ff-windows" if win else "ff-linux") / file, tools / file)
    for file in ("yt-dlp-LICENSE", "DENO-LICENSE"):
        shutil.copyfile(inputs / file, tools / file)
    for file in (dest, *(tools.glob("*" + ext) if ext else (tools / n for n in ["deno", "ffmpeg", "ffprobe", "yt-dlp"]))):
        if win:
            windows_x64(file)
        else:
            file.chmod(0o755)
    shutil.copyfile(ROOT / "LICENSE", cli / "LICENSE")
    shutil.copyfile(ROOT / "docs/desktop-cli.md", cli / "README.md")
    shutil.copyfile(ROOT / "docs/bundled-dependencies.md", cli / "THIRD-PARTY.md")

    gui = work / "SleekDownloader"
    electron_extract(inputs / f"electron-v45.4.1-{'win32' if win else 'linux'}-x64.zip", gui)
    (gui / f"electron{ext}").rename(gui / f"SleekDownloader{ext}")
    if not win:
        for n in ("SleekDownloader", "chrome-sandbox", "chrome_crashpad_handler"):
            (gui / n).chmod(0o755)
    (gui / "resources/default_app.asar").unlink(missing_ok=True)
    app = gui / "resources/app"
    app.mkdir(parents=True)
    shutil.copyfile(ROOT / "desktop/package.json", app / "package.json")
    shutil.copytree(ROOT / "desktop/src", app / "src", ignore=shutil.ignore_patterns("*.test.cjs"))
    shutil.copytree(cli, gui / "resources/backend")
    shutil.copyfile(ROOT / "docs/desktop-cli.md", gui / "SLEEK-README.md")
    return cli, gui


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("inputs", "engine_linux", "engine_windows", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--makensis", required=True)
    args = parser.parse_args()
    for name, sha in PINS.items():
        check(args.inputs / name, sha)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    names = {
        "wc": f"SleekCLI-{VERSION}-Windows-x64.zip",
        "wg": f"SleekDesktop-{VERSION}-Windows-x64-Setup.exe",
        "lc": f"SleekCLI-{VERSION}-Linux-x64.tar.gz",
        "lg": f"SleekDesktop-{VERSION}-Linux-x64.tar.gz",
        "src": f"Sleek-FFmpeg-LAME-Source-{VERSION}.tar.gz",
    }
    sums = f"SHA256SUMS-{VERSION}.txt"
    if any((output / n).exists() for n in [*names.values(), sums]):
        parser.error("Refusing to overwrite existing release assets.")

    with tempfile.TemporaryDirectory(dir=output) as base:
        base = Path(base)
        for target, engine in (("linux", args.engine_linux), ("windows", args.engine_windows)):
            work = base / target
            cli, gui = make_payload(target, args.inputs, engine, work)
            if target == "linux":
                tgz(cli, base / names["lc"])
                tgz(gui, base / names["lg"])
            else:
                zip_package(cli, base / names["wc"])
                install_script(work, gui, base / names["wg"], args.makensis)
        src = base / "Sleek-media-tool-sources"
        src.mkdir()
        for name in ("ffmpeg-8.1.3.tar.xz", "lame_3.100.orig.tar.gz"):
            shutil.copyfile(args.inputs / name, src / name)
        shutil.copyfile(ROOT / "packaging/dependencies/build-ffmpeg.sh", src / "build-ffmpeg.sh")
        shutil.copyfile(ROOT / "docs/bundled-dependencies.md", src / "README.md")
        tgz(src, base / names["src"])
        for name in names.values():
            (base / name).rename(output / name)
    (output / sums).write_text("".join(f"{digest(output / name)}  {name}\n" for name in sorted(names.values())))


if __name__ == "__main__":
    main()

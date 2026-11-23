#!/usr/bin/env python3
"""Package Windows x64 Electron GUI and Rust CLI from checksum-pinned inputs."""
import argparse
import hashlib
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from build_windows_exe import payload_manifest

ROOT = Path(__file__).resolve().parents[1]
VERSION = "v2.0.0-rc.1"
ELECTRON = "electron-v45.4.1-win32-x64.zip"
ELECTRON_SHA = "2ba6223afa9121f42831fefe92c434334907540165294fc56697449d12e7cfe9"
YTDLP_SHA = "f5389d3698ecde4ef06f4e6b1ce0294fe9ac1396228c8990b8d3416d6d177a7d"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def check(path, sha):
    if digest(path) != sha:
        raise ValueError(f"Checksum mismatch: {path.name}")


def windows_x64(path):
    with path.open("rb") as stream:
        header = stream.read(64)
        if len(header) != 64 or header[:2] != b"MZ":
            raise ValueError(f"Not a PE executable: {path.name}")
        stream.seek(int.from_bytes(header[60:64], "little"))
        if stream.read(6) != b"PE\x00\x00\x64\x86":
            raise ValueError(f"Not x64: {path.name}")


def zip_package(root, output):
    with ZipFile(output, "x", compression=ZIP_DEFLATED, compresslevel=6) as target:
        for file in sorted(p for p in root.rglob("*") if p.is_file()):
            info = ZipInfo(file.relative_to(root.parent).as_posix())
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            with file.open("rb") as source, target.open(info, "w") as dest:
                shutil.copyfileobj(source, dest, 1024 * 1024)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", type=Path, help="Directory with official Electron ZIP, yt-dlp.exe and yt-dlp-LICENSE")
    parser.add_argument("engine", type=Path, help="Rust x64 Windows sleek.exe")
    parser.add_argument("output", type=Path)
    parser.add_argument("--makensis", help="Optional NSIS compiler; makes the desktop Setup.exe")
    args = parser.parse_args()

    check(args.inputs / ELECTRON, ELECTRON_SHA)
    check(args.inputs / "yt-dlp.exe", YTDLP_SHA)
    windows_x64(args.engine)
    args.output.mkdir(parents=True, exist_ok=True)
    output = args.output.resolve()
    gui_zip = output / f"SleekDownloader-Electron-{VERSION}-Windows-x64-Portable.zip"
    cli_zip = output / f"SleekCLI-{VERSION}-Windows-x64.zip"
    setup = output / f"SleekDownloader-Electron-{VERSION}-Windows-x64-Setup.exe"
    checksum = output / f"SHA256SUMS-{VERSION}.txt"
    outputs = [gui_zip, cli_zip] + ([setup] if args.makensis else [])
    if any(p.exists() for p in [*outputs, checksum]):
        parser.error("Refusing to overwrite an existing artifact")

    with tempfile.TemporaryDirectory(dir=output) as scratch:
        work = Path(scratch)
        cli = work / "SleekCLI"
        cli.mkdir()
        shutil.copyfile(args.engine, cli / "sleek.exe")
        tools = cli / "tools"
        tools.mkdir()
        for name in ("yt-dlp.exe", "yt-dlp-LICENSE"):
            shutil.copyfile(args.inputs / name, tools / name)
        shutil.copyfile(ROOT / "LICENSE", cli / "LICENSE")
        shutil.copyfile(ROOT / "docs" / "desktop-cli.md", cli / "README.md")

        gui = work / "SleekDownloader"
        with ZipFile(args.inputs / ELECTRON) as source:
            for member in source.infolist():
                p = PurePosixPath(member.filename)
                if p.is_absolute() or ".." in p.parts or "\\" in member.filename:
                    raise ValueError("Unsafe file path in Electron archive")
            source.extractall(gui)
        windows_x64(gui / "electron.exe")
        (gui / "electron.exe").rename(gui / "SleekDownloader.exe")
        (gui / "resources" / "default_app.asar").unlink(missing_ok=True)
        application = gui / "resources" / "app"
        application.mkdir(parents=True)
        shutil.copyfile(ROOT / "desktop" / "package.json", application / "package.json")
        shutil.copytree(ROOT / "desktop" / "src", application / "src", ignore=shutil.ignore_patterns("*.test.cjs"))
        shutil.copytree(cli, gui / "resources" / "backend")
        shutil.copyfile(ROOT / "docs" / "desktop-cli.md", gui / "SLEEK-README.md")

        zip_package(gui, work / gui_zip.name)
        zip_package(cli, work / cli_zip.name)
        if args.makensis:
            for file in gui.rglob("*"):
                if file.is_file():
                    os.utime(file, (946684800, 946684800))
            manifest = work / "uninstall-payload.nsh"
            payload_manifest(gui, manifest)
            definition = work / "installer.nsi"
            installer = (ROOT / "packaging" / "windows" / "installer.nsi").read_text(encoding="utf-8")
            installer = installer.replace(r"Programs\SleekDownloader", r"Programs\SleekDesktop")
            installer = installer.replace(r"Uninstall\SleekDownloader", r"Uninstall\SleekDesktop")
            installer = installer.replace(r"\Sleek Downloader", r"\Sleek Desktop").replace(r"\Sleek Desktop.exe", r"\SleekDownloader.exe")
            definition.write_text(installer, encoding="utf-8")
            subprocess.run([args.makensis, "-WX", f"-DVERSION={VERSION[1:]}", f"-DOUTPUT={work / setup.name}",
                            f"-DPAYLOAD={gui}", f"-DMANIFEST={manifest}", str(definition)], check=True)
            windows_x64(work / setup.name)
        for file in outputs:
            (work / file.name).rename(file)
    checksum.write_text("".join(f"{digest(f)}  {f.name}\n" for f in outputs), encoding="utf-8")


if __name__ == "__main__":
    main()

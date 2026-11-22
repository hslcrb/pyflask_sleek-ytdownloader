#!/usr/bin/env python3
"""Cross-build the native x64 launcher, per-user installer and portable ZIP."""

import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from build_windows_portable import PACKAGING, digest, stage


def payload_manifest(payload, manifest):
    """Uninstall only files listed at build time, then remove empty folders."""
    files = []
    directories = []
    for path in sorted(payload.rglob("*")):
        parts = path.relative_to(payload).parts
        if not all(re.fullmatch(r"[A-Za-z0-9_.+-]+", name) for name in parts):
            raise ValueError(f"Unexpected path in Windows package: {path}")
        (directories if path.is_dir() else files).append(parts)

    def windows_path(parts):
        return "$INSTDIR\\" + "\\".join(parts)

    lines = ["!macro RemovePayload"]
    lines.extend(f'    Delete "{windows_path(parts)}"' for parts in files)
    lines.extend(f'    RMDir "{windows_path(parts)}"'
                 for parts in sorted(directories, key=len, reverse=True))
    lines.append("!macroend")
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return files


def portable_zip(payload, output):
    with ZipFile(output, "x", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(p for p in payload.rglob("*") if p.is_file()):
            info = ZipInfo(path.relative_to(payload.parent).as_posix())
            info.external_attr = 0o100644 << 16
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, path.read_bytes(), compresslevel=9)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", type=Path)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("--zig", type=Path, default=Path("zig"))
    parser.add_argument("--makensis", type=Path, default=Path("makensis"))
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.]+)?", args.version):
        parser.error("expected a version like v1.2.0 or v1.2.0-rc.1")

    output = args.output_directory.resolve()
    output.mkdir(parents=True, exist_ok=True)
    name = f"SleekDownloader-{args.version}-Windows-x64"
    setup = output / f"{name}-Setup.exe"
    portable = output / f"{name}-Portable.zip"
    checksums = output / f"SHA256SUMS-{args.version}.txt"
    if any(p.exists() for p in (setup, portable, checksums)):
        parser.error("refusing to overwrite existing output")
    with TemporaryDirectory() as temp:
        temp = Path(temp)
        payload = temp / "SleekDownloader"
        stage(payload, args.inputs.resolve())
        (payload / "SleekDownloader.cmd").unlink()
        shutil.copyfile(PACKAGING / "README-exe.txt", payload / "README.txt")

        subprocess.run([
            str(args.zig), "cc", "-target", "x86_64-windows-gnu", "-municode",
            "-Os", "-s", "-Wall", "-Wextra", "-Werror", str(PACKAGING / "launcher.c"),
            "-luser32", "-o", str(payload / "SleekDownloader.exe"),
        ], check=True)

        # NSIS records file times inside the payload. Use a fixed timestamp.
        for file in payload.rglob("*"):
            if file.is_file():
                os.utime(file, (946684800, 946684800))

        manifest = temp / "uninstall-payload.nsh"
        payload_manifest(payload, manifest)
        staged_setup = temp / setup.name
        subprocess.run([
            str(args.makensis), "-WX", f"-DVERSION={args.version[1:]}", f"-DOUTPUT={staged_setup}",
            f"-DPAYLOAD={payload}", f"-DMANIFEST={manifest}", str(PACKAGING / "installer.nsi"),
        ], check=True)
        staged_portable = temp / portable.name
        portable_zip(payload, staged_portable)
        shutil.copyfile(staged_setup, setup)
        shutil.copyfile(staged_portable, portable)

    lines = [f"{digest(file)}  {file.name}" for file in (setup, portable)]
    with checksums.open("x", encoding="utf-8", newline="\n") as file:
        file.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

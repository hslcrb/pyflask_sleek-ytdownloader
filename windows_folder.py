"""Windows folder dialog fallback for the Python embeddable runtime (no Tcl/Tk)."""

import json
import os
from pathlib import Path
import subprocess


_DIALOG = r"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
Add-Type -AssemblyName System.Windows.Forms
$dialog = [System.Windows.Forms.FolderBrowserDialog]::new()
try {
    $dialog.Description = 'Select Download Folder'
    if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        ConvertTo-Json -InputObject $dialog.SelectedPath -Compress
    } else {
        'null'
    }
} finally { $dialog.Dispose() }
"""


def choose_windows_folder():
    program = (Path(os.environ.get("SystemRoot", r"C:\Windows")) /
               "System32/WindowsPowerShell/v1.0/powershell.exe")
    if not program.is_file():
        raise OSError("Windows PowerShell is unavailable.")
    result = subprocess.run(
        [str(program), "-NoProfile", "-STA", "-Command", _DIALOG],
        capture_output=True, encoding="utf-8", check=True, timeout=300,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    value = json.loads(result.stdout)
    if value is not None and not isinstance(value, str):
        raise ValueError("Unexpected folder dialog response.")
    return value

from importlib import import_module
from pathlib import Path
from subprocess import CompletedProcess
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch


class WindowsLauncherTests(TestCase):
    def test_folder_result_is_utf8_and_no_user_input_is_in_the_command(self):
        picker = import_module("windows_folder")
        with TemporaryDirectory() as temp:
            exe = Path(temp) / "System32/WindowsPowerShell/v1.0/powershell.exe"
            exe.parent.mkdir(parents=True)
            exe.touch()
            with patch.dict("os.environ", {"SystemRoot": temp}), patch.object(
                picker.subprocess, "run",
                return_value=CompletedProcess([], 0, '"C:\\\\저장"\n', ""),
            ) as run:
                self.assertEqual(picker.choose_windows_folder(), "C:\\저장")
                self.assertEqual(run.call_args.args[0][0], str(exe))
                self.assertEqual(run.call_args.kwargs["encoding"], "utf-8")
                self.assertNotIn("shell", run.call_args.kwargs)

    def test_folder_cancel_is_null(self):
        picker = import_module("windows_folder")
        with TemporaryDirectory() as temp:
            exe = Path(temp) / "System32/WindowsPowerShell/v1.0/powershell.exe"
            exe.parent.mkdir(parents=True)
            exe.touch()
            with patch.dict("os.environ", {"SystemRoot": temp}), patch.object(
                picker.subprocess, "run", return_value=CompletedProcess([], 0, "null\n", "")
            ):
                self.assertIsNone(picker.choose_windows_folder())

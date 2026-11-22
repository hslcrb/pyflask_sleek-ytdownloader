from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_windows_exe import payload_manifest


class InstallerManifestTests(TestCase):
    def test_manifest_removes_only_packaged_files_and_empty_directories(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            app = root / "packaged" / "app"
            (app / "static").mkdir(parents=True)
            (app / "launch.py").write_text("")
            (app / "static" / "favicon.png").touch()
            target = root / "manifest.nsh"
            payload_manifest(root / "packaged", target)
            text = target.read_text()
            self.assertIn(r'Delete "$INSTDIR\app\launch.py"', text)
            self.assertIn(r'RMDir "$INSTDIR\app\static"', text)
            self.assertNotIn("config.json", text)
            self.assertNotIn("RMDir /r", text)
            self.assertLess(text.index(r'RMDir "$INSTDIR\app\static"'),
                            text.index(r'RMDir "$INSTDIR\app"'))

    def test_rejects_manifest_paths_that_could_be_misread_by_nsis(self):
        with TemporaryDirectory() as temp:
            app = Path(temp) / "packaged"
            app.mkdir()
            (app / "$unexpected").touch()
            with self.assertRaisesRegex(ValueError, "Unexpected path"):
                payload_manifest(app, Path(temp) / "manifest.nsh")

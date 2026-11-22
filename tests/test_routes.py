from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import mock_open, patch

from metadata import MetadataCache

# The application initializes a download directory at import time. Keep this
# test away from the workstation's real Downloads and config.json.
with TemporaryDirectory() as sandbox, patch.object(Path, "home", return_value=Path(sandbox)), \
        patch("builtins.open", mock_open(read_data="{}")):
    import app as sleek

# Every request here uses a fake extractor. No media or network is accessed.
class RouteTests(TestCase):
    def setUp(self):
        self.client = sleek.app.test_client()

    def test_info_reuses_success_and_keeps_response_contract(self):
        with patch.object(sleek, "metadata_cache", MetadataCache()), \
                patch.object(sleek, "extract_metadata", return_value={"title": "한글", "formats": []}) as extract:
            for url in ("https://example.test/video", " https://example.test/video "):
                self.assertEqual(self.client.post("/api/info", json={"url": url}).get_json(),
                                 {"title": "한글", "formats": []})
            extract.assert_called_once_with("https://example.test/video")

    def test_invalid_json_types_are_400_without_extracting(self):
        with patch.object(sleek, "extract_metadata") as extract:
            for payload in ([], {"url": 4}, {"url": " "}, {"url": "x" * 4097}):
                self.assertEqual(self.client.post("/api/info", json=payload).status_code, 400)
            self.assertEqual(self.client.post("/api/info", data="{", content_type="application/json").status_code, 400)
            extract.assert_not_called()

    def test_intro_does_not_load_the_download_app_script(self):
        response = self.client.get("/intro")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"/static/js/script.js", response.data)
        self.assertIn(b"/static/js/script.js", self.client.get("/").data)

    def test_favicon_has_the_declared_png_format_and_is_small(self):
        with self.client.get("/static/favicon.png") as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.mimetype, "image/png")
            self.assertTrue(response.data.startswith(b"\x89PNG\r\n\x1a\n"))
            self.assertLess(len(response.data), 12_000)

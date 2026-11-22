from concurrent.futures import Future, ThreadPoolExecutor
from threading import Event
from unittest import TestCase
from unittest.mock import patch

from metadata import MetadataCache, summarize


class MetadataTests(TestCase):
    def test_repeated_request_avoids_extraction_until_expiry(self):
        called = []
        now = [100]
        cache = MetadataCache(ttl=15, clock=lambda: now[0])

        def load():
            called.append(True)
            return {"title": "ok"}

        self.assertEqual(cache.get("url", load), cache.get("url", load))
        self.assertEqual(len(called), 1)
        now[0] += 15
        self.assertEqual(cache.get("url", load), {"title": "ok"})
        self.assertEqual(len(called), 2)

    def test_same_url_concurrent_and_failure_can_retry(self):
        cache = MetadataCache()
        entered, release, follower_entered = Event(), Event(), Event()

        def load():
            entered.set()
            if not release.wait(5):
                raise RuntimeError("test timed out")
            raise ValueError("extractor failed")

        class ObservedFuture(Future):
            def result(self, timeout=None):
                follower_entered.set()
                return super().result(timeout)

        with patch("metadata.Future", ObservedFuture), ThreadPoolExecutor(max_workers=2) as workers:
            leader = workers.submit(cache.get, "same", load)
            self.assertTrue(entered.wait(5))
            second = workers.submit(cache.get, "same", lambda: self.fail("duplicate extraction"))
            try:
                self.assertTrue(follower_entered.wait(5))
            finally:
                release.set()
            for result in (leader, second):
                with self.assertRaisesRegex(ValueError, "extractor failed"):
                    result.result(5)
        self.assertEqual(cache.get("same", lambda: "retry"), "retry")

    def test_bounded_lru(self):
        cache = MetadataCache(max_entries=2)
        cache.get("a", lambda: 1)
        cache.get("b", lambda: 2)
        cache.get("a", lambda: 4)
        cache.get("c", lambda: 3)
        self.assertEqual(cache.get("b", lambda: 5), 5)

    def test_summary_keeps_first_format_at_each_height(self):
        def fmt(key, height, codec="av1"):
            return {"format_id": key, "height": height, "vcodec": codec,
                    "ext": "webm", "filesize_approx": 100}

        result = summarize({"title": "한글", "duration": None, "formats": [
            fmt("first", 720), fmt("audio", 1440, "none"), fmt("second", 720),
            fmt("high", 1080), fmt("unknown", None),
        ]})
        self.assertEqual(result["duration"], "00:00")
        self.assertEqual([f["format_id"] for f in result["formats"]], ["high", "first"])

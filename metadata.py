"""Bounded, process-local cache for the public metadata response only."""

from collections import OrderedDict
from concurrent.futures import Future
from threading import Lock
from time import gmtime, monotonic, strftime


class MetadataCache:
    def __init__(self, *, max_entries=64, ttl=30, clock=monotonic):
        self._max_entries = max_entries
        self._ttl = ttl
        self._clock = clock
        self._entries = OrderedDict()
        self._pending = {}
        self._lock = Lock()

    def get(self, key, load):
        with self._lock:
            cached = self._entries.get(key)
            if cached:
                if self._clock() < cached[0]:
                    self._entries.move_to_end(key)
                    return cached[1]
                del self._entries[key]

            future = self._pending.get(key)
            is_leader = future is None
            if is_leader:
                future = self._pending[key] = Future()

        if not is_leader:
            return future.result()

        # Keep network/extractor work outside the lock so different URLs can overlap.
        try:
            value = load()
        except BaseException as error:
            with self._lock:
                del self._pending[key]
            future.set_exception(error)
            raise

        with self._lock:
            self._entries[key] = self._clock() + self._ttl, value
            if len(self._entries) > self._max_entries:
                self._entries.popitem(last=False)
            del self._pending[key]
        future.set_result(value)
        return value


def summarize(info):
    """Keep the first extractor-provided format per height, then rank heights."""
    by_height = {}
    for fmt in info.get("formats") or ():
        height = fmt.get("height")
        if height and fmt.get("vcodec") != "none" and height not in by_height:
            by_height[height] = {
                "format_id": fmt["format_id"],
                "height": height,
                "filesize": fmt.get("filesize") or fmt.get("filesize_approx"),
                "ext": fmt["ext"],
            }

    return {
        "title": info.get("title"),
        "thumbnail": info.get("thumbnail"),
        "duration": strftime("%M:%S", gmtime(info.get("duration") or 0)),
        "uploader": info.get("uploader"),
        "formats": [by_height[height] for height in sorted(by_height, reverse=True)],
    }

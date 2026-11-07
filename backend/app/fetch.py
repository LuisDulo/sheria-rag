"""Download official pages politely: identify ourselves, respect robots.txt, wait, and cache."""

import hashlib
import json
import ssl
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import httpx
import truststore

USER_AGENT = "SheriaRAG/0.1 (+https://github.com/LuisDulo/sheria-rag)"
MANIFEST = Path(__file__).parent.parent / "sources.json"
CACHE_DIR = Path(__file__).parent.parent / "data" / "raw"


@dataclass(frozen=True)
class Source:
    agency: str
    title: str
    url: str
    selector: str | None = None


def load_sources(path: Path = MANIFEST) -> list[Source]:
    return [Source(**entry) for entry in json.loads(path.read_text(encoding="utf-8"))]


class Fetcher:
    def __init__(
        self,
        client: httpx.Client | None = None,
        cache_dir: Path = CACHE_DIR,
        delay: float = 2.0,
    ):
        # The operating system's trust store completes chains that some government sites
        # serve incomplete, so certificates stay verified without special cases.
        self.client = client or httpx.Client(
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
            timeout=30,
            verify=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT),
        )
        self.cache_dir = cache_dir
        self.delay = delay
        self._robots: dict[str, RobotFileParser] = {}
        self._last_request = 0.0

    def _wait(self) -> None:
        remaining = self.delay - (time.monotonic() - self._last_request)
        if remaining > 0:
            time.sleep(remaining)
        self._last_request = time.monotonic()

    def _allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        host = f"{parts.scheme}://{parts.netloc}"
        if host not in self._robots:
            parser = RobotFileParser()
            self._wait()
            response = self.client.get(f"{host}/robots.txt")
            is_text = response.headers.get("content-type", "").startswith("text/plain")
            # A missing file, or a site's HTML error page, sets no rules.
            parser.parse(response.text.splitlines() if response.is_success and is_text else [])
            self._robots[host] = parser
        return self._robots[host].can_fetch(USER_AGENT, url)

    def get(self, url: str, refresh: bool = False) -> bytes:
        cached = self.cache_dir / hashlib.sha256(url.encode()).hexdigest()
        if cached.exists() and not refresh:
            return cached.read_bytes()
        if not self._allowed(url):
            raise PermissionError(f"robots.txt disallows {url}")
        self._wait()
        response = self.client.get(url)
        response.raise_for_status()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cached.write_bytes(response.content)
        return response.content

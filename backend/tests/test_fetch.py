import httpx
import pytest

from app.fetch import USER_AGENT, Fetcher, load_sources


def make_fetcher(tmp_path, robots, seen):
    def handler(request):
        seen.append(request)
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text=robots, headers={"content-type": "text/plain"})
        return httpx.Response(200, text="page")

    client = httpx.Client(
        transport=httpx.MockTransport(handler), headers={"User-Agent": USER_AGENT}
    )
    return Fetcher(client=client, cache_dir=tmp_path, delay=0)


def test_manifest_only_lists_official_https_sites():
    sources = load_sources()
    assert {source.agency for source in sources} == {"KRA", "SHA", "HELB"}
    assert all(
        source.url.startswith(("https://www.kra.go.ke", "https://www.sha.go.ke",
                               "https://www.helb.co.ke"))
        for source in sources
    )


def test_refuses_pages_blocked_by_robots(tmp_path):
    fetcher = make_fetcher(tmp_path, "User-agent: *\nDisallow: /private", [])
    with pytest.raises(PermissionError):
        fetcher.get("https://site.test/private/page")


def test_second_read_comes_from_the_cache(tmp_path):
    seen = []
    fetcher = make_fetcher(tmp_path, "", seen)
    assert fetcher.get("https://site.test/page") == b"page"
    assert fetcher.get("https://site.test/page") == b"page"
    assert [request.url.path for request in seen].count("/page") == 1


def test_sends_an_identifying_user_agent(tmp_path):
    seen = []
    make_fetcher(tmp_path, "", seen).get("https://site.test/page")
    assert all(request.headers["user-agent"] == USER_AGENT for request in seen)

import httpx

from app.fetch import Source
from app.ingest import ingest
from tests.fakes import FakeEmbedder

SOURCE = Source("KRA", "PAYE", "https://site.test/paye")


class StubFetcher:
    def __init__(self, page):
        self.page = page

    def get(self, url, refresh=False):
        if isinstance(self.page, Exception):
            raise self.page
        return self.page


def page(sentence):
    return f"<html><body><h2>Filing</h2><p>{sentence}</p></body></html>".encode()


FIRST = page("Employers must file and pay PAYE by the ninth of the next month.")
SECOND = page("Employers must file and pay PAYE on or before the ninth day of each month.")


def chunk_texts(conn):
    return [row[0] for row in conn.execute("SELECT content FROM chunks ORDER BY position")]


def test_adds_a_new_document(conn):
    totals = ingest(conn, [SOURCE], StubFetcher(FIRST), FakeEmbedder())
    assert totals["added"] == 1
    assert len(chunk_texts(conn)) == 1


def test_unchanged_document_is_not_embedded_again(conn):
    embedder = FakeEmbedder()
    ingest(conn, [SOURCE], StubFetcher(FIRST), embedder)
    totals = ingest(conn, [SOURCE], StubFetcher(FIRST), embedder)
    assert totals["unchanged"] == 1
    assert embedder.passages_embedded == 1


def test_changed_document_replaces_its_chunks(conn):
    ingest(conn, [SOURCE], StubFetcher(FIRST), FakeEmbedder())
    totals = ingest(conn, [SOURCE], StubFetcher(SECOND), FakeEmbedder())
    assert totals["updated"] == 1
    assert chunk_texts(conn) == [
        "Employers must file and pay PAYE on or before the ninth day of each month."
    ]


def test_document_dropped_from_the_manifest_is_removed(conn):
    ingest(conn, [SOURCE], StubFetcher(FIRST), FakeEmbedder())
    other = Source("KRA", "VAT", "https://site.test/vat")
    totals = ingest(conn, [other], StubFetcher(SECOND), FakeEmbedder())
    assert totals["removed"] == 1
    assert conn.execute("SELECT url FROM documents").fetchall() == [(other.url,)]


def test_failed_download_keeps_stored_chunks_and_continues(conn):
    ingest(conn, [SOURCE], StubFetcher(FIRST), FakeEmbedder())
    totals = ingest(conn, [SOURCE], StubFetcher(httpx.ConnectError("down")), FakeEmbedder())
    assert totals["failed"] == 1
    assert len(chunk_texts(conn)) == 1


def test_page_that_comes_back_empty_does_not_wipe_stored_chunks(conn):
    ingest(conn, [SOURCE], StubFetcher(FIRST), FakeEmbedder())
    totals = ingest(conn, [SOURCE], StubFetcher(b"<html><body></body></html>"), FakeEmbedder())
    assert totals["failed"] == 1
    assert len(chunk_texts(conn)) == 1

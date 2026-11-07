from app.extract import Chunk
from app.fetch import Source
from app.ingest import store
from app.retrieval import fuse, search
from tests.fakes import FakeEmbedder

PAGES = {
    "PAYE": "Employers deduct PAYE from employee salaries and remit it to KRA every month.",
    "VAT": "Value added tax is charged at sixteen percent on taxable goods and services.",
    "Rent": "Landlords pay monthly rental income tax on gross residential rent received.",
}


def load(conn):
    embedder = FakeEmbedder()
    for title, text in PAGES.items():
        source = Source("KRA", title, f"https://site.test/{title}")
        store(conn, source, [Chunk("", text)], embedder)
    return embedder


def titles(passages):
    return [passage.title for passage in passages]


def test_field_limits_search_to_one_agency(conn):
    embedder = load(conn)
    source = Source("HELB", "Loans", "https://site.test/loans")
    store(conn, source, [Chunk("", "Repay your student loan to HELB monthly.")], embedder)
    for mode in ("vector", "text", "hybrid"):
        assert titles(search(conn, embedder, "pay monthly", mode=mode, field="helb")) == ["Loans"]


def test_field_with_no_documents_returns_nothing(conn):
    embedder = load(conn)
    assert search(conn, embedder, "PAYE", field="sha") == []


def test_fuse_prefers_items_found_by_both_rankings():
    assert fuse([([1, 2, 3], 1.0), ([3, 4, 1], 1.0)], limit=2) == [1, 3]


def test_fuse_honours_the_limit():
    assert len(fuse([([1, 2, 3, 4], 1.0)], limit=2)) == 2


def test_fuse_lets_a_heavier_ranking_win():
    assert fuse([([1, 2], 1.0), ([2, 1], 0.1)], limit=1) == [1]
    assert fuse([([1, 2], 0.1), ([2, 1], 1.0)], limit=1) == [2]


def test_text_search_finds_an_exact_term(conn):
    embedder = load(conn)
    assert titles(search(conn, embedder, "What is PAYE?", mode="text"))[0] == "PAYE"


def test_text_search_matches_any_word_of_a_question(conn):
    embedder = load(conn)
    found = titles(search(conn, embedder, "do landlords need a zebra licence", mode="text"))
    assert found == ["Rent"]


def test_text_search_handles_a_question_of_only_stop_words(conn):
    embedder = load(conn)
    assert search(conn, embedder, "what is the", mode="text") == []


def test_vector_search_ranks_the_closest_passage_first(conn):
    embedder = load(conn)
    found = search(conn, embedder, "value added tax on goods and services", mode="vector")
    assert titles(found)[0] == "VAT"


def test_hybrid_search_returns_full_passages_with_their_source(conn):
    embedder = load(conn)
    passage = search(conn, embedder, "PAYE employers salaries", limit=1, mode="hybrid")[0]
    assert passage.title == "PAYE"
    assert passage.url == "https://site.test/PAYE"
    assert passage.content == PAGES["PAYE"]


def test_empty_database_returns_nothing(conn):
    assert search(conn, FakeEmbedder(), "PAYE") == []

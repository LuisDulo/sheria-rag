"""Find passages by meaning (pgvector) and by exact terms (full-text), then fuse the rankings."""

from dataclasses import dataclass
from typing import Literal

import psycopg

from app.embeddings import Embedder

Mode = Literal["vector", "text", "hybrid"]
Field = Literal["tax", "sha", "helb"]
FIELD_AGENCY: dict[str, str] = {"tax": "KRA", "sha": "SHA", "helb": "HELB"}
RRF_K = 60  # the constant from the original reciprocal rank fusion paper
TEXT_WEIGHT = 0.1  # the best hybrid weight in the benchmark; see the README


@dataclass
class Passage:
    id: int
    agency: str
    title: str
    url: str
    heading: str
    content: str


def vector_ranking(
    conn: psycopg.Connection, embedding, limit: int, agency: str | None = None
) -> list[int]:
    # The HNSW index is scanned before the agency filter applies, so it must look further
    # than its default or a small agency could come back with too few passages.
    conn.execute("SET LOCAL hnsw.ef_search = 400")
    rows = conn.execute(
        """
        SELECT c.id FROM chunks c JOIN documents d ON d.id = c.document_id
        WHERE %(agency)s::text IS NULL OR d.agency = %(agency)s
        ORDER BY c.embedding <=> %(embedding)s
        LIMIT %(limit)s
        """,
        {"agency": agency, "embedding": embedding, "limit": limit},
    ).fetchall()
    return [row[0] for row in rows]


def text_ranking(
    conn: psycopg.Connection, query: str, limit: int, agency: str | None = None
) -> list[int]:
    # plainto_tsquery requires every word to match, which almost no question satisfies.
    # Matching any word and ranking by relevance suits natural-language questions.
    rows = conn.execute(
        """
        WITH q AS (
            SELECT replace(plainto_tsquery('english', %(query)s)::text, '&', '|')::tsquery AS terms
        )
        SELECT c.id FROM chunks c JOIN documents d ON d.id = c.document_id, q
        WHERE c.search @@ q.terms AND (%(agency)s::text IS NULL OR d.agency = %(agency)s)
        ORDER BY ts_rank_cd(c.search, q.terms) DESC, c.id
        LIMIT %(limit)s
        """,
        {"query": query, "agency": agency, "limit": limit},
    ).fetchall()
    return [row[0] for row in rows]


def fuse(rankings: list[tuple[list[int], float]], limit: int) -> list[int]:
    """Weighted reciprocal rank fusion over (ranking, weight) pairs."""
    scores: dict[int, float] = {}
    for ranking, weight in rankings:
        for rank, chunk_id in enumerate(ranking, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + weight / (RRF_K + rank)
    return sorted(scores, key=lambda chunk_id: (-scores[chunk_id], chunk_id))[:limit]


def load_passages(conn: psycopg.Connection, ids: list[int]) -> list[Passage]:
    rows = conn.execute(
        """
        SELECT c.id, d.agency, d.title, d.url, c.heading, c.content
        FROM chunks c JOIN documents d ON d.id = c.document_id
        WHERE c.id = ANY(%s)
        """,
        (ids,),
    ).fetchall()
    by_id = {row[0]: Passage(*row) for row in rows}
    return [by_id[chunk_id] for chunk_id in ids if chunk_id in by_id]


def search(
    conn: psycopg.Connection,
    embedder: Embedder,
    query: str,
    limit: int = 6,
    mode: Mode = "vector",  # measured best on the benchmark; hybrid did not improve on it
    pool: int = 30,
    text_weight: float = TEXT_WEIGHT,
    field: Field | None = None,
) -> list[Passage]:
    agency = FIELD_AGENCY[field] if field else None
    rankings = []
    if mode in ("vector", "hybrid"):
        rankings.append((vector_ranking(conn, embedder.embed_query(query), pool, agency), 1.0))
    if mode in ("text", "hybrid"):
        rankings.append((text_ranking(conn, query, pool, agency), text_weight))
    return load_passages(conn, fuse(rankings, limit))

"""Find passages by meaning (pgvector) and by exact terms (full-text), then fuse the rankings."""

from dataclasses import asdict, dataclass
from typing import Literal

import psycopg

from app.embeddings import Embedder

Mode = Literal["vector", "text", "hybrid"]
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

    def to_dict(self) -> dict:
        return asdict(self)


def vector_ranking(conn: psycopg.Connection, embedding, limit: int) -> list[int]:
    rows = conn.execute(
        "SELECT id FROM chunks ORDER BY embedding <=> %s LIMIT %s", (embedding, limit)
    ).fetchall()
    return [row[0] for row in rows]


def text_ranking(conn: psycopg.Connection, query: str, limit: int) -> list[int]:
    # plainto_tsquery requires every word to match, which almost no question satisfies.
    # Matching any word and ranking by relevance suits natural-language questions.
    rows = conn.execute(
        """
        WITH q AS (
            SELECT replace(plainto_tsquery('english', %s)::text, '&', '|')::tsquery AS terms
        )
        SELECT id FROM chunks, q
        WHERE search @@ q.terms
        ORDER BY ts_rank_cd(search, q.terms) DESC, id
        LIMIT %s
        """,
        (query, limit),
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
) -> list[Passage]:
    rankings = []
    if mode in ("vector", "hybrid"):
        rankings.append((vector_ranking(conn, embedder.embed_query(query), pool), 1.0))
    if mode in ("text", "hybrid"):
        rankings.append((text_ranking(conn, query, pool), text_weight))
    return load_passages(conn, fuse(rankings, limit))

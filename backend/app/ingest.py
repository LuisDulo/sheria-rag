"""Load the official sources into PostgreSQL. Run with: python -m app.ingest [--refresh]"""

import argparse
import hashlib
import logging

import httpx
import psycopg

from app.db import apply_schema, connect
from app.embeddings import Embedder, get_embedder
from app.extract import Chunk, chunk_sections, extract_html, extract_pdf
from app.fetch import Fetcher, Source, load_sources

logger = logging.getLogger("sheria.ingest")


def parse(source: Source, data: bytes) -> list[Chunk]:
    if source.url.lower().endswith(".pdf"):
        return chunk_sections(extract_pdf(data))
    return chunk_sections(extract_html(data, source.selector))


def content_hash(chunks: list[Chunk]) -> str:
    joined = "\n".join(f"{chunk.heading}\t{chunk.content}" for chunk in chunks)
    return hashlib.sha256(joined.encode()).hexdigest()


def store(
    conn: psycopg.Connection, source: Source, chunks: list[Chunk], embedder: Embedder
) -> str:
    """Insert, replace or skip one document. Returns what happened."""
    digest = content_hash(chunks)
    existing = conn.execute(
        "SELECT id, content_hash FROM documents WHERE url = %s", (source.url,)
    ).fetchone()
    if existing and existing[1] == digest:
        return "unchanged"

    embeddings = embedder.embed_passages(
        [f"{source.title}. {chunk.heading}. {chunk.content}" for chunk in chunks]
    )
    with conn.transaction():
        document_id = conn.execute(
            """
            INSERT INTO documents (url, agency, title, content_hash) VALUES (%s, %s, %s, %s)
            ON CONFLICT (url) DO UPDATE SET
                agency = EXCLUDED.agency, title = EXCLUDED.title,
                content_hash = EXCLUDED.content_hash, fetched_at = now()
            RETURNING id
            """,
            (source.url, source.agency, source.title, digest),
        ).fetchone()[0]
        conn.execute("DELETE FROM chunks WHERE document_id = %s", (document_id,))
        with conn.cursor() as cursor:
            cursor.executemany(
                "INSERT INTO chunks (document_id, position, heading, content, embedding)"
                " VALUES (%s, %s, %s, %s, %s)",
                [
                    (document_id, position, chunk.heading, chunk.content, embedding)
                    for position, (chunk, embedding) in enumerate(
                        zip(chunks, embeddings, strict=True)
                    )
                ],
            )
    return "updated" if existing else "added"


def ingest(
    conn: psycopg.Connection,
    sources: list[Source],
    fetcher: Fetcher,
    embedder: Embedder,
    refresh: bool = False,
) -> dict[str, int]:
    """One unreachable or empty page must not stop the run or wipe what is already stored."""
    totals = {"added": 0, "updated": 0, "unchanged": 0, "failed": 0}
    removed = conn.execute(
        "DELETE FROM documents WHERE url <> ALL(%s)", ([source.url for source in sources],)
    ).rowcount
    conn.commit()
    totals["removed"] = removed
    for source in sources:
        try:
            chunks = parse(source, fetcher.get(source.url, refresh=refresh))
            if not chunks:
                raise ValueError("no text extracted")
            outcome = store(conn, source, chunks, embedder)
        except (httpx.HTTPError, PermissionError, ValueError) as error:
            logger.warning("Skipped %s: %s", source.url, error)
            outcome = "failed"
        else:
            logger.info("%s: %s (%d chunks)", outcome, source.title, len(chunks))
        totals[outcome] += 1
    return totals


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="download pages again")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    with connect() as conn:
        apply_schema(conn)
        totals = ingest(conn, load_sources(), Fetcher(), get_embedder(), args.refresh)
    logger.info("Done: %s", totals)


if __name__ == "__main__":
    main()

"""Measure retrieval against labelled questions. Run with: python -m app.evaluate"""

import json
from dataclasses import dataclass
from pathlib import Path

from app.db import connect
from app.embeddings import get_embedder
from app.main import PASSAGES
from app.retrieval import TEXT_WEIGHT, search

QUESTIONS = Path(__file__).parent.parent / "eval" / "questions.json"
TOP_K = PASSAGES
CONFIGURATIONS = [
    ("vector", {"mode": "vector"}),
    ("text", {"mode": "text"}),
    ("hybrid 1.0", {"mode": "hybrid", "text_weight": 1.0}),
    ("hybrid 0.5", {"mode": "hybrid", "text_weight": 0.5}),
    ("hybrid 0.25", {"mode": "hybrid", "text_weight": 0.25}),
    ("hybrid 0.1", {"mode": "hybrid", "text_weight": 0.1}),
]


@dataclass
class Scores:
    hit_at_1: float
    hit_at_k: float
    mrr: float


def first_rank(found: list[str], expected: str) -> int | None:
    """1-based position of the first passage from the expected document."""
    return next((rank for rank, title in enumerate(found, start=1) if title == expected), None)


def score(ranks: list[int | None]) -> Scores:
    total = len(ranks)
    return Scores(
        hit_at_1=sum(rank == 1 for rank in ranks) / total,
        hit_at_k=sum(rank is not None for rank in ranks) / total,
        mrr=sum(1 / rank for rank in ranks if rank) / total,
    )


def main() -> None:
    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    styles = sorted({item["style"] for item in questions})
    embedder = get_embedder()
    print(f"Top {TOP_K} passages. Default text weight: {TEXT_WEIGHT}\n")
    print(f"{'Questions':12}{'Search':13}{'Hit@1':>7}{f'Hit@{TOP_K}':>7}{'MRR':>7}")
    with connect() as conn:
        for style in [*styles, "all"]:
            subset = [item for item in questions if style in (item["style"], "all")]
            for name, options in CONFIGURATIONS:
                ranks = []
                for item in subset:
                    found = search(conn, embedder, item["question"], limit=TOP_K, **options)
                    ranks.append(first_rank([p.title for p in found], item["document"]))
                result = score(ranks)
                print(
                    f"{f'{style} ({len(subset)})':16}{name:13}"
                    f"{result.hit_at_1:7.2f}{result.hit_at_k:7.2f}{result.mrr:7.2f}"
                )
            print()


if __name__ == "__main__":
    main()

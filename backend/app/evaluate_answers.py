"""Test the local answers against expected facts. Run with: python -m app.evaluate_answers"""

import json
from pathlib import Path

from app.db import connect
from app.embeddings import get_embedder
from app.local_answer import local_answer
from app.main import PASSAGES
from app.retrieval import search

QUESTIONS = Path(__file__).parent.parent / "eval" / "answers.json"


def passes(item: dict, answer: str | None) -> bool:
    """An answer passes if it declines when it should, or contains every expected fact."""
    if item.get("declines"):
        return answer is None
    return answer is not None and all(
        fact.lower() in answer.lower() for fact in item["expect"]
    )


def main() -> None:
    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    embedder = get_embedder()
    passed = 0
    with connect() as conn:
        for item in questions:
            passages = search(
                conn, embedder, item["question"], limit=PASSAGES, field=item["field"]
            )
            answer = local_answer(item["question"], passages, embedder)
            ok = passes(item, answer)
            passed += ok
            print(f"{'PASS' if ok else 'FAIL'} [{item['field']}] {item['question']}")
            print(f"     {(answer or '(declined)')[:230]!r}")
    print(f"\n{passed} of {len(questions)} passed")


if __name__ == "__main__":
    main()

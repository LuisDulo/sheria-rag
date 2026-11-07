import json

import pytest

from app.evaluate import QUESTIONS, first_rank, score
from app.fetch import load_sources


def test_first_rank_finds_the_earliest_match():
    assert first_rank(["VAT", "PAYE", "PAYE"], "PAYE") == 2


def test_first_rank_is_none_when_missing():
    assert first_rank(["VAT"], "PAYE") is None


def test_score():
    result = score([1, 2, None, 4])
    assert result.hit_at_1 == 0.25
    assert result.hit_at_k == 0.75
    assert result.mrr == pytest.approx((1 + 0.5 + 0.25) / 4)


def test_every_question_is_labelled_with_a_real_document():
    titles = {source.title for source in load_sources()}
    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    assert {item["document"] for item in questions} <= titles

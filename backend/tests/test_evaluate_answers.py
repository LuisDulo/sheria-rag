import json

from app.evaluate_answers import QUESTIONS, passes


def test_answer_passes_when_it_contains_every_fact():
    assert passes({"expect": ["16%", "general"]}, "The General rate is 16%.")


def test_answer_fails_when_a_fact_is_missing():
    assert not passes({"expect": ["16%"]}, "The rate is 8%.")


def test_a_decline_fails_a_question_that_has_an_answer():
    assert not passes({"expect": ["16%"]}, None)


def test_declining_passes_when_it_should_decline():
    assert passes({"declines": True}, None)
    assert not passes({"declines": True}, "Here is an answer.")


def test_every_question_has_a_field_and_a_way_to_pass():
    for item in json.loads(QUESTIONS.read_text(encoding="utf-8")):
        assert item["field"] in {"tax", "sha", "helb"}
        assert item.get("declines") or item["expect"]

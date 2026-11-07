from app.local_answer import (
    ANSWER_SHAPE_WEIGHT,
    answer_shape_bonus,
    compose_answer,
    local_answer,
    split_sentences,
    word_overlap,
)
from app.retrieval import Passage
from tests.fakes import FakeEmbedder


def passage(content):
    return Passage(1, "KRA", "VAT", "u", "Rates", content)


def test_does_not_split_after_a_currency_abbreviation():
    text = "Turnover tax applies above Kshs. 1,000,000 in a single year of income."
    assert split_sentences(text) == [text]


def test_splits_ordinary_sentences():
    text = "The general rate is sixteen percent today. Exports are zero rated under the Act."
    assert len(split_sentences(text)) == 2


def test_drops_fragments_questions_and_links():
    text = (
        "details are complete and then submit the request. What is the rate of tax? "
        "Click here to download the approved list today. The rate of tax is sixteen percent."
    )
    assert split_sentences(text) == ["The rate of tax is sixteen percent."]


def test_replaces_typographic_characters():
    assert split_sentences("Employers\u2019 returns are due \u2014 file them on time.") == [
        "Employers' returns are due - file them on time."
    ]


def test_word_overlap_ignores_stop_words_and_endings():
    assert word_overlap("When do repayments start?", "Repayment starts soon") == 1.0


def test_when_questions_favour_sentences_about_timing():
    question = "When do I start repaying?"
    assert answer_shape_bonus(question, "Repayment starts within one year.") == ANSWER_SHAPE_WEIGHT
    assert answer_shape_bonus(question, "Seek clearance from the board.") == 0.0


def test_amount_questions_favour_sentences_with_figures():
    assert answer_shape_bonus("How much is the tax?", "It is 16%.") == ANSWER_SHAPE_WEIGHT
    assert answer_shape_bonus("How much is the tax?", "It depends.") == 0.0


def test_declines_when_nothing_is_close_enough():
    assert compose_answer([(0.9, 0.5, "A weak match.")]) is None
    assert compose_answer([]) is None


def test_keeps_only_sentences_near_the_best():
    scored = [(0.9, 0.8, "Best."), (0.88, 0.8, "Close."), (0.5, 0.8, "Far.")]
    assert compose_answer(scored) == "Best.\n\nClose."


def test_answers_from_a_matching_passage():
    text = "The standard rate of value added tax is sixteen percent on taxable goods."
    question = "standard rate of value added tax is sixteen percent on taxable goods"
    assert local_answer(question, [passage(text)], FakeEmbedder()) == text


def test_declines_an_unrelated_question():
    text = "The standard rate of value added tax is sixteen percent on taxable goods."
    assert local_answer("who won the football match", [passage(text)], FakeEmbedder()) is None


def test_declines_when_there_are_no_passages():
    assert local_answer("what is the rate", [], FakeEmbedder()) is None

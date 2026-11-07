"""Answer without a paid API: pick the sentences closest in meaning to the question."""

import re

import numpy as np

from app.answer import to_keyboard
from app.embeddings import Embedder
from app.retrieval import Passage

MIN_SIMILARITY = 0.70  # below this the pages do not cover the question; see the README
KEEP_WITHIN = 0.08  # also keep sentences this close to the best match
MAX_SENTENCES = 3
WORD_OVERLAP_WEIGHT = 0.15
ANSWER_SHAPE_WEIGHT = 0.2
TIME_QUESTION = re.compile(r"^when\b|how long|how soon|what date|which date|deadline")
TIME_ANSWER = re.compile(r"\b(within|on or before|by the|starts?|begins?)\b", re.IGNORECASE)
AMOUNT_QUESTION = re.compile(r"how much|what rate|what is the rate|percentage|how many")
AMOUNT_ANSWER = re.compile(r"\d|\b(two|three|four|five|six)\b", re.IGNORECASE)
NOT_ENDS = ["Kshs", "Ksh", "Kes", "KES", "No", "Nos", "Mr", "Mrs", "Dr", "Sec", "Cap", "Art"]
SENTENCE_END = re.compile(
    "".join(rf"(?<!\b{word}\.)" for word in NOT_ENDS) + r"(?<=[.!?])\s+(?=[A-Z(\"'])"
)
LIST_MARKER = re.compile(r"^(\(?[0-9a-z]{1,2}[.)]|[-*])\s+")
UNHELPFUL = re.compile(r"^(click|note:|read more|learn more)|click here", re.IGNORECASE)
STOP_WORDS = set(
    "a an and are at be by can do does for from get how i if in is it my of on or should that the "
    "their there to under was what when where which who why will with you your".split()
)


def split_sentences(text: str) -> list[str]:
    """Whole, readable sentences. Fragments left by chunk overlap start in lower case."""
    sentences = []
    for sentence in SENTENCE_END.split(to_keyboard(text)):
        sentence = LIST_MARKER.sub("", sentence.strip())
        sentence = re.sub(r"\s+\d{1,2}\.$", "", sentence)  # a list number left at the end
        readable = sentence[:1].isupper() and not sentence.endswith(("?", ":"))
        if readable and 5 <= len(sentence.split()) <= 70 and not UNHELPFUL.search(sentence):
            sentences.append(sentence)
    return sentences


def stems(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {re.sub(r"(ing|ed|es|s)$", "", word) or word for word in words} - STOP_WORDS


def word_overlap(question: str, sentence: str) -> float:
    wanted = stems(question)
    return len(wanted & stems(sentence)) / len(wanted) if wanted else 0.0


def answer_shape_bonus(question: str, sentence: str) -> float:
    """Similarity cannot tell that "when" wants a time, so reward sentences of the right shape."""
    asked = question.lower()
    if TIME_QUESTION.search(asked) and TIME_ANSWER.search(sentence):
        return ANSWER_SHAPE_WEIGHT
    if AMOUNT_QUESTION.search(asked) and AMOUNT_ANSWER.search(sentence):
        return ANSWER_SHAPE_WEIGHT
    return 0.0


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / ((np.linalg.norm(a) * np.linalg.norm(b)) or 1.0))


def score_sentences(
    question: str, passages: list[Passage], embedder: Embedder
) -> list[tuple[float, float, str]]:
    """(rank score, topic similarity, sentence), best first.

    Topic similarity includes the page title and heading, so it shows whether the pages cover
    the question at all. Ranking uses the sentence alone as well, because the title would
    otherwise lift every sentence on the right page equally.
    """
    contexts: dict[str, str] = {}
    for passage in passages:
        for sentence in split_sentences(passage.content):
            contexts.setdefault(sentence, f"{passage.title}. {passage.heading}. {sentence}")
    if not contexts:
        return []
    sentences = list(contexts)
    query = embedder.embed_query(question)
    plain = embedder.embed_passages(sentences)
    with_topic = embedder.embed_passages(list(contexts.values()))
    scored = []
    for sentence, plain_vector, topic_vector in zip(sentences, plain, with_topic, strict=True):
        topic = cosine(query, topic_vector)
        similarity = (cosine(query, plain_vector) + topic) / 2
        rank = (
            similarity
            + WORD_OVERLAP_WEIGHT * word_overlap(question, sentence)
            + answer_shape_bonus(question, sentence)
        )
        scored.append((rank, topic, sentence))
    return sorted(scored, key=lambda item: -item[0])


def compose_answer(scored: list[tuple[float, float, str]]) -> str | None:
    """Join the closest sentences, or return None when the pages do not cover the question."""
    if not scored or max(topic for _, topic, _ in scored) < MIN_SIMILARITY:
        return None
    best = scored[0][0]
    top = scored[:MAX_SENTENCES]
    chosen = [sentence for rank, _, sentence in top if rank >= best - KEEP_WITHIN]
    return "\n\n".join(chosen)


def local_answer(question: str, passages: list[Passage], embedder: Embedder) -> str | None:
    return compose_answer(score_sentences(question, passages, embedder))

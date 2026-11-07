import json

import pytest
from fastapi.testclient import TestClient

from app import main
from app.answer import NOT_COVERED
from app.embeddings import get_embedder
from app.main import answer_client, app
from app.retrieval import Passage
from tests.fakes import FakeEmbedder
from tests.test_answer import FakeClient

PASSAGE = Passage(1, "KRA", "PAYE", "https://x.test/paye", "Filing", "File by the 9th.")


def parse(body):
    events = []
    for block in body.strip().split("\n\n"):
        name, data = block.split("\n")
        events.append((name.removeprefix("event: "), json.loads(data.removeprefix("data: "))))
    return events


@pytest.fixture
def api(monkeypatch):
    monkeypatch.setattr(main, "find_passages", lambda question, field, embedder: [PASSAGE])
    app.dependency_overrides[get_embedder] = FakeEmbedder
    yield TestClient(app)
    app.dependency_overrides.clear()


def use_model(reply):
    app.dependency_overrides[answer_client] = lambda: reply


def test_streams_the_answer_then_done(api):
    use_model(FakeClient(["File by ", "the 9th."]))
    response = api.post("/api/chat", json={"question": "When is PAYE due?"})
    assert response.headers["content-type"].startswith("text/event-stream")
    events = parse(response.text)
    assert [name for name, _ in events] == ["delta", "delta", "done"]


def test_sources_are_not_sent_to_the_client(api):
    use_model(FakeClient(["File by the 9th."]))
    assert "x.test" not in api.post("/api/chat", json={"question": "When is PAYE due?"}).text


def test_without_a_key_it_still_answers(api, monkeypatch):
    monkeypatch.setattr(main, "local_answer", lambda q, p, e: "File returns by the ninth day.")
    use_model(None)
    events = parse(api.post("/api/chat", json={"question": "When is PAYE due?"}).text)
    assert "".join(data["text"] for name, data in events if name == "delta") == (
        "File returns by the ninth day."
    )
    assert events[-1] == ("done", {})


def test_without_a_key_it_declines_what_the_pages_do_not_cover(api, monkeypatch):
    monkeypatch.setattr(main, "local_answer", lambda q, p, e: None)
    use_model(None)
    events = parse(api.post("/api/chat", json={"question": "Who won the cup?"}).text)
    assert "".join(data["text"] for name, data in events if name == "delta") == NOT_COVERED


def test_model_failure_arrives_as_an_error_event(api):
    use_model(FakeClient(stop_reason="refusal"))
    events = parse(api.post("/api/chat", json={"question": "When is PAYE due?"}).text)
    assert events[-1][0] == "error"


def test_passes_the_chosen_field_to_search(api, monkeypatch):
    seen = []
    monkeypatch.setattr(main, "find_passages", lambda q, field, e: seen.append(field) or [PASSAGE])
    use_model(None)
    api.post("/api/chat", json={"question": "When is it due?", "field": "helb"})
    assert seen == ["helb"]


def test_rejects_an_unknown_field(api):
    use_model(None)
    response = api.post("/api/chat", json={"question": "When is it due?", "field": "land"})
    assert response.status_code == 422


@pytest.mark.parametrize("question", ["", "hi", "x" * 501])
def test_rejects_questions_of_the_wrong_length(api, question):
    use_model(None)
    assert api.post("/api/chat", json={"question": question}).status_code == 422

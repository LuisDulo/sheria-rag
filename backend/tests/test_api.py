import json

import pytest
from fastapi.testclient import TestClient

from app import main
from app.embeddings import get_embedder
from app.main import NO_KEY_NOTICE, answer_client, app
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
    monkeypatch.setattr(main, "find_passages", lambda question, embedder: [PASSAGE])
    app.dependency_overrides[get_embedder] = FakeEmbedder
    yield TestClient(app)
    app.dependency_overrides.clear()


def use_model(reply):
    app.dependency_overrides[answer_client] = lambda: reply


def test_streams_sources_then_answer_then_done(api):
    use_model(FakeClient(["File by the 9th ", "[1]."]))
    response = api.post("/api/chat", json={"question": "When is PAYE due?"})
    assert response.headers["content-type"].startswith("text/event-stream")
    events = parse(response.text)
    assert [name for name, _ in events] == ["sources", "delta", "delta", "done"]
    assert events[0][1][0]["url"] == "https://x.test/paye"
    assert events[-1][1] == {"cited": [1]}


def test_without_a_key_returns_the_passages(api):
    use_model(None)
    events = parse(api.post("/api/chat", json={"question": "When is PAYE due?"}).text)
    assert [name for name, _ in events] == ["sources", "notice", "done"]
    assert events[1][1] == {"message": NO_KEY_NOTICE}


def test_model_failure_arrives_as_an_error_event(api):
    use_model(FakeClient(stop_reason="refusal"))
    events = parse(api.post("/api/chat", json={"question": "When is PAYE due?"}).text)
    assert events[-1][0] == "error"


@pytest.mark.parametrize("question", ["", "hi", "x" * 501])
def test_rejects_questions_of_the_wrong_length(api, question):
    use_model(None)
    assert api.post("/api/chat", json={"question": question}).status_code == 422

import json
from collections.abc import Iterator
from typing import Annotated, Any

from fastapi import Depends, FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.answer import get_client, stream_answer
from app.config import get_settings
from app.db import connect
from app.embeddings import Embedder, get_embedder
from app.retrieval import Passage, search

NO_KEY_NOTICE = "Written answers are switched off, so here are the closest official passages."

app = FastAPI(title="Sheria RAG")


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


def find_passages(question: str, embedder: Embedder) -> list[Passage]:
    with connect() as conn:
        return search(conn, embedder, question)


def answer_client():
    """The Claude client, or None when no key is configured."""
    return get_client() if get_settings().anthropic_api_key else None


def sse(event: str, data: dict | list) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def chat_events(question: str, passages: list[Passage], client) -> Iterator[str]:
    yield sse("sources", [passage.to_dict() for passage in passages])
    if client is None:
        yield sse("notice", {"message": NO_KEY_NOTICE})
        yield sse("done", {"cited": list(range(1, len(passages) + 1))})
        return
    for event in stream_answer(question, passages, client):
        kind = event.pop("type")
        yield sse(kind, event)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat")
def chat(
    request: ChatRequest,
    embedder: Annotated[Embedder, Depends(get_embedder)],
    client: Annotated[Any, Depends(answer_client)],
) -> StreamingResponse:
    # Retrieval runs before the response starts, so a database failure is a clean 500
    # and no connection is held open while the model streams.
    passages = find_passages(request.question, embedder)
    return StreamingResponse(
        chat_events(request.question, passages, client),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

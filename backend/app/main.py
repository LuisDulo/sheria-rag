import json
import re
from collections.abc import Iterator
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import Depends, FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.answer import NOT_COVERED, get_client, stream_answer
from app.config import get_settings
from app.db import connect
from app.embeddings import Embedder, get_embedder
from app.local_answer import local_answer
from app.retrieval import Field as SearchField
from app.retrieval import Passage, search

PASSAGES = 12
WORDS_PER_DELTA = 3

@asynccontextmanager
async def lifespan(_: FastAPI):
    get_embedder()  # load the model now, so the first question is not slow
    yield


app = FastAPI(title="Sheria RAG", lifespan=lifespan)


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    field: SearchField | None = None


def find_passages(question: str, field: SearchField | None, embedder: Embedder) -> list[Passage]:
    with connect() as conn:
        return search(conn, embedder, question, limit=PASSAGES, field=field)


def answer_client():
    """The Claude client, or None when no key is configured."""
    return get_client() if get_settings().anthropic_api_key else None


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def local_events(question: str, passages: list[Passage], embedder: Embedder) -> Iterator[str]:
    """Send a local answer in small pieces, so it arrives the same way as a model's."""
    answer = local_answer(question, passages, embedder) or NOT_COVERED
    pieces = re.findall(r"\s*\S+", answer)
    for start in range(0, len(pieces), WORDS_PER_DELTA):
        yield sse("delta", {"text": "".join(pieces[start : start + WORDS_PER_DELTA])})
    yield sse("done", {})


def chat_events(
    question: str, passages: list[Passage], client, embedder: Embedder
) -> Iterator[str]:
    if client is None:
        yield from local_events(question, passages, embedder)
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
    passages = find_passages(request.question, request.field, embedder)
    return StreamingResponse(
        chat_events(request.question, passages, client, embedder),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

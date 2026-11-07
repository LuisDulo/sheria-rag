"""Local embeddings, so ingestion and search need no paid API."""

from functools import lru_cache
from typing import Protocol

import numpy as np

from app.config import get_settings


class Embedder(Protocol):
    def embed_passages(self, texts: list[str]) -> list[np.ndarray]: ...

    def embed_query(self, text: str) -> np.ndarray: ...


class LocalEmbedder:
    def __init__(self, model_name: str):
        from fastembed import TextEmbedding

        self.model = TextEmbedding(model_name=model_name)

    def embed_passages(self, texts: list[str]) -> list[np.ndarray]:
        return list(self.model.passage_embed(texts))

    def embed_query(self, text: str) -> np.ndarray:
        return next(iter(self.model.query_embed(text)))


@lru_cache
def get_embedder() -> Embedder:
    return LocalEmbedder(get_settings().embedding_model)

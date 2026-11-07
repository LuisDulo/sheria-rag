import hashlib
import re

import numpy as np


class FakeEmbedder:
    """Deterministic bag-of-words vectors, so tests need no model download."""

    def __init__(self):
        self.passages_embedded = 0

    def _vector(self, text: str) -> np.ndarray:
        vector = np.zeros(384, dtype=np.float32)
        for word in re.findall(r"[a-z0-9]+", text.lower()):
            vector[int(hashlib.sha256(word.encode()).hexdigest(), 16) % 384] += 1
        return vector / (np.linalg.norm(vector) or 1)

    def embed_passages(self, texts):
        self.passages_embedded += len(texts)
        return [self._vector(text) for text in texts]

    def embed_query(self, text):
        return self._vector(text)

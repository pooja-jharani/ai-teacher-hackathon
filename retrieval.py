"""
Lightweight RAG retrieval using TF-IDF + cosine similarity.

Why TF-IDF instead of a neural embedding model: it needs no model
download (works fully offline, no HuggingFace/OpenAI embedding calls
required), it's fast, and for grounding short lesson material it performs
well enough to keep the AI Teacher's answers tied to the uploaded content.
If you want higher-quality semantic retrieval and have an OpenAI key,
swap in `openai_embedding_retriever()` below -- the interface is the same.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ingest import Chunk


@dataclass
class RetrievedChunk:
    text: str
    source: str
    score: float


class TfidfRetriever:
    def __init__(self, chunks: List[Chunk]):
        self.chunks = chunks
        self.vectorizer = TfidfVectorizer(stop_words="english", max_features=20000)
        self.matrix = self.vectorizer.fit_transform([c.text for c in chunks]) if chunks else None

    def retrieve(self, query: str, top_k: int = 4) -> List[RetrievedChunk]:
        if not self.chunks or self.matrix is None:
            return []
        query_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(query_vec, self.matrix)[0]
        top_idx = np.argsort(sims)[::-1][:top_k]
        results = []
        for i in top_idx:
            if sims[i] <= 0:
                continue
            results.append(RetrievedChunk(text=self.chunks[i].text, source=self.chunks[i].source, score=float(sims[i])))
        return results


def build_retriever(chunks: List[Chunk]) -> TfidfRetriever:
    return TfidfRetriever(chunks)


def format_context(retrieved: List[RetrievedChunk]) -> str:
    """Formats retrieved chunks into a context block for the LLM prompt,
    with source tags so the model can (and should) ground its answer."""
    if not retrieved:
        return ""
    parts = []
    for i, r in enumerate(retrieved, 1):
        parts.append(f"[Source {i} | relevance={r.score:.2f}]\n{r.text}")
    return "\n\n".join(parts)

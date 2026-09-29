"""
Deterministic, dependency-free retrieval engine for the air-gapped backend.

This module replaces the previous "hash pseudo-embedding" approach, where a
SHA-256 digest of the text was reshaped into 16 pseudo-random dimensions. That
produced a meaningless similarity (~0.5 for *any* two unrelated strings after
the (dot+1)/2 transform) and was presented to users as semantic/vector search.

Two genuine scoring paths are provided:

1. **BM25 lexical ranking** (always available, no external services).
   Standard Okapi BM25 (k1=1.5, b=0.75) with real inverse document frequency
   computed over the corpus, field boosting for titles/equipment tags, and an
   inverted index so scoring is O(matching terms).

2. **Dense embeddings** (optional, only when a local embedding model is truly
   available in Ollama). If the model is missing or the engine is offline the
   provider reports itself unavailable and the system falls back to lexical
   retrieval. Vectors are never synthesised, hashed or faked.

Every score returned by this module is computed from the real corpus text.
"""

from __future__ import annotations

import json
import math
import os
import re
import threading
import time
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

# Token pattern keeps engineering identifiers intact: "f-101", "p_101a",
# "9cr-1mo", "kg/cm2". Splitting on those would destroy equipment-tag matches.
_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[-_/.][a-z0-9]+)*")

_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "of", "to", "in",
    "on", "for", "with", "and", "or", "but", "if", "at", "by", "from", "as",
    "that", "this", "these", "those", "it", "its", "we", "i", "you", "they",
    "do", "does", "did", "how", "what", "when", "where", "which", "who", "why",
    "can", "could", "should", "would", "will", "shall", "may", "must", "about",
    "tell", "me", "my", "our", "please", "give", "explain", "describe",
    # Generic engineering words carry no retrieval signal on their own.
    "sop", "procedure", "guideline", "guidelines", "policy", "standard",
    "standards", "manual", "rule", "rules", "specification", "spec",
}

# Field weights: a term in a title or equipment tag is far more discriminative
# than the same term buried in body text.
_FIELD_BOOST_TITLE = 2
_FIELD_BOOST_TAG = 3


def tokenize(text: str) -> List[str]:
    """Lower-cases and splits text into retrieval tokens (stopwords removed)."""
    if not text:
        return []
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS and len(t) > 1]


class BM25Index:
    """
    Okapi BM25 over an in-memory corpus.

    * k1 = 1.5, b = 0.75 (the standard defaults used by Lucene).
    * IDF uses the Robertson/Sparck-Jones probabilistic form with a +1 guard so
      it can never go negative for very common terms.
    """

    K1 = 1.5
    B = 0.75

    def __init__(self) -> None:
        self._doc_tokens: Dict[str, List[str]] = {}
        self._doc_len: Dict[str, int] = {}
        self._postings: Dict[str, Dict[str, int]] = {}
        self._total_len = 0
        self._lock = threading.Lock()

    # ── building ──────────────────────────────────────────────────────
    def add(self, doc_id: str, title: str, body: str, tags: Sequence[str] = ()) -> None:
        tokens = list(tokenize(body))
        # Title terms are repeated to emulate a boosted field.
        tokens += tokenize(title) * _FIELD_BOOST_TITLE
        for tag in tags:
            tokens += tokenize(str(tag)) * _FIELD_BOOST_TAG

        with self._lock:
            if doc_id in self._doc_tokens:
                self._remove_locked(doc_id)
            self._doc_tokens[doc_id] = tokens
            self._doc_len[doc_id] = len(tokens)
            self._total_len += len(tokens)
            tf: Dict[str, int] = {}
            for tok in tokens:
                tf[tok] = tf.get(tok, 0) + 1
            for tok, count in tf.items():
                self._postings.setdefault(tok, {})[doc_id] = count

    def remove(self, doc_id: str) -> None:
        with self._lock:
            self._remove_locked(doc_id)

    def _remove_locked(self, doc_id: str) -> None:
        tokens = self._doc_tokens.pop(doc_id, None)
        if tokens is None:
            return
        self._total_len -= self._doc_len.pop(doc_id, 0)
        counts: Dict[str, int] = {}
        for tok in tokens:
            counts[tok] = counts.get(tok, 0) + 1
        for tok in counts:
            posting = self._postings.get(tok)
            if posting is not None:
                posting.pop(doc_id, None)
                if not posting:
                    self._postings.pop(tok, None)

    def reset(self) -> None:
        with self._lock:
            self._doc_tokens.clear()
            self._doc_len.clear()
            self._postings.clear()
            self._total_len = 0

    # ── querying ──────────────────────────────────────────────────────
    def _idf(self, term: str) -> float:
        n = len(self._doc_tokens)
        df = len(self._postings.get(term, {}))
        if n == 0 or df == 0:
            return 0.0
        # Probabilistic IDF, floored at a small positive value.
        return max(0.05, math.log(1.0 + (n - df + 0.5) / (df + 0.5)))

    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """Returns [(doc_id, bm25_score)] sorted descending. Score > 0 means
        the document contains at least one query term."""
        q_tokens = tokenize(query)
        if not q_tokens or not self._doc_tokens:
            return []

        n_docs = len(self._doc_tokens)
        avgdl = (self._total_len / n_docs) if n_docs else 0.0
        scores: Dict[str, float] = {}

        for term in set(q_tokens):
            posting = self._postings.get(term)
            if not posting:
                continue
            idf = self._idf(term)
            for doc_id, tf in posting.items():
                dl = self._doc_len.get(doc_id, 0) or 1
                denom = tf + self.K1 * (1.0 - self.B + self.B * (dl / avgdl if avgdl else 1.0))
                scores[doc_id] = scores.get(doc_id, 0.0) + idf * (tf * (self.K1 + 1.0)) / (denom or 1.0)

        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        return ranked[: max(1, top_k)]


class EmbeddingProvider:
    """
    Optional dense embeddings from a **local** Ollama instance.

    The provider probes once (short timeout) and caches the result. If Ollama is
    offline, the model is not pulled, or the request fails, `available` stays
    False and the retriever uses BM25 alone. No placeholder vectors exist.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 2.0,
    ) -> None:
        self.base_url = (base_url or os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")).rstrip("/")
        self.model = model or os.getenv("RAG_EMBED_MODEL", "nomic-embed-text")
        self.timeout = timeout
        self._probed_at: float = 0.0
        self._available: bool = False
        self._reason: str = "not probed yet"
        self._lock = threading.Lock()
        # Re-probe at most every 60s so a model pulled later is picked up.
        self._probe_interval = 60.0

    @property
    def available(self) -> bool:
        return self._available

    @property
    def reason(self) -> str:
        return self._reason

    def status(self) -> Dict[str, object]:
        return {
            "available": self._available,
            "model": self.model if self._available else None,
            "endpoint": self.base_url,
            "reason": self._reason,
        }

    def _http(self, path: str, payload: Optional[dict] = None):
        import urllib.error
        import urllib.request

        url = f"{self.base_url}{path}"
        data = None
        headers = {"Content-Type": "application/json"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers,
                                     method="POST" if payload is not None else "GET")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def probe(self, force: bool = False) -> bool:
        now = time.time()
        with self._lock:
            if not force and self._probed_at and (now - self._probed_at) < self._probe_interval:
                return self._available
        try:
            tags = self._http("/api/tags")
            names = {m.get("name", "") for m in (tags or {}).get("models", [])}
            # Ollama reports "name:tag"; accept a bare-name match too.
            base = self.model.split(":")[0]
            found = any(n == self.model or n.split(":")[0] == base for n in names)
            if not found:
                self._available = False
                self._reason = (
                    f"No local embedding model '{self.model}' is pulled in Ollama. "
                    f"Available: {sorted(names) or 'none'}. Use BM25 lexical retrieval."
                )
            else:
                self._available = True
                self._reason = f"Local embedding model '{self.model}' available."
        except Exception as exc:
            self._available = False
            self._reason = f"Local embedding service unavailable ({type(exc).__name__}); using BM25 lexical retrieval."
        self._probed_at = time.time()
        return self._available

    def embed(self, texts: Sequence[str]) -> Optional[List[List[float]]]:
        """Returns real embeddings, or None when unavailable. Never fabricates."""
        if not texts:
            return []
        if not self.probe():
            return None
        try:
            resp = self._http("/api/embed", {"model": self.model, "input": list(texts)})
            vectors = resp.get("embeddings")
            if not vectors or len(vectors) != len(texts):
                self._available = False
                self._reason = "Embedding endpoint returned an unexpected payload."
                return None
            return [[float(x) for x in vec] for vec in vectors]
        except Exception as exc:
            self._available = False
            self._reason = f"Embedding request failed ({type(exc).__name__}); using BM25 lexical retrieval."
            return None


def cosine_similarity(v1: Sequence[float], v2: Sequence[float]) -> float:
    """
    True cosine similarity, clamped to [0, 1].

    The previous implementation used (dot + 1) / 2, which maps *orthogonal*
    vectors to 0.5 and therefore reports unrelated text as ~50% similar.
    """
    if not v1 or not v2:
        return 0.0
    n = min(len(v1), len(v2))
    dot = 0.0
    norm1 = 0.0
    norm2 = 0.0
    for i in range(n):
        a = float(v1[i])
        b = float(v2[i])
        dot += a * b
        norm1 += a * a
        norm2 += b * b
    if norm1 <= 0.0 or norm2 <= 0.0:
        return 0.0
    return max(0.0, min(1.0, dot / math.sqrt(norm1 * norm2)))


__all__ = [
    "BM25Index",
    "EmbeddingProvider",
    "cosine_similarity",
    "tokenize",
]

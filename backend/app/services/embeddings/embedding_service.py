import os
import math
import hashlib
import re
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.api.types import Documents, Embeddings
from app.core.config import settings

class ContinuumEmbeddingFunction(chromadb.EmbeddingFunction[Documents]):
    """
    Genuine Semantic Neural Embedding Engine powered by SentenceTransformers ('all-MiniLM-L6-v2').
    Produces 384-dimensional normalized dense vectors with real semantic clustering.
    Includes fallback to local deterministic vector transformation if neural model fails to load.
    """
    def __init__(self, dimension: int = 384, model_name: Optional[str] = None):
        self.dimension = dimension
        self.model_name = model_name or settings.EMBEDDING_MODEL or "all-MiniLM-L6-v2"
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                # Try local cached weights first for speed & offline reliability
                try:
                    self._model = SentenceTransformer(self.model_name, local_files_only=True)
                except Exception:
                    self._model = SentenceTransformer(self.model_name)
            except Exception as e:
                print(f"[EmbeddingService Warning] Could not load SentenceTransformer: {e}. Using local fallback.")
                self._model = False
        return self._model if self._model is not False else None

    def _generate_fallback_vector(self, text: str) -> List[float]:
        vec = [0.0] * self.dimension
        if not text:
            return vec

        cleaned = text.lower()
        words = re.findall(r'\b\w+\b', cleaned)
        if not words:
            return vec

        for i, word in enumerate(words):
            decay = 1.0 / (math.log2(i + 2))
            h_word = int(hashlib.sha256(word.encode('utf-8')).hexdigest(), 16)
            idx_w = h_word % self.dimension
            sign_w = 1.0 if ((h_word >> 8) & 1) else -1.0
            vec[idx_w] += 2.0 * decay * sign_w

            if len(word) >= 3:
                for k in range(len(word) - 2):
                    ngram = word[k:k+3]
                    h_ng = int(hashlib.md5(ngram.encode('utf-8')).hexdigest(), 16)
                    idx_ng = h_ng % self.dimension
                    sign_ng = 1.0 if ((h_ng >> 4) & 1) else -1.0
                    vec[idx_ng] += 0.8 * decay * sign_ng

        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            return [x / norm for x in vec]
        return vec

    def __call__(self, input: Documents) -> Embeddings:
        model = self._get_model()
        if model is not None:
            try:
                vectors = model.encode(list(input), normalize_embeddings=True)
                return [v.tolist() for v in vectors]
            except Exception as e:
                print(f"[EmbeddingService Inference Error] {e}. Using local fallback.")

        embeddings: List[List[float]] = []
        for doc in input:
            embeddings.append(self._generate_fallback_vector(doc))
        return embeddings

def get_embedding_function() -> ContinuumEmbeddingFunction:
    return ContinuumEmbeddingFunction()

import logging
from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    _instance: Optional["EmbeddingService"] = None
    _model: Optional[SentenceTransformer] = None
    _fallback_model: Optional[SentenceTransformer] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info(f"Loading embedding model: {settings.embedding_model}")
            self._model = SentenceTransformer(settings.embedding_model)
            logger.info("Embedding model loaded")
        return self._model

    @property
    def fallback_model(self) -> SentenceTransformer:
        if self._fallback_model is None:
            logger.info(f"Loading fallback embedding model: {settings.embedding_fallback_model}")
            self._fallback_model = SentenceTransformer(settings.embedding_fallback_model)
            logger.info("Fallback embedding model loaded")
        return self._fallback_model

    def embed(self, texts: list[str]) -> list[list[float]]:
        try:
            embeddings = self.model.encode(texts, show_progress_bar=False)
            return embeddings.tolist() if isinstance(embeddings, np.ndarray) else embeddings
        except Exception as e:
            logger.warning(f"Primary embedding failed ({e}), using fallback")
            embeddings = self.fallback_model.encode(texts, show_progress_bar=False)
            return embeddings.tolist() if isinstance(embeddings, np.ndarray) else embeddings

    def embed_query(self, text: str) -> list[float]:
        return self.embed([text])[0]

    @property
    def embedding_dimension(self) -> int:
        try:
            return self.model.get_embedding_dimension()
        except AttributeError:
            return self.model.get_sentence_embedding_dimension()


embedding_service = EmbeddingService()

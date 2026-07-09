import logging
from typing import Optional

from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)

CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class Reranker:
    _instance: Optional["Reranker"] = None
    _model: Optional[CrossEncoder] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def model(self) -> CrossEncoder:
        if self._model is None:
            logger.info(f"Loading cross-encoder model: {CROSS_ENCODER_MODEL}")
            self._model = CrossEncoder(CROSS_ENCODER_MODEL)
            logger.info("Cross-encoder model loaded")
        return self._model

    def rerank(self, query: str, documents: list[str], top_k: Optional[int] = None) -> list[tuple[str, float]]:
        if not documents:
            return []

        pairs = [[query, doc] for doc in documents]
        scores = self.model.predict(pairs)

        scored = list(zip(documents, scores.tolist() if hasattr(scores, 'tolist') else scores))
        scored.sort(key=lambda x: x[1], reverse=True)

        if top_k:
            scored = scored[:top_k]

        return scored

    def rerank_with_details(
        self, query: str, results: list[dict], top_k: Optional[int] = None
    ) -> list[dict]:
        documents = [r["content"] for r in results]
        reranked = self.rerank(query, documents, top_k)

        doc_map = {r["content"]: r for r in results}
        output = []
        for doc, score in reranked:
            original = doc_map.get(doc, {})
            output.append({
                "content": doc,
                "rerank_score": float(score),
                "metadata": original.get("metadata", {}),
                "distance": original.get("distance", 0),
            })
        return output


reranker = Reranker()

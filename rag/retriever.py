import logging
from typing import Optional

from rag.embedding_pipeline import EmbeddingPipeline

logger = logging.getLogger(__name__)


class Retriever:

    def __init__(self, collection_name: str = "resume_knowledge", top_k: int = 10):
        self.collection_name = collection_name
        self.top_k = top_k

    def retrieve(self, query: str, top_k: Optional[int] = None) -> list[dict]:
        k = top_k or self.top_k
        results = EmbeddingPipeline.query(
            query_text=query,
            collection_name=self.collection_name,
            top_k=k,
        )
        logger.debug(f"Retrieved {len(results)} results for query: {query[:50]}...")
        return results

    def retrieve_with_scores(self, query: str, top_k: Optional[int] = None) -> list[tuple[str, float, dict]]:
        results = self.retrieve(query, top_k)
        return [
            (r["content"], r["distance"], r["metadata"])
            for r in results
        ]

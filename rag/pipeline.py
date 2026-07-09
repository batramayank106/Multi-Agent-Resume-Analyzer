import logging
from typing import Optional

from rag.retriever import Retriever
from rag.reranker import reranker
from rag.context_builder import ContextBuilder

logger = logging.getLogger(__name__)


class RAGPipeline:
    def __init__(
        self,
        collection_name: str = "resume_knowledge",
        retrieve_top_k: int = 10,
        rerank_top_k: int = 5,
        max_context_chars: int = 4000,
    ):
        self.retriever = Retriever(collection_name=collection_name, top_k=retrieve_top_k)
        self.rerank_top_k = rerank_top_k
        self.max_context_chars = max_context_chars

    def run(self, query: str) -> dict:
        retrieved = self.retriever.retrieve(query)
        logger.info(f"Retrieved {len(retrieved)} documents for query")

        reranked = reranker.rerank_with_details(query, retrieved, top_k=self.rerank_top_k)
        logger.info(f"Reranked to {len(reranked)} documents")

        context = ContextBuilder.build_context_with_scores(
            reranked, max_chars=self.max_context_chars
        )

        prompt = ContextBuilder.format_for_prompt(context, query)

        return {
            "query": query,
            "context": context,
            "prompt": prompt,
            "retrieved_count": len(retrieved),
            "reranked_count": len(reranked),
            "documents": reranked,
        }

    def run_stream(self, query: str) -> dict:
        return self.run(query)

    def get_retrieved_chunks(self, query: str) -> list[dict]:
        retrieved = self.retriever.retrieve(query)
        return reranker.rerank_with_details(query, retrieved, top_k=self.rerank_top_k)


rag_pipeline = RAGPipeline()

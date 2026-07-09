import logging
import uuid
from typing import Optional

from rag.chroma_client import chroma_client
from rag.document_loader import DocumentLoader
from rag.chunking import chunking_service
from services.embedding_service import embedding_service

logger = logging.getLogger(__name__)

KNOWLEDGE_COLLECTION = "resume_knowledge"
DOCUMENTS_COLLECTION = "resume_documents"


class EmbeddingPipeline:

    @staticmethod
    def embed_and_store(
        texts: list[str],
        metadatas: Optional[list[dict]] = None,
        collection_name: str = KNOWLEDGE_COLLECTION,
    ) -> int:
        collection = chroma_client.get_or_create_collection(collection_name)
        embeddings = embedding_service.embed(texts)

        ids = [str(uuid.uuid4()) for _ in texts]
        if metadatas is None:
            metadatas = [{"source": "knowledge_base"} for _ in texts]

        collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )
        logger.info(f"Stored {len(texts)} chunks in collection '{collection_name}'")
        return len(texts)

    @staticmethod
    def process_and_store(
        file_path: Optional[str] = None,
        raw_text: Optional[str] = None,
        source_name: str = "unknown",
        collection_name: str = KNOWLEDGE_COLLECTION,
    ) -> int:
        if file_path:
            text = DocumentLoader.load_file(file_path)
        elif raw_text:
            text = raw_text
        else:
            logger.error("Either file_path or raw_text is required")
            return 0

        if not text:
            logger.error("No text content to process")
            return 0

        chunks = chunking_service.chunk_text(text)
        metadatas = [{"source": source_name, "chunk_index": i} for i in range(len(chunks))]
        return EmbeddingPipeline.embed_and_store(chunks, metadatas, collection_name)

    @staticmethod
    def query(
        query_text: str,
        collection_name: str = KNOWLEDGE_COLLECTION,
        top_k: int = 5,
    ) -> list[dict]:
        collection = chroma_client.get_or_create_collection(collection_name)
        query_embedding = embedding_service.embed_query(query_text)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )

        output = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                output.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                })
        return output

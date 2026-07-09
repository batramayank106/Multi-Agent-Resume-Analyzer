"""Seed ChromaDB with knowledge documents for RAG."""

import logging
from pathlib import Path

from rag.embedding_pipeline import EmbeddingPipeline

logger = logging.getLogger(__name__)

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"


def seed_knowledge_base():
    knowledge_files = list(KNOWLEDGE_DIR.glob("*.txt"))
    if not knowledge_files:
        logger.warning(f"No knowledge files found in {KNOWLEDGE_DIR}")
        return 0

    total_chunks = 0
    for kf in knowledge_files:
        source_name = kf.stem.replace("_", " ").title()
        logger.info(f"Processing: {kf.name}")
        chunks = EmbeddingPipeline.process_and_store(
            file_path=str(kf),
            source_name=source_name,
        )
        total_chunks += chunks
        logger.info(f"  → {chunks} chunks stored")

    logger.info(f"Knowledge base seeded: {total_chunks} total chunks from {len(knowledge_files)} files")
    return total_chunks


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_knowledge_base()

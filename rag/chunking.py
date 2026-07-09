import logging
from typing import Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class ChunkingService:
    _instance: Optional["ChunkingService"] = None
    _splitter: Optional[RecursiveCharacterTextSplitter] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def splitter(self) -> RecursiveCharacterTextSplitter:
        if self._splitter is None:
            self._splitter = RecursiveCharacterTextSplitter(
                chunk_size=512,
                chunk_overlap=64,
                separators=["\n\n", "\n", ".", " ", ""],
                length_function=len,
            )
        return self._splitter

    def chunk_text(self, text: str) -> list[str]:
        chunks = self.splitter.split_text(text)
        logger.debug(f"Split {len(text)} chars into {len(chunks)} chunks")
        return chunks

    def chunk_documents(self, texts: list[str]) -> list[str]:
        all_chunks = []
        for text in texts:
            all_chunks.extend(self.chunk_text(text))
        return all_chunks

    def set_chunk_size(self, chunk_size: int, chunk_overlap: int = 64):
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", " ", ""],
            length_function=len,
        )


chunking_service = ChunkingService()

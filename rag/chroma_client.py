import logging
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.errors import NotFoundError

from config import settings

logger = logging.getLogger(__name__)


class ChromaClient:
    _instance: Optional["ChromaClient"] = None
    _client: Optional[chromadb.PersistentClient] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def client(self) -> chromadb.PersistentClient:
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=settings.chroma_persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            logger.info(f"ChromaDB client initialized at {settings.chroma_persist_dir}")
        return self._client

    def get_or_create_collection(self, name: str):
        try:
            return self.client.get_collection(name)
        except NotFoundError:
            return self.client.create_collection(name)

    def delete_collection(self, name: str):
        try:
            self.client.delete_collection(name)
            logger.info(f"Deleted collection '{name}'")
        except NotFoundError:
            logger.warning(f"Collection '{name}' not found")

    def list_collections(self) -> list[str]:
        return [c.name for c in self.client.list_collections()]


chroma_client = ChromaClient()

import logging
from pathlib import Path
from typing import Optional

from langchain_community.document_loaders import TextLoader, PyMuPDFLoader

logger = logging.getLogger(__name__)


class DocumentLoader:

    @staticmethod
    def load_text(file_path: str) -> Optional[str]:
        try:
            loader = TextLoader(file_path, encoding="utf-8")
            docs = loader.load()
            return "\n".join(d.page_content for d in docs)
        except Exception as e:
            logger.error(f"Failed to load text file {file_path}: {e}")
            return None

    @staticmethod
    def load_pdf(file_path: str) -> Optional[str]:
        try:
            loader = PyMuPDFLoader(file_path)
            docs = loader.load()
            return "\n".join(d.page_content for d in docs)
        except Exception as e:
            logger.error(f"Failed to load PDF file {file_path}: {e}")
            return None

    @staticmethod
    def load_file(file_path: str) -> Optional[str]:
        path = Path(file_path)
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return None
        suffix = path.suffix.lower()
        if suffix == ".txt" or suffix == ".md":
            return DocumentLoader.load_text(file_path)
        elif suffix == ".pdf":
            return DocumentLoader.load_pdf(file_path)
        else:
            logger.warning(f"Unsupported file type: {suffix}")
            return None

    @staticmethod
    def load_raw_text(text: str) -> str:
        return text

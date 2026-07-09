import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from cryptography.fernet import Fernet

from config import settings

logger = logging.getLogger(__name__)
LIBRARY_DIR = Path(__file__).parent.parent / "resume_library"
LIBRARY_DIR.mkdir(exist_ok=True)
METADATA_FILE = LIBRARY_DIR / "metadata.json"


def _get_cipher() -> Fernet:
    key = settings.encryption_key.encode("utf-8")
    return Fernet(key)


def _load_metadata() -> dict:
    if METADATA_FILE.exists():
        try:
            return json.loads(METADATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_metadata(meta: dict):
    METADATA_FILE.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def encrypt_data(data: bytes) -> bytes:
    cipher = _get_cipher()
    return cipher.encrypt(data)


def decrypt_data(data: bytes) -> bytes:
    cipher = _get_cipher()
    try:
        return cipher.decrypt(data)
    except InvalidToken:
        logger.error("Failed to decrypt file — key may have changed")
        raise


def save_file(original_filename: str, data: bytes) -> dict:
    file_id = str(uuid.uuid4())
    encrypted = encrypt_data(data)
    file_path = LIBRARY_DIR / f"{file_id}.enc"
    file_path.write_bytes(encrypted)
    meta = _load_metadata()
    meta[file_id] = {
        "id": file_id,
        "original_filename": original_filename,
        "size": len(data),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_metadata(meta)
    logger.info(f"Saved file {original_filename} as {file_id}")
    return meta[file_id]


def get_file(file_id: str) -> tuple[bytes, dict]:
    meta = _load_metadata()
    info = meta.get(file_id)
    if not info:
        raise FileNotFoundError(f"File {file_id} not found")
    file_path = LIBRARY_DIR / f"{file_id}.enc"
    if not file_path.exists():
        raise FileNotFoundError(f"Encrypted file {file_id} missing from disk")
    data = decrypt_data(file_path.read_bytes())
    return data, info


def list_files() -> list[dict]:
    meta = _load_metadata()
    files = sorted(meta.values(), key=lambda f: f.get("created_at", ""), reverse=True)
    for f in files:
        size = f.get("size", 0)
        if size < 1024:
            f["size_display"] = f"{size} B"
        elif size < 1024 * 1024:
            f["size_display"] = f"{size / 1024:.1f} KB"
        else:
            f["size_display"] = f"{size / 1024 / 1024:.1f} MB"
    return files


def delete_file(file_id: str) -> bool:
    meta = _load_metadata()
    if file_id not in meta:
        return False
    file_path = LIBRARY_DIR / f"{file_id}.enc"
    if file_path.exists():
        file_path.unlink()
    del meta[file_id]
    _save_metadata(meta)
    logger.info(f"Deleted file {file_id}")
    return True

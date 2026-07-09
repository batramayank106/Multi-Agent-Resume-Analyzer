import logging
import traceback

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import Response

from services.resume_library import save_file, get_file, list_files, delete_file
from services.auth_service import get_current_user
from models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/library", tags=["library"])


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    try:
        if not file.filename:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename required")
        allowed = {".txt", ".pdf", ".tex", ".md", ".doc", ".docx", ".json", ".html", ".csv"}
        ext = (file.filename.rsplit(".", 1)[-1] if "." in file.filename else "").lower()
        if ext and f".{ext}" not in allowed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File type .{ext} not allowed")
        data = await file.read()
        if len(data) > 10 * 1024 * 1024:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large (max 10MB)")
        info = save_file(file.filename, data)
        return {"message": "File uploaded", "file": info}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/files")
def get_files(current_user: User = Depends(get_current_user)):
    return list_files()


@router.get("/files/{file_id}")
def download_file(file_id: str, current_user: User = Depends(get_current_user)):
    try:
        data, info = get_file(file_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return Response(
        content=data,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{info["original_filename"]}"'},
    )


@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_file(file_id: str, current_user: User = Depends(get_current_user)):
    if not delete_file(file_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

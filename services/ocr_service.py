import os
import re
import logging
from PIL import Image

logger = logging.getLogger(__name__)

_HAS_OCR = False
_OCR_ENGINE = None

TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
    os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe"),
]


def init_ocr():
    global _HAS_OCR, _OCR_ENGINE
    try:
        import pytesseract
        for p in TESSERACT_PATHS:
            if os.path.isfile(p):
                pytesseract.pytesseract.tesseract_cmd = p
                _OCR_ENGINE = "pytesseract"
                _HAS_OCR = True
                logger.info(f"OCR initialised: {p}")
                return True
        tess_cmd = os.getenv("TESSERACT_CMD", "")
        if tess_cmd and os.path.isfile(tess_cmd):
            pytesseract.pytesseract.tesseract_cmd = tess_cmd
            _OCR_ENGINE = "pytesseract"
            _HAS_OCR = True
            logger.info(f"OCR initialised via TESSERACT_CMD: {tess_cmd}")
            return True
        try:
            pytesseract.get_tesseract_version()
            _OCR_ENGINE = "pytesseract"
            _HAS_OCR = True
            logger.info("OCR initialised via PATH")
            return True
        except Exception:
            pass
        logger.warning("Tesseract binary not found in any known path")
        return False
    except ImportError:
        logger.warning("pytesseract not installed")
        return False


def is_ocr_available() -> bool:
    return _HAS_OCR


def ocr_engine() -> str:
    return _OCR_ENGINE or "none"


def _preprocess_image(img):
    try:
        import numpy as np
        import cv2
    except ImportError:
        return img.convert("L") if img.mode != "L" else img
    img = img.convert("L")
    arr = np.array(img)
    _, arr = cv2.threshold(arr, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = np.ones((2, 2), np.uint8)
    arr = cv2.morphologyEx(arr, cv2.MORPH_CLOSE, kernel)
    arr = cv2.medianBlur(arr, 1)
    coords = cv2.findNonZero(arr)
    if coords is not None:
        x, y, w, h = cv2.boundingRect(coords)
        arr = arr[y : y + h, x : x + w]
    if arr.shape[0] > 0 and arr.shape[1] > 0:
        arr = cv2.copyMakeBorder(arr, 15, 15, 15, 15, cv2.BORDER_CONSTANT, value=255)
    return Image.fromarray(arr)


def _postprocess_text(raw: str) -> str:
    lines = raw.split("\n")
    cleaned = []
    buffer = ""
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if buffer:
                cleaned.append(buffer)
                buffer = ""
            continue
        stripped = re.sub(r"^[%\&=\*\+\~]+\s*", "• ", stripped)
        if stripped.endswith("-") and len(stripped) > 2:
            buffer += stripped[:-1]
        elif buffer and (stripped[0].islower() or stripped[0] in ",;:)"):
            buffer += " " + stripped
        else:
            if buffer:
                cleaned.append(buffer)
            buffer = stripped
    if buffer:
        cleaned.append(buffer)
    result = "\n".join(cleaned)

    result = re.sub(r"(?<=\w)-\n(?=\w)", "", result)
    result = re.sub(r"\n{3,}", "\n\n", result)
    result = re.sub(r"[ \t]{2,}", " ", result)
    result = re.sub(r"(?<=\w)\.(?=\w)", ". ", result)
    return result.strip()


def extract_text_from_image(image_bytes: bytes) -> str:
    if not _HAS_OCR:
        init_ocr()
    if not _HAS_OCR:
        raise RuntimeError(
            "OCR is not available. Install Tesseract OCR "
            "(https://github.com/UB-Mannheim/tesseract/wiki) "
            "and add it to your PATH, or set TESSERACT_CMD in .env"
        )
    try:
        import pytesseract
        import io
        img = Image.open(io.BytesIO(image_bytes))
        img = _preprocess_image(img)
        text = pytesseract.image_to_string(img, config="--psm 6 --oem 3")
        text = _postprocess_text(text)
        if not text.strip():
            img_orig = Image.open(io.BytesIO(image_bytes))
            text = pytesseract.image_to_string(img_orig, config="--psm 3 --oem 3")
            text = _postprocess_text(text)
        return text.strip()
    except Exception as e:
        logger.error(f"OCR extraction failed: {e}")
        return ""


def ocr_status_html() -> str:
    if not _HAS_OCR:
        init_ocr()
    if _HAS_OCR:
        return (
            '<span style="color:#5db872;font-size:0.8rem;">'
            f"✓ OCR engine available ({_OCR_ENGINE})</span>"
        )
    return (
        '<span style="color:#c64545;font-size:0.8rem;">'
        "✗ OCR not available — image text won't be extracted. "
        "<a href='https://github.com/UB-Mannheim/tesseract/wiki' "
        "target='_blank' style='color:#cc785c;'>Install Tesseract</a></span>"
    )
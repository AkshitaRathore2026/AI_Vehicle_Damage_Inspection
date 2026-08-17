from pathlib import Path
from uuid import uuid4


EXTENSION_BY_CONTENT_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
}


def safe_original_filename(filename: str | None) -> str:
    if not filename:
        return "uploaded_image"
    return Path(filename).name.strip() or "uploaded_image"


def build_unique_image_filename(content_type: str) -> str:
    extension = EXTENSION_BY_CONTENT_TYPE[content_type]
    return f"{uuid4().hex}{extension}"


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

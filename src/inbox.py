import json
import shutil
import time
from datetime import datetime
from pathlib import Path

from src.config import AUDIO_EXTENSIONS


def ensure_dirs(*dirs: Path):
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def list_new_recordings(inbox: Path, settle_seconds: float = 2.0):
    """Аудіофайли з inbox, які вже повністю скопійовані (не змінювались кілька секунд)."""
    now = time.time()
    files = [
        p for p in Path(inbox).iterdir()
        if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS
        and now - p.stat().st_mtime >= settle_seconds
    ]
    return sorted(files, key=lambda p: p.stat().st_mtime)


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def move_to(src: Path, dest_dir: Path, stamp: str) -> Path:
    """Переносить файл в архів, додаючи мітку часу, щоб імена не конфліктували."""
    dest = Path(dest_dir) / f"{stamp}_{src.name}"
    shutil.move(str(src), str(dest))
    return dest


def save_json(path: Path, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

INBOX_DIR = DATA_DIR / "inbox"                      # сюди кладете нові записи
PROCESSED_DIR = DATA_DIR / "archive" / "processed"  # успішно оброблені
FAILED_DIR = DATA_DIR / "archive" / "failed"        # оброблені з помилкою
RESULTS_DIR = DATA_DIR / "results"                  # транскрипти та результати (JSON)

TEAM_CONTEXT_PATH = DATA_DIR / "team_context.json"
TICKETS_DB_PATH = DATA_DIR / "tickets_db.json"

STT_MODEL = "whisper-large-v3"
LLM_MODEL = "openai/gpt-oss-20b"

AUDIO_EXTENSIONS = {".mp3", ".ogg", ".wav", ".m4a", ".flac", ".webm", ".mp4", ".mpeg", ".mpga"}

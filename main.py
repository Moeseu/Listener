import argparse
import asyncio
import time
import traceback

from dotenv import load_dotenv

from src.agents.validators import build_glossary, load_json
from src.agents.workflow import MeetingWorkflow
from src.audio.transcriber import AudioTranscriber
from src.config import (FAILED_DIR, INBOX_DIR, PROCESSED_DIR, RESULTS_DIR, TEAM_CONTEXT_PATH)
from src.inbox import ensure_dirs, list_new_recordings, move_to, save_json, timestamp
from src.mcp_client import export_tasks_via_mcp

load_dotenv()


def process_recording(path, transcriber, workflow):
    stamp = timestamp()
    print(f"\n=== Обробка: {path.name} ===")

    print("1. Розпізнавання аудіо...")
    glossary = build_glossary(load_json(TEAM_CONTEXT_PATH, {}))
    text = transcriber.transcribe(path, glossary=glossary)
    print(f"   Транскрипт: {text}")

    print("2. Робота мультиагентного графа...")
    state = workflow.run(text)
    tasks = state["action_items"]
    for w in state["warnings"]:
        print(f"   ! {w}")

    print(f"3. Експорт завдань через MCP-протокол ({len(tasks)} шт.)...")
    replies = asyncio.run(export_tasks_via_mcp(tasks, source=path.name)) if tasks else []

    save_json(RESULTS_DIR / f"{stamp}_{path.stem}.json", {
        "file": path.name,
        "transcript": text,
        "summary": state["summary"],
        "key_decisions": state["key_decisions"],
        "tasks": [t.model_dump() for t in tasks],
        "warnings": state["warnings"],
        "mcp_replies": replies,
    })
    archived = move_to(path, PROCESSED_DIR, stamp)
    print(f"4. Запис перенесено в архів: {archived.relative_to(archived.parents[2])}")


def process_inbox(transcriber, workflow) -> int:
    files = list_new_recordings(INBOX_DIR)
    for path in files:
        try:
            process_recording(path, transcriber, workflow)
        except Exception:
            err = traceback.format_exc()
            print(f"   ПОМИЛКА, файл переміщено в archive/failed:\n{err}")
            stamp = timestamp()
            save_json(RESULTS_DIR / f"{stamp}_{path.stem}_ERROR.json", {"file": path.name, "error": err})
            move_to(path, FAILED_DIR, stamp)
    return len(files)


def main():
    parser = argparse.ArgumentParser(description="Обробка записів нарад з папки data/inbox")
    parser.add_argument("--watch", action="store_true", help="не завершуватись, а чекати на нові файли")
    parser.add_argument("--interval", type=int, default=5, help="період опитування папки, с")
    args = parser.parse_args()

    ensure_dirs(INBOX_DIR, PROCESSED_DIR, FAILED_DIR, RESULTS_DIR)
    transcriber, workflow = AudioTranscriber(), MeetingWorkflow()

    if not args.watch:
        if process_inbox(transcriber, workflow) == 0:
            print(f"У папці {INBOX_DIR} немає нових записів.")
        return

    print(f"Очікування нових записів у {INBOX_DIR} (Ctrl+C для виходу)...")
    try:
        while True:
            process_inbox(transcriber, workflow)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nЗупинено.")


if __name__ == "__main__":
    main()

"""Детермінована перевірка результатів LLM (без викликів моделі)."""
import json
from pathlib import Path


def load_json(path: Path, default):
    path = Path(path)
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_alias_map(ctx: dict) -> dict:
    """Нижній регістр псевдоніма -> канонічне ім'я учасника."""
    mapping = {}
    for member in ctx.get("team_members", []):
        for alias in [member["name"], *member.get("aliases", [])]:
            mapping[alias.strip().lower()] = member["name"]
    return mapping


def build_glossary(ctx: dict) -> str:
    """Підказка для Whisper: імена та назви проєктів розпізнаються точніше."""
    names = []
    for m in ctx.get("team_members", []):
        names.append(m["name"])
        if m.get("aliases"):
            names.append(m["aliases"][0])
    projects = [p["name"].split(":")[0] for p in ctx.get("active_projects", [])]
    return f"Нарада IT-команди. Учасники: {', '.join(names)}. Проєкти: {', '.join(projects)}."


def detect_projects(transcript: str, ctx: dict) -> set:
    text = transcript.lower()
    found = set()
    for p in ctx.get("active_projects", []):
        words = [p["name"].split(":")[0].lower(), *[k.lower() for k in p.get("keywords", [])]]
        if any(w in text for w in words):
            found.add(p["id"])
    return found


def normalize_tasks(tasks, ctx: dict, existing_tickets: list, transcript: str):
    """Повертає (чисті задачі, список попереджень)."""
    aliases = build_alias_map(ctx)
    project_ids = {p["id"] for p in ctx.get("active_projects", [])}
    existing_ids = {t["id"] for t in existing_tickets}
    mentioned = detect_projects(transcript, ctx)

    clean, warnings, seen = [], [], set()
    for task in tasks:
        task = task.model_copy()

        if task.duplicate_of:
            if task.duplicate_of in existing_ids:
                warnings.append(f"Пропущено «{task.title}»: дублює {task.duplicate_of}")
                continue
            task.duplicate_of = None

        key = task.title.strip().lower()
        if key in seen:
            warnings.append(f"Пропущено «{task.title}»: дубль у межах наради")
            continue
        seen.add(key)

        if task.assignee:
            canonical = aliases.get(task.assignee.strip().lower())
            if canonical is None:
                warnings.append(f"«{task.title}»: виконавця «{task.assignee}» немає в команді, не призначено")
            task.assignee = canonical
        if task.assignee is None:
            warnings.append(f"«{task.title}»: потребує ручного призначення виконавця")

        if task.project_id and task.project_id not in project_ids:
            warnings.append(f"«{task.title}»: невідомий проєкт «{task.project_id}», скинуто")
            task.project_id = None
        if task.project_id is None and len(mentioned) == 1:
            task.project_id = next(iter(mentioned))
            warnings.append(f"«{task.title}»: проєкт визначено за ключовими словами ({task.project_id})")

        clean.append(task)
    return clean, warnings

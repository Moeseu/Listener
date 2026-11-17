import os
from typing import TypedDict, List

from groq import Groq
from langgraph.graph import StateGraph, START, END
from pydantic import ValidationError

from src.config import LLM_MODEL, TEAM_CONTEXT_PATH, TICKETS_DB_PATH
from src.schemas.task import SummaryOutput, TasksOutput
from src.agents.validators import load_json, normalize_tasks

SYSTEM_PROMPT = (
    "Ти асистент проєктного менеджера. Відповідай ЛИШЕ валідним JSON. "
    "Усі текстові значення пиши УКРАЇНСЬКОЮ мовою, незалежно від мови транскрипту."
)


class MeetingState(TypedDict, total=False):
    transcript: str
    team_context: dict
    existing_tickets: list
    summary: str
    key_decisions: List[str]
    raw_items: list
    action_items: list
    warnings: List[str]


class MeetingWorkflow:
    def __init__(self, max_retries: int = 3):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.max_retries = max_retries

        builder = StateGraph(MeetingState)
        builder.add_node("summarizer", self.summarize_node)
        builder.add_node("extractor", self.extract_tasks_node)
        builder.add_node("validator", self.validate_node)
        builder.add_edge(START, "summarizer")
        builder.add_edge("summarizer", "extractor")
        builder.add_edge("extractor", "validator")
        builder.add_edge("validator", END)
        self.graph = builder.compile()

    def _ask(self, prompt: str, schema):
        """Запит до LLM з повтором, якщо JSON не пройшов валідацію."""
        last_error = None
        for _ in range(self.max_retries):
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                model=LLM_MODEL,
                temperature=0,
                response_format={"type": "json_object"},
            )
            try:
                return schema.model_validate_json(response.choices[0].message.content)
            except (ValidationError, ValueError) as e:
                last_error = e
        raise RuntimeError(f"LLM не повернула коректний JSON після {self.max_retries} спроб: {last_error}")

    def summarize_node(self, state: MeetingState):
        prompt = f"""Сформуй управлінське резюме наради. Поверни JSON:
{{"summary": "1-2 речення суті", "key_decisions": ["Рішення 1"]}}

Транскрипт: {state['transcript']}"""
        result = self._ask(prompt, SummaryOutput)
        return {"summary": result.summary, "key_decisions": result.key_decisions}

    def extract_tasks_node(self, state: MeetingState):
        import json
        ctx = json.dumps(state["team_context"], ensure_ascii=False, indent=2)
        existing = json.dumps(
            [{"id": t["id"], "title": t["title"], "description": t.get("description", ""),
            "assignee": t["assignee"], "project_id": t.get("project_id")}
            for t in state["existing_tickets"] if t.get("status") != "DONE"],
            ensure_ascii=False,
        )
        prompt = f"""Виділи з наради нові задачі. Поверни JSON:
{{"action_items": [{{"title": "...", "description": "...", "assignee": "ім'я або null",
"assignee_reason": "коротко чому", "priority": "Low|Medium|High",
"project_id": "ID або null", "duplicate_of": "ID наявного тікета або null"}}]}}

КОНТЕКСТ ПРОЄКТУ:
{ctx}

НАЯВНІ ТІКЕТИ: {existing}

Резюме наради: {state['summary']}
Транскрипт: {state['transcript']}

Правила:
1. Задача це конкретна дія, яку треба виконати в майбутньому. Привітання, обговорення та нагадування про вже призначене задачами НЕ є. Якщо задач немає, поверни порожній список.
2. assignee: ТІЛЬКИ точне поле "name" з team_members. Якщо виконавця названо за іменем або псевдонімом (aliases), використай його. Якщо імені немає, обери людину за role та responsibilities лише коли збіг очевидний. Інакше null. Імена, яких немає в team_members, не вигадуй, став null.
3. project_id: ТІЛЬКИ "id" з active_projects, і лише якщо в тексті згадано назву або ключове слово проєкту. Інакше null.
4. Якщо в тексті лише нагадується про роботу, яка вже є серед НАЯВНИХ ТІКЕТІВ (навіть іншими словами), не створюй нову задачу: вкажи її ID в duplicate_of.
5. priority High лише якщо сказано "терміново" або схоже. За замовчуванням Medium.
6. title і description пиши українською.
7. Якщо в одній фразі згадано різні види робіт (наприклад, 3D-модель і програмний код), створи окрему задачу на кожен вид."""
        result = self._ask(prompt, TasksOutput)
        return {"raw_items": result.action_items}

    def validate_node(self, state: MeetingState):
        clean, warnings = normalize_tasks(
            state["raw_items"], state["team_context"], state["existing_tickets"], state["transcript"]
        )
        return {"action_items": clean, "warnings": warnings}

    def run(self, transcript: str):
        # Контекст і тікети читаються щоразу: правки в JSON діють без перезапуску
        return self.graph.invoke({
            "transcript": transcript,
            "team_context": load_json(TEAM_CONTEXT_PATH, {}),
            "existing_tickets": load_json(TICKETS_DB_PATH, []),
        })

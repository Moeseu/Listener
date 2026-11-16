import os
import json
from typing import TypedDict, List
from groq import Groq
from langgraph.graph import StateGraph, START, END
from src.schemas.task import SummaryOutput, TasksOutput

class MeetingState(TypedDict):
    transcript: str
    summary: str
    key_decisions: List[str]
    action_items: list
    backlog: str

class MeetingWorkflow:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        with open("data/team_context.json", "r", encoding="utf-8") as file:
            self.team_context = file.read()
        
        builder = StateGraph(MeetingState)
        builder.add_node("summarizer", self.summarize_node)
        builder.add_node("extractor", self.extract_tasks_node)
        
        builder.add_edge(START, "summarizer")
        builder.add_edge("summarizer", "extractor")
        builder.add_edge("extractor", END)
        
        self.graph = builder.compile()

    def summarize_node(self, state: MeetingState):
        prompt = f"""Ти аналітик. Сформуй управлінське резюме. Поверни суворо JSON:
{{
    "summary": "1-2 речення суті",
    "key_decisions": ["Рішення 1"]
}}
Транскрипт: {state['transcript']}"""
        
        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="openai/gpt-oss-20b",
            response_format={"type": "json_object"},
            temperature=0.0
        )
        result = SummaryOutput.model_validate_json(response.choices[0].message.content)
        return {"summary": result.summary, "key_decisions": result.key_decisions}

    def extract_tasks_node(self, state: MeetingState):
        prompt = f"""Ти Agile Project Manager. Декомпозуй обговорення на тікети. Поверни суворо JSON формату {{"action_items": [...]}}.
        
ПРАВИЛА ГЕНЕРАЦІЇ:
1. Атомарність: Одне завдання — один логічний крок.
2. Дієвий заголовок: title завжди починається з дієслова.
3. Критерії завершеності: description фіксує конкретний артефакт.
4. Контекстна маршрутизація: Заповнюй project_id з КОНТЕКСТУ ПРОЄКТУ.
5. Валідація виконавця: assignee ТІЛЬКИ з КОНТЕКСТУ ПРОЄКТУ.
6. ДЕДУПЛІКАЦІЯ: Уважно прочитай ІСНУЮЧИЙ БЕКЛОГ. Якщо обговорювана задача вже присутня там за змістом, ПОВНІСТЮ ІГНОРУЙ її та не генеруй для неї тікет.

Резюме наради: {state['summary']}
Транскрипт: {state['transcript']}
КОНТЕКСТ ПРОЄКТУ: {self.team_context}
ІСНУЮЧИЙ БЕКЛОГ: {state['backlog']}"""
        
        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="openai/gpt-oss-20b",
            response_format={"type": "json_object"},
            temperature=0.0
        )
        result = TasksOutput.model_validate_json(response.choices[0].message.content)
        return {"action_items": result.action_items}
        
    def run(self, transcript: str):
        # Зчитування поточного беклогу перед запуском графа
        backlog_data = "[]"
        if os.path.exists("data/tickets_db.json"):
            with open("data/tickets_db.json", "r", encoding="utf-8") as file:
                backlog_data = file.read()
                
        return self.graph.invoke({
            "transcript": transcript,
            "backlog": backlog_data
        })
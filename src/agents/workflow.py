import os
from typing import TypedDict, List
from groq import Groq
from langgraph.graph import StateGraph, START, END
from src.schemas.task import SummaryOutput, TasksOutput

class MeetingState(TypedDict):
    transcript: str
    summary: str
    key_decisions: List[str]
    action_items: list

class MeetingWorkflow:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        with open("data/team_context.json", "r", encoding="utf-8") as file:
            self.team_context = file.read()
        
        # Ініціалізація графа
        builder = StateGraph(MeetingState)
        builder.add_node("summarizer", self.summarize_node)
        builder.add_node("extractor", self.extract_tasks_node)
        
        # Налаштування потоку
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
            response_format={"type": "json_object"}
        )
        result = SummaryOutput.model_validate_json(response.choices[0].message.content)
        return {"summary": result.summary, "key_decisions": result.key_decisions}

    def extract_tasks_node(self, state: MeetingState):
        prompt = f"""Ти Agile Project Manager. Розподіли задачі. Поверни суворо JSON:
{{
    "action_items": [
        {{"title": "Задача", "description": "Опис", "assignee": "Ім'я", "priority": "Medium", "project_id": "ID"}}
    ]
}}

Резюме наради: {state['summary']}
Транскрипт: {state['transcript']}
КОНТЕКСТ ПРОЄКТУ: {self.team_context}

Правила: призначай задачі ТІЛЬКИ на учасників з КОНТЕКСТУ та використовуй project_id."""
        
        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="openai/gpt-oss-20b",
            response_format={"type": "json_object"}
        )
        result = TasksOutput.model_validate_json(response.choices[0].message.content)
        return {"action_items": result.action_items}
        
    def run(self, transcript: str):
        return self.graph.invoke({"transcript": transcript})
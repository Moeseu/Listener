import os
import json
from groq import Groq
from src.schemas.task import MeetingProtocol

class MeetingAnalyzer:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        # RAG: Завантажуємо контекст проєкту в пам'ять агента
        with open("data/team_context.json", "r", encoding="utf-8") as file:
            self.team_context = file.read()

    def analyze_transcript(self, transcript_text: str) -> MeetingProtocol:
        prompt = f"""Ти Agile Project Manager. Поверни суворо JSON:
{{
    "summary": "1-2 речення суті",
    "key_decisions": ["Рішення"],
    "action_items": [
        {{"title": "Задача", "description": "Короткий опис", "assignee": "Реальне ім'я з команди", "priority": "Medium"}}
    ]
}}

КОНТЕКСТ ПРОЄКТУ:
{self.team_context}

Транскрипт: {transcript_text}

Правила:
1. Призначай задачі ТІЛЬКИ на учасників з "КОНТЕКСТ ПРОЄКТУ".
2. Зіставляй суть задачі з роллю людини (наприклад, якщо задача про тестування — призначай на QA).
3. Якщо з тексту незрозуміло, хто саме має це робити, повертай null у полі assignee.
4. Визначай project_id для кожної задачі на основі ключових слів з "active_projects" у КОНТЕКСТІ. Якщо проєкт неможливо визначити, повертай null.
"""
        
        chat_completion = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="openai/gpt-oss-20b",
            response_format={"type": "json_object"}
        )
        
        return MeetingProtocol.model_validate_json(chat_completion.choices[0].message.content)
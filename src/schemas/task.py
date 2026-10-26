from pydantic import BaseModel, Field
from typing import List, Optional

class TaskItem(BaseModel):
    title: str = Field(description="Коротка назва завдання")
    description: str = Field(description="Детальний опис")
    assignee: Optional[str] = Field(default=None, description="Ім'я відповідального з команди")
    priority: str = Field(default="Medium", description="Пріоритет")
    project_id: Optional[str] = Field(default=None, description="ID проєкту")

class SummaryOutput(BaseModel):
    summary: str = Field(description="Короткий зміст наради")
    key_decisions: List[str] = Field(description="Список прийнятих рішень")

class TasksOutput(BaseModel):
    action_items: List[TaskItem] = Field(description="Список виділених завдань")
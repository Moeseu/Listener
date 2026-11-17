from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class TaskItem(BaseModel):
    title: str = Field(description="Коротка назва завдання")
    description: str = Field(description="Детальний опис")
    assignee: Optional[str] = Field(default=None, description="Ім'я відповідального з команди")
    assignee_reason: Optional[str] = Field(default=None, description="Чому обрано цього виконавця")
    priority: str = Field(default="Medium", description="Low / Medium / High")
    project_id: Optional[str] = Field(default=None, description="ID проєкту")
    duplicate_of: Optional[str] = Field(default=None, description="ID наявного тікета, якщо задача вже існує")

    @field_validator("priority", mode="before")
    @classmethod
    def normalize_priority(cls, v):
        v = str(v or "Medium").strip().capitalize()
        return v if v in {"Low", "Medium", "High"} else "Medium"

    @field_validator("assignee", "project_id", "duplicate_of", mode="before")
    @classmethod
    def empty_to_none(cls, v):
        if v is None:
            return None
        v = str(v).strip()
        return None if v.lower() in {"", "null", "none", "n/a", "unassigned"} else v


class SummaryOutput(BaseModel):
    summary: str = Field(description="Короткий зміст наради")
    key_decisions: List[str] = Field(description="Список прийнятих рішень")


class TasksOutput(BaseModel):
    action_items: List[TaskItem] = Field(description="Список виділених завдань")

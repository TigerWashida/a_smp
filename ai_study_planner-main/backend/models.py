from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class StudyGoal(BaseModel):
    subject: str = Field(min_length=1, max_length=120)
    total_hours: float = Field(gt=0, le=100)
    difficulty: Literal["Easy", "Medium", "Hard"]
    preferred_slot: Literal["Morning", "Afternoon", "Evening"]
    deadline: date

    @field_validator("subject")
    @classmethod
    def normalize_subject(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Subject cannot be blank.")
        return value


class PreviewSessionUpdate(BaseModel):
    preview_session_id: str = Field(min_length=1, max_length=80)
    date: date
    start_time: str
    end_time: str


class AcceptPreviewRequest(BaseModel):
    sessions: list[PreviewSessionUpdate] = Field(min_length=1)


class ScheduleUpdate(BaseModel):
    date: date
    start_time: str
    end_time: str


class TaskStatusUpdate(BaseModel):
    status: Literal["pending", "completed"]


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    preview_id: str | None = None

from pydantic import BaseModel
from datetime import date

class StudyGoal(BaseModel):
    subject: str
    total_hours: int
    difficulty: str
    preferred_slot: str
    exam_date: date

from pydantic import BaseModel

class ChatRequest(BaseModel):
    query: str
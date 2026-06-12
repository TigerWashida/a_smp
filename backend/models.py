from pydantic import BaseModel
class StudyGoal(BaseModel):
    subject: str
    total_hours: int
    difficulty: str
    preferred_slot: str
    exam_date: str

# class TaskUpdate(BaseModel):

#     status: str
from pydantic import BaseModel
from datetime import date

class TaskCreate(BaseModel):
    title: str
    category: str
    priority: str
    due_date: date
    
class MorningCheckin(BaseModel):
    morning_notes: str
    
class EveningCheckin(BaseModel):
    evening_notes: str
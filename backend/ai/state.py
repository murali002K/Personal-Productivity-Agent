# state.py

from typing import TypedDict

class ProductivityState(TypedDict):
    tasks: list
    overdue_tasks: list
    completed_tasks: list
    summary: str
    tomorrow_plan: str
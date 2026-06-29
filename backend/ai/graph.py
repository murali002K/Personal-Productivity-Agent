from typing import TypedDict
from langgraph.graph import StateGraph, END
from backend.ai.groq_client import generate_summary
from database import SessionLocal
from models import Task
from datetime import date

# Define state strictly matching graph requirements
class AgentState(TypedDict):
    message: str
    category: str
    overdue_tasks: str
    eod_summary: str
    tomorrow_plan: str


def classifier(state: AgentState) -> dict:
    print("Classifier Running")
    
    # Safe lookup for the required incoming key
    task_message = state.get("message", "")
    
    prompt = f"""
Classify this task into exactly one category: Work, Learning, Health, or Personal.
Task: {task_message}
Return only the category name.
"""
    category = generate_summary(prompt).strip()
    
    # Fixed: Return ONLY the state updates as a new dictionary slice
    return {"category": category}


def overdue(state: AgentState) -> dict:
    print("Overdue Running")
    db = SessionLocal()
    try:
        overdue_tasks = db.query(Task).filter(
            Task.due_date < date.today(),
            Task.status == "Pending"
        ).all()

        titles = [task.title for task in overdue_tasks]
        overdue_str = ", ".join(titles) if titles else "No overdue tasks"
        
        # Fixed: Return ONLY the state slice updates
        return {"overdue_tasks": overdue_str}
    finally:
        db.close()  # Fixed: Always safely close the database session


def eod_summary(state: AgentState) -> dict:
    print("EOD Summary Running")
    
    # Safe dictionary lookups to avoid unexpected KeyError failures
    task_message = state.get("message", "")
    category = state.get("category", "Unclassified")
    
    prompt = f"""
Write a short productivity summary.
Task: {task_message}
Category: {category}
"""
    summary = generate_summary(prompt)
    
    # Fixed: Return ONLY the state slice updates
    return {"eod_summary": summary}


def tomorrow_planner(state: AgentState) -> dict:
    print("Tomorrow Planner Running")
    task_message = state.get("message", "")
    
    prompt = f"""
Create a short plan for tomorrow.
Task: {task_message}
"""
    plan = generate_summary(prompt)
    
    # Fixed: Return ONLY the state slice updates
    return {"tomorrow_plan": plan}


# --- Graph Construction and Compilation ---
graph = StateGraph(AgentState)

# Add processing worker nodes
graph.add_node("classifier", classifier)
graph.add_node("overdue", overdue)
graph.add_node("eod_summary", eod_summary)
graph.add_node("tomorrow_planner", tomorrow_planner)

# Set the flow logic sequence
graph.set_entry_point("classifier")
graph.add_edge("classifier", "overdue")
graph.add_edge("overdue", "eod_summary")
graph.add_edge("eod_summary", "tomorrow_planner")
graph.add_edge("tomorrow_planner", END)

# Compile ready for invoke() steps
app_graph = graph.compile()

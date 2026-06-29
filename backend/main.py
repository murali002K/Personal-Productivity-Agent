from datetime import datetime, date
import os
from fastapi import FastAPI, HTTPException
from backend.database import SessionLocal
from backend.models import Task, DailyLog, EODSummary
from backend.schemas import (
    TaskCreate,
    MorningCheckin,
    EveningCheckin
)
from backend.schemas import *
from backend.ai.graph import app_graph
from backend.ai.groq_client import generate_summary
from backend.database import engine
from backend.models import Base

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Database Connected Successfully"}

@app.post("/tasks")
def create_task(task: TaskCreate):
    db = SessionLocal()
    try:
        new_task = Task(
            user_id=1,
            title=task.title,
            category=task.category,
            priority=task.priority,
            due_date=task.due_date,
            status="Pending"
        )
        db.add(new_task)
        db.commit()
        return {"message": "Task Saved Successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/tasks")
def get_tasks():
    db = SessionLocal()
    try:
        tasks = db.query(Task).all()
        result = []
        for task in tasks:
            result.append({
                "id": task.id,
                "title": task.title,
                "category": task.category,
                "priority": task.priority,
                "status": task.status
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.put("/tasks/{task_id}")
def complete_task(task_id: int):
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        task.status = "Completed"
        task.completed_at = datetime.now()
        db.commit()
        return {"message": "Task marked as completed"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        db.delete(task)
        db.commit()
        return {"message": "Task deleted"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/checkin/morning")
def morning_checkin(data: MorningCheckin):
    db = SessionLocal()
    try:
        # Check if a log entry already exists for today
        existing_log = db.query(DailyLog).filter(
            DailyLog.user_id == 1,
            DailyLog.log_date == date.today()
        ).first()

        if existing_log:
            existing_log.morning_notes = data.morning_notes
            message = "Morning Check-in Updated"
        else:
            log = DailyLog(
                user_id=1,
                log_date=date.today(),
                morning_notes=data.morning_notes
            )
            db.add(log)
            message = "Morning Check-in Saved"
            
        db.commit()
        return {"message": message}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/checkin/evening")
def evening_checkin(data: EveningCheckin):
    db = SessionLocal()
    try:
        latest_log = db.query(DailyLog)\
                       .filter(DailyLog.user_id == 1)\
                       .order_by(DailyLog.id.desc())\
                       .first()
        if not latest_log:
            raise HTTPException(status_code=404, detail="No morning check-in found")
        latest_log.evening_notes = data.evening_notes
        db.commit()
        return {"message": "Evening Check-in Saved"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/overdue-tasks")
def get_overdue_tasks():
    db = SessionLocal()
    try:
        overdue_tasks = db.query(Task).filter(
            Task.due_date < date.today(),
            Task.status == "Pending"
        ).all()
        result = []
        for task in overdue_tasks:
            result.append({
                "id": task.id,
                "title": task.title,
                "category": task.category,
                "priority": task.priority,
                "due_date": str(task.due_date)
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/dashboard")
def dashboard():
    db = SessionLocal()
    try:
        total = db.query(Task).count()
        completed = db.query(Task).filter(Task.status == "Completed").count()
        pending = db.query(Task).filter(Task.status == "Pending").count()
        
        # Calculate completion percentage safely
        completion_rate = round((completed / total * 100), 2) if total > 0 else 0.0

        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "pending_tasks": pending,
            "completion_rate": completion_rate
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/eod-summary")
def generate_eod_summary():
    db = SessionLocal()
    try:
        total_tasks = db.query(Task).count()
        if total_tasks == 0:
            return {"summary": "No tasks available today. Keep up the clean slate!"}

        completed_tasks = db.query(Task).filter(Task.status == "Completed").all()
        pending_tasks = db.query(Task).filter(Task.status == "Pending").all()
        
        completed_titles = [task.title for task in completed_tasks]
        pending_titles = [task.title for task in pending_tasks]
        
        prompt = f"""
You are a productivity coach.
Completed tasks: {', '.join(completed_titles) if completed_titles else 'None'}
Pending tasks: {', '.join(pending_titles) if pending_titles else 'None'}
Write a professional End Of Day Summary in one paragraph.
"""
        summary = generate_summary(prompt)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
    
@app.get("/tomorrow-plan")
def tomorrow_plan():
    db = SessionLocal()
    try:
        pending_tasks = db.query(Task).filter(Task.status == "Pending").all()
        if not pending_tasks:
            return {"tomorrow_plan": "You have no pending tasks! Enjoy a clear focus day tomorrow or add new goals."}
            
        pending_titles = [task.title for task in pending_tasks]
        
        prompt = f"""
You are a productivity coach.
Pending tasks: {', '.join(pending_titles)}
Create a prioritized plan for tomorrow.
Mention:
1. Top priority tasks
2. Medium priority tasks
3. Suggested focus for the day
Keep it concise.
"""
        plan = generate_summary(prompt)
        return {"tomorrow_plan": plan}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
    
@app.post("/run-eod")
def run_eod():
    db = SessionLocal()
    try:
        total_tasks = db.query(Task).count()
        if total_tasks == 0:
            return {"message": "End Of Day Summary run skipped. No tasks found.", "summary": ""}

        completed_tasks = db.query(Task).filter(Task.status == "Completed").all()
        pending_tasks = db.query(Task).filter(Task.status == "Pending").all()
        
        completed_titles = [task.title for task in completed_tasks]
        pending_titles = [task.title for task in pending_tasks]

        prompt = f"Summarize today's progress. Completed: {', '.join(completed_titles) if completed_titles else 'None'}. Pending: {', '.join(pending_titles) if pending_titles else 'None'}."
        summary_text = generate_summary(prompt)

        eod_log = EODSummary(
            user_id=1,
            summary=summary_text
        )
        db.add(eod_log)
        db.commit()

        return {"message": "End Of Day Summary run and saved successfully!", "summary": summary_text}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/weekly-review")
def get_weekly_review():
    db = SessionLocal()
    try:
        total = db.query(Task).count()
        
        # Handle zero tasks scenario gracefully before AI request
        if total == 0:
            return {"weekly_review": "No tasks recorded this week. Ready to plan some new milestones?"}

        completed = db.query(Task).filter(Task.status == "Completed").count()
        pending = db.query(Task).filter(Task.status == "Pending").count()
        
        # Enhanced granularity metrics
        high_priority = db.query(Task).filter(Task.priority == "High").count()
        medium_priority = db.query(Task).filter(Task.priority == "Medium").count()
        overdue_tasks = db.query(Task).filter(Task.due_date < date.today(), Task.status == "Pending").count()
        completion_rate = round((completed / total * 100), 2)

        prompt = f"""
You are a productivity coach.

Weekly Performance Metrics:
- Total Managed Tasks: {total}
- Completed: {completed}
- Pending: {pending}
- Completion Rate: {completion_rate}%
- High Priority Items: {high_priority}
- Medium Priority Items: {medium_priority}
- Overdue Bottlenecks: {overdue_tasks}

Write a professional weekly review.

Mention:
1. Productivity level based on completion rate and priority allocation
2. Significant Accomplishments
3. Areas to improve (addressing overdue items if any exist)
4. Strategic Goals for next week
5. Keep it concise.
"""
        review = generate_summary(prompt)
        return {"weekly_review": review}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
    
@app.get("/test-agent")
def test_agent():
    db = SessionLocal()
    try:
        task = db.query(Task).first()
        if not task:
            raise HTTPException(status_code=404, detail="No tasks found")
        
        result = app_graph.invoke({"message": task.title})
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
        
@app.get("/test-groq")
def test_groq():
    try:
        result = generate_summary("Write a 2 line productivity summary.")
        return {"response": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


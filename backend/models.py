from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Date, DateTime

Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    title = Column(String(255))
    category = Column(String(50))
    priority = Column(String(20))
    status = Column(String(20))
    due_date = Column(Date)

    completed_at = Column(DateTime, nullable=True)
    
class DailyLog(Base):
    __tablename__ = "daily_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    log_date = Column(Date)
    morning_notes = Column(String(1000))
    evening_notes = Column(String(1000))
    
class EODSummary(Base):
    __tablename__ = "eod_summaries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    summary = Column(String(5000))


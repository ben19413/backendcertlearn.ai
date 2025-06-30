from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class QuestionDB(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, nullable=False, index=True)  # Unique identifier for a test session
    user_email = Column(String(255), nullable=False, index=True)
    exam_type = Column(String(50), nullable=False)  # Store exam type (e.g., CFA1)
    question = Column(String, nullable=False)
    answer_1 = Column(String, nullable=False)
    answer_2 = Column(String, nullable=False)
    answer_3 = Column(String, nullable=False)
    answer_4 = Column(String, nullable=False)
    solution = Column(Integer, nullable=False)  # Now stores 1-4 for correct answer

class QuestionLogDB(Base):
    __tablename__ = "question_logs"
    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)
    user_email = Column(String(255), nullable=False, index=True)
    selected_answer = Column(Integer, nullable=False)  # 1-4
    liked = Column(Boolean, nullable=True)  # True=upvote, False=downvote, None=not voted
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)


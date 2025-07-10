from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class QuestionDB(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, nullable=False, index=True) 
    exam_type = Column(String(50), nullable=False)
    topic = Column(String(255), nullable=False)  
    topic_number = Column(Integer, nullable=False)
    batch_number = Column(Integer, nullable=False)
    question = Column(String, nullable=False)
    answer_1 = Column(String, nullable=False)
    answer_2 = Column(String, nullable=False)
    answer_3 = Column(String, nullable=False)
    answer_4 = Column(String, nullable=False)
    solution = Column(Integer, nullable=False)

class AnswerLogDB(Base):
    __tablename__ = "answer_logs"
    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)
    selected_answer = Column(Integer, nullable=False)
    user_email = Column(String(255), nullable=False)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)

class OpinionLogDB(Base):
    __tablename__ = "opinion_logs"
    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)
    up = Column(Boolean, nullable=False)
    user_email = Column(String(255), nullable=False)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)


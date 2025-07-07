from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func,UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class QuestionDB(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, nullable=False, index=True) 
    user_email = Column(String(255), nullable=False, index=True)
    exam_type = Column(String(50), nullable=False)
    question_set_id = Column(String(255), nullable=False, index=True)  
    topic = Column(String(255), nullable=False)  
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
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)

class OpinionLogDB(Base):
    __tablename__ = "opinion_logs"
    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)
    up = Column(Boolean, nullable=False) 
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    password = Column(String, nullable=True)
    provider = Column(String, default="local", nullable=True)
    fullname = Column(String, nullable=True)
    register_date = Column(DateTime, default=func.now())
    __table_args__ = (UniqueConstraint('username', 'provider', name='unique_username_per_provider'),)

    @property
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
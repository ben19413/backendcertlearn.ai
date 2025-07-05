import asyncio
from pathlib import Path
from typing import Dict, Any
import aiofiles
from models import QuestionDB
from schemas import QuestionRequest, QuestionResponse, ErrorResponse, ExamType

from gemini import GeminiClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from question_repository import QuestionRepository, AnswerLogRepository
import os


class QuestionGeneratorService:
    """Service class for generating exam questions with async IO operations."""
    
    def __init__(self, data_dir: str = "/data"):
        """Initialize the question generator service."""
        self.data_dir = Path(data_dir)
        self.gemini_client = GeminiClient()
    
    async def generate_questions(self, request: QuestionRequest, test_id: str, ) -> QuestionResponse:
        """Generate questions based on the request parameters."""
        try:
            # Load exam content from a .txt file
            exam_content = await self._load_exam_content(request.exam_type)
            # Generate questions using Gemini, passing topic and exam_content
            response = await self.gemini_client.generate_questions_async(
                topic=request.topic,
                num_questions=request.num_questions,
                exam_type=request.exam_type,
                exam_content=exam_content
            )
            # Save each question to the DB
            db = SessionLocal()
            repo = QuestionRepository(db)
            for q in response.questions:
                repo.add_question(
                    test_id=test_id,
                    user_email=request.user_email,
                    exam_type=request.exam_type.value,
                    question_set_id=request.question_set_id,
                    topic=request.topic,  # <-- Add this line
                    question=q.question,
                    answer_1=q.answer_1,
                    answer_2=q.answer_2,
                    answer_3=q.answer_3,
                    answer_4=q.answer_4,
                    solution=q.solution
                )
            db.close()
            return response
        except Exception as e:
            raise RuntimeError(f"Failed to generate questions: {e}")

    async def _load_exam_content(self, exam_type: ExamType) -> str:
        """Load exam content from a .txt file."""
        file_path = self.data_dir / f"{exam_type.value}.txt"
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
                return await file.read()
        except FileNotFoundError:
            return ""
        except Exception as e:
            raise RuntimeError(f"Error loading content for {exam_type.value}: {e}")

    def list_questions_for_user(self, user_email: str):
        db = SessionLocal()
        repo = QuestionRepository(db)
        questions = repo.get_questions_by_user(user_email)
        db.close()
        return questions

    def get_question_for_user(self, user_email: str, question_id: int):
        db = SessionLocal()
        repo = QuestionRepository(db)
        question = repo.get_question_by_user_and_id(user_email, question_id)
        db.close()
        return question

    def list_questions_for_test(self, test_id: str):
        db = SessionLocal()
        repo = QuestionRepository(db)
        questions = repo.get_questions_by_test(test_id)
        db.close()
        return questions

    def get_question_for_test(self, test_id: str, question_id: int):
        db = SessionLocal()
        repo = QuestionRepository(db)
        question = repo.get_question_by_test_and_id(test_id, question_id)
        db.close()
        return question


class QuestionLogService:
    """Service class for handling answer logging operations."""

    def add_log(self, log):
        db = SessionLocal()
        repo = AnswerLogRepository(db)
        log_entry = repo.add_log(
            question_id=log.question_id,
            selected_answer=log.selected_answer
        )
        db.close()
        return log_entry

    def get_logs_for_question(self, question_id: int):
        db = SessionLocal()
        repo = AnswerLogRepository(db)
        logs = repo.get_logs_for_question(question_id)
        db.close()
        return logs

    def get_logs_for_user(self, user_email: str):
        db = SessionLocal()
        repo = AnswerLogRepository(db)
        logs = repo.get_logs_for_user(user_email)
        db.close()
        return logs


DATABASE_URL = os.getenv("DATABASE_URL", "mssql+pyodbc://sa:YourStrong!Passw0rd@mssql:1433/master?driver=ODBC+Driver+17+for+SQL+Server")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


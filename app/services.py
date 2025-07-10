import asyncio
from pathlib import Path
from typing import Dict, Any
import aiofiles
from models import QuestionDB
from schemas import QuestionRequest, QuestionResponse, ErrorResponse, ExamType, InProgressSetsResponse, Question
from gemini import GeminiClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from question_repository import QuestionRepository, AnswerLogRepository, OpinionLogRepository
import os


class QuestionGeneratorService:
    """Service class for generating exam questions with async IO operations."""
    
    def __init__(self, data_dir: str = "/data"):
        """Initialize the question generator service."""
        self.data_dir = Path(data_dir)
        self.gemini_client = GeminiClient()
    
    async def generate_questions(self, request: QuestionRequest, test_id: str, batch_number: int) -> QuestionResponse:
        """
        Generate a batch of questions: N questions for each topic.
        Each question will be tagged with its topic, topic_number (1..N), and batch_number (index of topic in topics list, starting from 1).
        All questions are stored under the same batch_number.
        """
        try:
            all_questions = []
            exam_type = request.exam_type
            for topic_batch_number, topic in enumerate(request.topics, start=1):
                pdf_bytes = await self._load_exam_pdf(exam_type, topic.value)
                response = await self.gemini_client.generate_questions_async(
                    topic=topic.value,
                    num_questions=request.num_questions,
                    exam_type=exam_type,
                    exam_pdf_bytes=pdf_bytes
                )
                db = SessionLocal()
                repo = QuestionRepository(db)
                for topic_number, q in enumerate(response.questions, start=1):
                    repo.add_question(
                        test_id=test_id,
                        exam_type=exam_type.value,
                        topic=topic.value,
                        topic_number=topic_number,
                        batch_number=batch_number,
                        question=q.question,
                        answer_1=q.answer_1,
                        answer_2=q.answer_2,
                        answer_3=q.answer_3,
                        answer_4=q.answer_4,
                        solution=q.solution
                    )
                    q_dict = q.dict()
                    q_dict["topic"] = topic.value
                    q_dict["topic_number"] = topic_number
                    q_dict["batch_number"] = batch_number
                    all_questions.append(q_dict)
                db.close()
            return QuestionResponse(
                test_id=test_id,
                questions=[Question(**q) for q in all_questions],
                exam_type=exam_type,
                total_questions=len(all_questions)
            )
        except Exception as e:
            raise RuntimeError(f"Failed to generate questions: {e}")

    async def _load_exam_pdf(self, exam_type: ExamType, topic: str) -> bytes:
        """Load exam PDF file as bytes from /data/{exam_name}/{topic}.pdf."""
        file_path = self.data_dir / exam_type.value / f"{topic}.pdf"
        try:
            async with aiofiles.open(file_path, 'rb') as file:
                return await file.read()
        except FileNotFoundError:
            raise RuntimeError(f"PDF file not found: {file_path}")
        except Exception as e:
            raise RuntimeError(f"Error loading PDF for {exam_type.value}/{topic}: {e}")

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

    def get_unseen_questions_for_user_and_set(self, user_email: str, question_set_id: str):
        db = SessionLocal()
        try:
            questions = db.query(QuestionDB).filter(QuestionDB.question_set_id == question_set_id).all()
            question_ids = [q.id for q in questions]
            from models import AnswerLogDB
            seen_logs = db.query(AnswerLogDB.question_id).filter(
                AnswerLogDB.user_email == user_email,
                AnswerLogDB.question_id.in_(question_ids)
            ).distinct().all()
            seen_ids = {row[0] for row in seen_logs}
            unseen_questions = [q for q in questions if q.id not in seen_ids]
            if questions:
                exam_type = questions[0].exam_type
            else:
                exam_type = None
            from schemas import Question, ExamType, QuestionResponse
            pydantic_questions = [
                Question(
                    question=q.question,
                    answer_1=q.answer_1,
                    answer_2=q.answer_2,
                    answer_3=q.answer_3,
                    answer_4=q.answer_4,
                    solution=q.solution
                ) for q in unseen_questions
            ]
            response = QuestionResponse(
                test_id=0,
                questions=pydantic_questions,
                exam_type=ExamType(exam_type) if exam_type else ExamType.CFA3topics,
                total_questions=len(pydantic_questions)
            )
            return response
        finally:
            db.close()

    def get_in_progress_question_sets_for_user(self, user_email: str) -> InProgressSetsResponse:
        db = SessionLocal()
        try:
            from models import AnswerLogDB
            set_ids = db.query(QuestionDB.question_set_id).distinct().all()
            set_ids = [row[0] for row in set_ids]
            in_progress_sets = []
            for question_set_id in set_ids:
                questions = db.query(QuestionDB).filter(QuestionDB.question_set_id == question_set_id).all()
                question_ids = [q.id for q in questions]
                total_questions = len(question_ids)
                if total_questions == 0:
                    continue
                # Count how many of these questions have been answered by the user
                answered_count = db.query(AnswerLogDB).filter(
                    AnswerLogDB.user_email == user_email,
                    AnswerLogDB.question_id.in_(question_ids)
                ).distinct(AnswerLogDB.question_id).count()
                # Only in progress if at least one answered and not all answered
                if answered_count > 0 and answered_count < total_questions:
                    in_progress_sets.append(question_set_id)
            return InProgressSetsResponse(in_progress_sets=in_progress_sets)
        finally:
            db.close()


class QuestionLogService:
    """Service class for handling answer logging operations."""

    def add_log(self, log):
        db = SessionLocal()
        repo = AnswerLogRepository(db)
        log_entry = repo.add_log(
            question_id=log.question_id,
            selected_answer=log.selected_answer,
            user_email=log.user_email
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


class OpinionLogService:
    """Service class for handling opinion logging operations."""

    def add_opinion(self, log):
        db = SessionLocal()
        repo = OpinionLogRepository(db)
        log_entry = repo.add_opinion(
            question_id=log.question_id,
            up=log.up,
            user_email=log.user_email
        )
        db.close()
        return log_entry


DATABASE_URL = os.getenv("DATABASE_URL", "mssql+pyodbc://sa:YourStrong!Passw0rd@mssql:1433/master?driver=ODBC+Driver+17+for+SQL+Server")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



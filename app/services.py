import asyncio
from pathlib import Path
from typing import Dict, Any
import aiofiles
from models import QuestionDB, QuestionSetDB, AnswerLogDB
from schemas import QuestionRequest, QuestionResponse, ErrorResponse, ExamType, InProgressSetsResponse, Question, CreateQuestionSetRequest, QuestionSetResponse
from gemini import GeminiClient
from sqlalchemy import create_engine
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from question_repository import QuestionRepository, AnswerLogRepository, OpinionLogRepository
import os


class QuestionGeneratorService:
    """Service class for generating exam questions with async IO operations."""
    
    def __init__(self, data_dir: str = "/data"):
        """Initialize the question generator service."""
        self.data_dir = Path(data_dir)
        self.gemini_client = GeminiClient()
    
    async def generate_questions(self, request: QuestionRequest, test_id: int, batch_number: int) -> QuestionResponse:
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

    def get_unseen_questions_for_user_and_set(self, user_email: str, question_set_id: int):
        db = SessionLocal()
        try:
            # Get all question_ids in this question set for this user
            question_set_entries = db.query(QuestionSetDB).filter(
                QuestionSetDB.question_set_id == question_set_id,
                QuestionSetDB.user_email == user_email
            ).all()
            
            if not question_set_entries:
                # No questions in this set for this user
                return QuestionResponse(
                    test_id=0,
                    questions=[],
                    exam_type=ExamType.CFA1,
                    total_questions=0
                )
            
            question_ids = [entry.question_id for entry in question_set_entries]
            
            # Get all questions in the set
            questions = db.query(QuestionDB).filter(QuestionDB.id.in_(question_ids)).all()
            
            # Find which questions the user has already answered
            answered_question_ids = db.query(AnswerLogDB.question_id).filter(
                AnswerLogDB.user_email == user_email,
                AnswerLogDB.question_id.in_(question_ids)
            ).distinct().all()
            answered_ids = {row[0] for row in answered_question_ids}
            
            # Filter to get only unseen questions
            unseen_questions = [q for q in questions if q.id not in answered_ids]
            
            # Get exam_type from the first question if available
            exam_type = questions[0].exam_type if questions else None
            
            pydantic_questions = [
                Question(
                    question=q.question,
                    answer_1=q.answer_1,
                    answer_2=q.answer_2,
                    answer_3=q.answer_3,
                    answer_4=q.answer_4,
                    solution=q.solution,
                    topic=q.topic,
                    topic_number=q.topic_number,
                    batch_number=q.batch_number
                ) for q in unseen_questions
            ]
            
            return QuestionResponse(
                test_id=0,
                questions=pydantic_questions,
                exam_type=ExamType(exam_type) if exam_type else ExamType.CFA3topics,
                total_questions=len(pydantic_questions)
            )
        finally:
            db.close()

    def get_in_progress_question_sets_for_user(self, user_email: str) -> InProgressSetsResponse:
        db = SessionLocal()
        try:
            # Get all unique question_set_ids for this user from the question_set_lookup_table
            set_ids = db.query(QuestionSetDB.question_set_id).filter(
                QuestionSetDB.user_email == user_email
            ).distinct().all()
            set_ids = [row[0] for row in set_ids]
            
            in_progress_sets = []
            for question_set_id in set_ids:
                # Get all question_ids in this question set for this user
                question_set_entries = db.query(QuestionSetDB.question_id).filter(
                    QuestionSetDB.question_set_id == question_set_id,
                    QuestionSetDB.user_email == user_email
                ).all()
                question_ids = [row[0] for row in question_set_entries]
                total_questions = len(question_ids)
                
                if total_questions == 0:
                    continue
                
                # Count how many of these questions have been answered by the user
                answered_count = db.query(AnswerLogDB.question_id).filter(
                    AnswerLogDB.user_email == user_email,
                    AnswerLogDB.question_id.in_(question_ids)
                ).distinct().count()
                
                # Only in progress if at least one answered and not all answered
                if answered_count > 0 and answered_count < total_questions:
                    in_progress_sets.append(str(question_set_id))
                    
            return InProgressSetsResponse(in_progress_sets=in_progress_sets)
        finally:
            db.close()

    def create_question_set_for_user(self, request: CreateQuestionSetRequest) -> QuestionSetResponse:
        db = SessionLocal()
        try:
            repo = QuestionRepository(db)
            # Generate a new question_set_id
            max_qsid = db.query(sa.func.max(sa.cast(QuestionSetDB.question_set_id, sa.Integer))).scalar() or 0
            question_set_id = max_qsid + 1
            # Get next questions for each topic
            next_questions = repo.get_next_questions_for_topics(
                user_email=request.user_email,
                topics=request.topics,
                num_questions_per_topic=request.num_questions_per_topic
            )
            # Add entries to question_sets table
            for q in next_questions:
                repo.add_question_set_entry(
                    question_set_id=question_set_id,
                    question_id=q.id,
                    user_email=request.user_email
                )
            # Prepare response
            questions = [Question(
                question=q.question,
                answer_1=q.answer_1,
                answer_2=q.answer_2,
                answer_3=q.answer_3,
                answer_4=q.answer_4,
                solution=q.solution,
                topic=q.topic,
                topic_number=q.topic_number,
                batch_number=q.batch_number
            ) for q in next_questions]
            return QuestionSetResponse(
                question_set_id=question_set_id,
                questions=questions
            )
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


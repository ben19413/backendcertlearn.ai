from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from schemas import QuestionRequest, QuestionResponse, ErrorResponse, Question, ExamType, AnswerLog, OpinionLog, CreateQuestionSetRequest, QuestionSetResponse
from services import QuestionGeneratorService, SessionLocal, QuestionLogService, OpinionLogService, InProgressSetsResponse
import logging
import uuid
from sqlalchemy.orm import Session
from models import QuestionDB
import sqlalchemy as sa
from sqlalchemy import select
from models import AnswerLogDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/questions", tags=["questions"])

# Dependency injection for service
def get_question_service() -> QuestionGeneratorService:
    """Get question generator service instance."""
    return QuestionGeneratorService()

log_service = QuestionLogService()
opinion_service = OpinionLogService()


@router.post(
    "/generate",
    response_model=QuestionResponse,
    responses={
        400: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Generate multiple choice questions",
    description="Generate multiple choice questions from provided text for specified exam type"
)
async def generate_questions(
    request: QuestionRequest,
    service: QuestionGeneratorService = Depends(get_question_service)
) -> QuestionResponse:
    """Generate multiple choice questions for each topic and store under the same batch (batch_number)."""
    try:
        db = SessionLocal()
        # Generate a new integer test_id (one greater than the current max)
        max_test_id = db.query(sa.func.max(sa.cast(QuestionDB.test_id, sa.Integer))).scalar() or 0
        test_id = max_test_id + 1
        # Generate a new integer batch_number (one greater than the current max)
        max_batch = db.query(sa.func.max(sa.cast(QuestionDB.batch_number, sa.Integer))).scalar() or 0
        batch_number = max_batch + 1
        db.close()
        logger.info(f"Generating {request.num_questions} questions for each topic in {request.topics} for {request.exam_type.value} with test_id {test_id} and batch_number {batch_number}")
        response = await service.generate_questions(request, test_id=test_id, batch_number=batch_number)
        logger.info(f"Successfully generated {response.total_questions} questions")
        response.test_id = test_id
        return response
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail={"error": "Invalid input", "detail": str(e)}
        )
    except RuntimeError as e:
        logger.error(f"Service error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error", "detail": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Unexpected error occurred", "detail": "Please try again later"}
        )


@router.get(
    "/health",
    summary="Health check endpoint",
    description="Check if the questions service is healthy"
)
async def health_check():
    """Health check endpoint for the questions service."""
    return {"status": "healthy", "service": "questions"}

@router.post("/log", response_model=AnswerLog)
def log_question_answer(log: AnswerLog):
    """Log a student's answer for a question."""
    try:
        return log_service.add_log(log)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/opinion", response_model=OpinionLog)
def log_opinion(log: OpinionLog):
    """Log an up/down opinion for a question."""
    return opinion_service.add_opinion(log)


@router.get(
    "/unseen",
    response_model=QuestionResponse,
    summary="List unseen questions for a user in a question set",
    description="Return all questions in a question set that the user has not answered yet"
)
def list_unseen_questions(
    user_email: str = Query(..., description="User's email address"),
    question_set_id: int = Query(..., description="Question set identifier"),
    service: QuestionGeneratorService = Depends(get_question_service)
):
    """List all unseen questions for a user in a question set."""
    return service.get_unseen_questions_for_user_and_set(user_email, question_set_id)


@router.get(
    "/in_progress",
    response_model=InProgressSetsResponse,
    summary="Check all question sets in progress for a user",
    description="Returns {'in_progress_sets': [question_set_id, ...]} for sets started but not finished by the user"
)
def list_in_progress_question_sets(
    user_email: str = Query(..., description="User's email address"),
    service: QuestionGeneratorService = Depends(get_question_service)
):
    """
    Check all question sets for which the user has started but not finished answering questions.
    Returns a list of question_set_id values that are in progress.
    """
    return service.get_in_progress_question_sets_for_user(user_email)


@router.post(
    "/create_question_set",
    response_model=QuestionSetResponse,
    summary="Create a question set for a user from specified topics",
    description="Assigns next N questions from each topic to a user and returns the question set"
)
def create_question_set(
    request: CreateQuestionSetRequest,
    service: QuestionGeneratorService = Depends(get_question_service)
):
    """Create a question set for a user from specified topics."""
    return service.create_question_set_for_user(request)
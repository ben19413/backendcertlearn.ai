from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from schemas import QuestionRequest, QuestionResponse, ErrorResponse, Question, ExamType, QuestionLog
from services import QuestionGeneratorService, SessionLocal, QuestionLogService
import logging
import uuid
from sqlalchemy.orm import Session
from models import QuestionDB
import sqlalchemy as sa

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/questions", tags=["questions"])

# Dependency injection for service
def get_question_service() -> QuestionGeneratorService:
    """Get question generator service instance."""
    return QuestionGeneratorService()

log_service = QuestionLogService()


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
    """Generate multiple choice questions based on input text and exam type."""
    try:
        # Generate a new integer test_id (one greater than the current max)
        db = SessionLocal()
        max_test_id = db.query(sa.func.max(sa.cast(QuestionDB.test_id, sa.Integer))).scalar() or 0
        test_id = max_test_id + 1
        db.close()
        logger.info(f"Generating {request.num_questions} questions for {request.exam_type.value} with test_id {test_id}")
        response = await service.generate_questions(request, test_id=test_id)
        
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


@router.get("/list", response_model=list[Question])
def list_questions(test_id: str = Query(...), service: QuestionGeneratorService = Depends(get_question_service)):
    """List all questions for a specific test_id."""
    questions = service.list_questions_for_test(test_id)
    return questions


@router.get("/get", response_model=Question)
def get_question(test_id: str = Query(...), question_id: int = Query(...), service: QuestionGeneratorService = Depends(get_question_service)):
    """Get a specific question by test_id and id."""
    question = service.get_question_for_test(test_id, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@router.post("/log", response_model=QuestionLog)
def log_question_answer(log: QuestionLog):
    """Log a student's answer and up/downvote for a question."""
    return log_service.add_log(log)

@router.get("/logs/question/{question_id}", response_model=list[QuestionLog])
def get_logs_for_question(question_id: int):
    """Get all logs for a specific question."""
    return log_service.get_logs_for_question(question_id)

@router.get("/logs/user/{user_email}", response_model=list[QuestionLog])
def get_logs_for_user(user_email: str):
    """Get all logs for a specific user."""
    return log_service.get_logs_for_user(user_email)
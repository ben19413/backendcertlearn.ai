from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from schemas import QuestionRequest, QuestionResponse, ErrorResponse, Question, ExamType
from services import QuestionGeneratorService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/questions", tags=["questions"])

# Dependency injection for service
def get_question_service() -> QuestionGeneratorService:
    """Get question generator service instance."""
    return QuestionGeneratorService()


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
        logger.info(f"Generating {request.num_questions} questions for {request.exam_type.value}")
        
        response = await service.generate_questions(request)
        
        logger.info(f"Successfully generated {response.total_questions} questions")
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
def list_questions(user_email: str = Query(...), service: QuestionGeneratorService = Depends(get_question_service)):
    """List all questions for a specific user_email."""
    questions = service.list_questions_for_user(user_email)
    return questions


@router.get("/get", response_model=Question)
def get_question(user_email: str = Query(...), question_id: int = Query(...), service: QuestionGeneratorService = Depends(get_question_service)):
    """Get a specific question by user_email and id."""
    question = service.get_question_for_user(user_email, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question
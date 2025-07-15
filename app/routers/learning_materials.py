from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from schemas import LearningMaterialRequest, LearningMaterialResponse, ErrorResponse, Specification, ExamType, CFA1Topic
from services import LearningMaterialService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/learning-materials", tags=["learning-materials"])

# Dependency injection for service
def get_learning_material_service() -> LearningMaterialService:
    """Get learning material service instance."""
    return LearningMaterialService()


@router.post(
    "/generate",
    response_model=LearningMaterialResponse,
    responses={
        400: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Generate learning materials",
    description="Generate learning materials for a specific exam and topic based on PDF content"
)
async def generate_learning_materials(
    request: LearningMaterialRequest,
    service: LearningMaterialService = Depends(get_learning_material_service)
) -> LearningMaterialResponse:
    """Generate learning materials for the specified exam and topic."""
    try:
        logger.info(f"Generating learning materials for {request.exam.value}/{request.topic.value}")
        
        # Check if specification already exists
        existing_spec = service.get_specification(request.exam.value, request.topic.value)
        if existing_spec:
            logger.info(f"Found existing specification for {request.exam.value}/{request.topic.value}")
            specification = Specification(
                id=existing_spec.id,
                exam=existing_spec.exam,
                topic=existing_spec.topic,
                specification=existing_spec.specification,
                created_at=existing_spec.created_at
            )
            return LearningMaterialResponse(specification=specification)
        
        # Generate new specification
        spec_entry = await service.generate_learning_material(request.exam.value, request.topic.value)
        specification = Specification(
            id=spec_entry.id,
            exam=spec_entry.exam,
            topic=spec_entry.topic,
            specification=spec_entry.specification,
            created_at=spec_entry.created_at
        )
        
        logger.info(f"Successfully generated learning materials for {request.exam.value}/{request.topic.value}")
        return LearningMaterialResponse(specification=specification)
        
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
    "/{exam}/{topic}",
    response_model=LearningMaterialResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Get existing learning materials",
    description="Retrieve existing learning materials for a specific exam and topic"
)
async def get_learning_materials(
    exam: ExamType,
    topic: CFA1Topic,
    service: LearningMaterialService = Depends(get_learning_material_service)
) -> LearningMaterialResponse:
    """Get existing learning materials for the specified exam and topic."""
    try:
        logger.info(f"Retrieving learning materials for {exam.value}/{topic.value}")
        
        existing_spec = service.get_specification(exam.value, topic.value)
        if not existing_spec:
            raise HTTPException(
                status_code=404,
                detail={"error": "Not found", "detail": f"No learning materials found for {exam.value}/{topic.value}"}
            )
        
        specification = Specification(
            id=existing_spec.id,
            exam=existing_spec.exam,
            topic=existing_spec.topic,
            specification=existing_spec.specification,
            created_at=existing_spec.created_at
        )
        
        return LearningMaterialResponse(specification=specification)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Unexpected error occurred", "detail": "Please try again later"}
        )


@router.get(
    "/health",
    summary="Health check endpoint",
    description="Check if the learning materials service is healthy"
)
async def health_check():
    """Health check endpoint for the learning materials service."""
    return {"status": "healthy", "service": "learning-materials"}

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, validator

class ExamType(str, Enum):
    """Supported exam types with their identifiers."""
    CFA1= "CFA1"

class QuestionRequest(BaseModel):
    """Request model for question generation."""
    user_email: str = Field(..., description="User's email address")
    exam_type: ExamType = Field(..., description="Type of exam for question formatting")
    text: str = Field(..., min_length=1, max_length=5000, description="Text to generate questions from")
    num_questions: int = Field(..., ge=1, le=20, description="Number of questions to generate")
    @validator('text')
    def validate_text_content(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Text cannot be empty or only whitespace")
        return v.strip()

class Choice(BaseModel):
    label: str = Field(..., description="Choice label (A, B, C, or D)")
    text: str = Field(..., min_length=1, max_length=500, description="Choice text")

class Question(BaseModel):
    question: str = Field(..., min_length=10, max_length=1000, description="The question text")
    answer_1: str
    answer_2: str
    answer_3: str
    answer_4: str
    solution: int = Field(..., ge=1, le=4, description="Indicates which answer (1-4) is correct")

class QuestionResponse(BaseModel):
    test_id: int = Field(..., description="Unique integer identifier for the test session")
    questions: List[Question] = Field(..., description="Generated questions")
    exam_type: ExamType = Field(..., description="Exam type used for generation")
    total_questions: int = Field(..., description="Total number of questions generated")
    @validator('total_questions')
    def validate_total_questions(cls, v: int, values: dict) -> int:
        if 'questions' in values and len(values['questions']) != v:
            raise ValueError("total_questions must match the number of questions")
        return v

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, validator


class ExamType(str, Enum):
    """Supported exam types with their identifiers."""
    CFA1= "CFA1"
    


class QuestionRequest(BaseModel):
    """Request model for question generation."""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to generate questions from")
    num_questions: int = Field(..., ge=1, le=20, description="Number of questions to generate")
    exam_type: ExamType = Field(..., description="Type of exam for question formatting")
    
    @validator('text')
    def validate_text_content(cls, v: str) -> str:
        """Ensure text has meaningful content."""
        if not v.strip():
            raise ValueError("Text cannot be empty or only whitespace")
        return v.strip()


class Choice(BaseModel):
    """Individual multiple choice option."""
    label: str = Field(..., description="Choice label (A, B, C, or D)")
    text: str = Field(..., min_length=1, max_length=500, description="Choice text")


class Question(BaseModel):
    """Individual question with multiple choice options."""
    question: str = Field(..., min_length=10, max_length=1000, description="The question text")
    correct_answer: str = Field(...)
    choices: List[Choice] = Field(..., min_items=4, max_items=4, description="Four multiple choice options")
    
    @validator('choices')
    def validate_choices(cls, v: List[Choice]) -> List[Choice]:
        """Ensure choices have labels A, B, C, D."""
        expected_labels = {'A', 'B', 'C', 'D'}
        actual_labels = {choice.label for choice in v}
        if actual_labels != expected_labels:
            raise ValueError("Choices must have exactly labels A, B, C, D")
        return sorted(v, key=lambda x: x.label)


class QuestionResponse(BaseModel):
    """Response model for generated questions."""
    questions: List[Question] = Field(..., description="Generated questions")
    exam_type: ExamType = Field(..., description="Exam type used for generation")
    total_questions: int = Field(..., description="Total number of questions generated")
    
    @validator('total_questions')
    def validate_total_questions(cls, v: int, values: dict) -> int:
        """Ensure total_questions matches actual questions count."""
        if 'questions' in values and len(values['questions']) != v:
            raise ValueError("total_questions must match the number of questions")
        return v


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")


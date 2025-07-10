from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ExamType(str, Enum):
    """Supported exam types with their identifiers."""
    CFA1 = "CFA1"
    CFA3topics = "CFA3topics"

# Enum for CFA1 topics
class CFA1Topic(str, Enum):
    quantitative_methods = "quantitative_methods"
    economics = "economics"
    corporate_issuers = "corporate_issuers"
    financial_statement_analysis = "financial_statement_analysis"
    equity_investments = "equity_investments"
    fixed_income = "fixed_income"
    derivatives = "derivatives"
    alternative_investments = "alternative_investments"
    portfolio_management = "portfolio_management"
    ethical_and_professional_standards = "ethical_and_professional_standards"
    

class QuestionRequest(BaseModel):
    """Request model for question generation."""
    exam_type: ExamType = Field(default=ExamType.CFA3topics, description="Type of exam for question formatting")
    topics: list[CFA1Topic] = Field(..., description="List of topics to generate questions about (used as PDF filenames, e.g. /data/CFA1/{topic}.pdf)")
    num_questions: int = Field(..., ge=1, le=20, description="Number of questions to generate per topic")
    question_set_id: str = Field(None, description="Unique identifier for the question set (optional, will be generated if not provided)")

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
    topic: str
    topic_number: int
    batch_number: int

class QuestionResponse(BaseModel):
    test_id: int = Field(..., description="Unique integer identifier for the test session")
    questions: List[Question] = Field(..., description="Generated questions")
    exam_type: ExamType = Field(..., description="Exam type used for generation")
    total_questions: int = Field(..., description="Total number of questions generated")

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")

class AnswerLog(BaseModel):
    id: Optional[int]
    question_id: int
    selected_answer: int
    user_email: str
    timestamp: datetime

class OpinionLog(BaseModel):
    id: Optional[int]
    question_id: int
    up: bool
    user_email: str
    timestamp: datetime

class InProgressSetsResponse(BaseModel):
    in_progress_sets: list[str]

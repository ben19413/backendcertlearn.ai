from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.gemini import generate_questions

router = APIRouter()

class QuestionRequest(BaseModel):
    specification: str
    example_questions: list[str]
    customer_id: str

@router.post("/generate-questions")
async def generate_questions_endpoint(request: QuestionRequest):
    try:
        return await generate_questions(request.specification, request.example_questions, request.customer_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ValidationError
from services.gemini import generate_questions
import json
import logging
import re
from typing import Dict, List

router = APIRouter()

class Question(BaseModel):
    id: int
    question: str
    correct_answer: str
    other_answers: Dict[str, str]

class QuestionRequest(BaseModel):
    specification: str
    example_questions: List[str]
    customer_id: str
    num_questions: int = 10
    num_answers: int = 10

@router.post("/generate-questions")
async def generate_questions_endpoint(request: QuestionRequest):
    try:
        gemini_response = await generate_questions(
            request.specification,
            request.example_questions,
            request.customer_id,
            request.num_questions,
            request.num_answers
        )
        text = gemini_response["candidates"][0]["content"]["parts"][0]["text"]
        # Remove markdown code block markers and 'json' prefix
        cleaned = re.sub(r'^```json\s*|^```|```$', '', text.strip(), flags=re.MULTILINE)
        try:
            questions_raw = json.loads(cleaned)
            questions = [Question(**q) for q in questions_raw]
            return {"questions": [q.dict() for q in questions]}
        except (Exception, ValidationError) as parse_error:
            logging.error(f"Failed to parse or validate Gemini response as JSON. Cleaned text: {cleaned}")
            return {"error": "Failed to parse or validate Gemini response as JSON.", "raw": cleaned}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

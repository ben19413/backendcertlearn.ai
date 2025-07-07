# app/gemini.py
import json
import asyncio
from typing import Dict, Any, Optional
from google import genai
import os
from pydantic import BaseModel
from schemas import QuestionResponse, ExamType
from prompts import PromptTemplates


class GeminiClient:
    """Async client for Gemini API with structured output support (using google.genai.Client)."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini client."""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable must be set")
        self.client = genai.Client(api_key=self.api_key)

    async def generate_questions_async(
        self,
        topic: str,
        num_questions: int,
        exam_type: ExamType,
        exam_pdf_bytes: bytes
    ) -> QuestionResponse:
        """Generate questions asynchronously with structured output, passing PDF as input using types.Part.from_bytes."""
        from google import genai as google_genai
        prompt = PromptTemplates.get_full_prompt(exam_type, topic, num_questions, None)
        loop = asyncio.get_event_loop()
        def call_gemini():
            pdf_part = google_genai.types.Part.from_bytes(
                data=exam_pdf_bytes,
                mime_type='application/pdf',
            )
            return self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[pdf_part, prompt],
                config={
                    "response_schema": QuestionResponse,
                    "response_mime_type": "application/json",
                },
            )
        response = await loop.run_in_executor(None, call_gemini)
        # Parse and validate response
        try:
            response_data = json.loads(response.text)
            if isinstance(response_data, list):
                response_data = {
                    "questions": response_data,
                    "exam_type": exam_type,
                    "total_questions": len(response_data)
                }
            else:
                response_data['exam_type'] = exam_type
                response_data['total_questions'] = len(response_data.get('questions', []))
            return QuestionResponse(**response_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from Gemini: {e}")
        except Exception as e:
            raise RuntimeError(f"Error generating questions: {e}")
import asyncio
from pathlib import Path
from typing import Dict, Any
import aiofiles
from models import ExamType, QuestionRequest, QuestionResponse
from gemini import GeminiClient


class QuestionGeneratorService:
    """Service class for generating exam questions with async IO operations."""
    
    def __init__(self, data_dir: str = "/data"):
        """Initialize the question generator service."""
        self.data_dir = Path(data_dir)
        self.gemini_client = GeminiClient()
    
    async def generate_questions(self, request: QuestionRequest) -> QuestionResponse:
        """Generate questions based on the request parameters."""
        try:
            # Load exam content from a .txt file
            exam_content = await self._load_exam_content(request.exam_type)
            # Generate questions using Gemini, passing user_info and exam_content
            response = await self.gemini_client.generate_questions_async(
                user_info=request.text,
                num_questions=request.num_questions,
                exam_type=request.exam_type,
                exam_content=exam_content
            )
            return response
        except Exception as e:
            raise RuntimeError(f"Failed to generate questions: {e}")

    async def _load_exam_content(self, exam_type: ExamType) -> str:
        """Load exam content from a .txt file."""
        file_path = self.data_dir / f"{exam_type.value}.txt"
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
                return await file.read()
        except FileNotFoundError:
            return ""
        except Exception as e:
            raise RuntimeError(f"Error loading content for {exam_type.value}: {e}")


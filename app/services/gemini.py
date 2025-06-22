import os
import httpx
from services.prompt import GEMINI_PROMPT_TEMPLATE

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


async def generate_questions(specification, example_questions, customer_id):
    prompt = GEMINI_PROMPT_TEMPLATE.format(
        specification=specification,
        example_questions=example_questions,
        customer_id=customer_id
    )
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(GEMINI_API_URL, headers=headers, params=params, json=data)
        response.raise_for_status()
        return response.json()

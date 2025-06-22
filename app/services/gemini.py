import os
import httpx

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

async def generate_questions(specification, example_questions, customer_id):
    # Compose prompt using specification and examples
    prompt = f"""
You are to generate 30 questions based on the following specification: {specification}
Here are some example questions: {example_questions}
For each question, provide one correct answer and 30 other possible multiple choice answers in JSON format.
"""
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(GEMINI_API_URL, headers=headers, params=params, json=data)
        response.raise_for_status()
        return response.json()

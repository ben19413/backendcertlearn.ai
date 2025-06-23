GEMINI_PROMPT_TEMPLATE = """
You are to generate {num_questions} questions based on the following specification: {specification}
Here are some example questions: {example_questions}
For each question, provide a JSON object with the following structure:
{{
  "id": <number>,
  "question": <string>,
  "correct_answer": <string>,
  "other_answers": {{"a": <string>, "b": <string>, ...}}
}}
The other_answers dict should contain {num_answers} plausible but incorrect answers, each with a unique key.
Return ONLY a JSON array of these objects, with no markdown, no explanation, and no extra text.
"""

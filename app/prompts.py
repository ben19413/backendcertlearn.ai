from typing import Dict
from schemas import ExamType


class PromptTemplates:
    """Collection of prompts for different exam types."""
    
    BASE_SYSTEM_PROMPT = """You are an expert AI assistant specialized in creating high-quality multiple-choice questions for standardized exams. 
    
Your task is to generate educational assessment questions based on the specified topic. For each question you create:
1. Write a clear, unambiguous question
2. Provide one correct answer
3. Create three plausible but incorrect distractors
4. Ensure all options are grammatically consistent and of similar length
5. Make questions that test comprehension, analysis, and critical thinking

"""

    EXAM_SPECIFIC_PROMPTS: Dict[ExamType, str] = {
        ExamType.CFA1: """
For SAT-style questions:
- Focus on reading comprehension, vocabulary in context, and analytical thinking
- Questions should test understanding of main ideas, supporting details, and author's tone
- Use academic vocabulary and formal language
- Emphasize critical analysis and evidence-based reasoning
""",
        
   
    }
    
    @classmethod
    def get_full_prompt(cls, exam_type: ExamType, num_questions: int) -> str:
        """Generate complete prompt for question generation."""
        exam_specific = cls.EXAM_SPECIFIC_PROMPTS.get(exam_type, "")
        return f"""{cls.BASE_SYSTEM_PROMPT}

{exam_specific}

Generate exactly {num_questions} multiple-choice questions based only on the EXAM CONTENT above, but you may use the USER BACKGROUND INFORMATION to personalize or contextualize the questions if appropriate. Each question should be appropriate for the {exam_type.value.upper()} exam format. Return the questions as a list of objects with the fields: question, correct_answer, and choices (where choices is a list of objects with label and text).

The exam content is in the attached pdf file.
"""
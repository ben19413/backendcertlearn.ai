from sqlalchemy.orm import Session
from models import QuestionDB

class QuestionRepository:
    def __init__(self, db_session: Session):
        self.db = db_session

    def add_question(self, user_email: str, question: str, answer_1: str, answer_2: str, answer_3: str, answer_4: str, solution: str):
        db_question = QuestionDB(
            user_email=user_email,
            question=question,
            answer_1=answer_1,
            answer_2=answer_2,
            answer_3=answer_3,
            answer_4=answer_4,
            solution=solution
        )
        self.db.add(db_question)
        self.db.commit()
        self.db.refresh(db_question)
        return db_question

    def get_questions_by_user(self, user_email: str):
        return self.db.query(QuestionDB).filter(QuestionDB.user_email == user_email).all()

    def get_all_questions(self):
        return self.db.query(QuestionDB).all()

    def get_question_by_user_and_id(self, user_email: str, question_id: int):
        return self.db.query(QuestionDB).filter(QuestionDB.user_email == user_email, QuestionDB.id == question_id).first()

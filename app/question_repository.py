from sqlalchemy.orm import Session
from models import QuestionDB, QuestionLogDB

class QuestionRepository:
    def __init__(self, db_session: Session):
        self.db = db_session

    def add_question(self, test_id: str, user_email: str, exam_type: str, question: str, answer_1: str, answer_2: str, answer_3: str, answer_4: str, solution: int):
        db_question = QuestionDB(
            test_id=test_id,
            user_email=user_email,
            exam_type=exam_type,
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

    def get_questions_by_test(self, test_id: str):
        return self.db.query(QuestionDB).filter(QuestionDB.test_id == test_id).all()

    def get_question_by_test_and_id(self, test_id: str, question_id: int):
        return self.db.query(QuestionDB).filter(QuestionDB.test_id == test_id, QuestionDB.id == question_id).first()

class QuestionLogRepository:
    def __init__(self, db_session: Session):
        self.db = db_session

    def add_log(self, question_id: int, user_email: str, selected_answer: int, liked: bool = None):
        log = QuestionLogDB(
            question_id=question_id,
            user_email=user_email,
            selected_answer=selected_answer,
            liked=liked
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_logs_for_question(self, question_id: int):
        return self.db.query(QuestionLogDB).filter(QuestionLogDB.question_id == question_id).all()

    def get_logs_for_user(self, user_email: str):
        return self.db.query(QuestionLogDB).filter(QuestionLogDB.user_email == user_email).all()

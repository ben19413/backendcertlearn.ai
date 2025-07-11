from sqlalchemy.orm import Session
from models import QuestionDB, AnswerLogDB, OpinionLogDB, QuestionSetDB

class QuestionRepository:
    def __init__(self, db_session: Session):
        self.db = db_session

    def add_question(self, test_id: int, exam_type: str, topic: str, topic_number: int, batch_number: int, question: str, answer_1: str, answer_2: str, answer_3: str, answer_4: str, solution: int):
        db_question = QuestionDB(
            test_id=test_id,
            exam_type=exam_type,
            topic=topic,
            topic_number=topic_number,
            batch_number=batch_number,
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

    def get_all_questions(self):
        return self.db.query(QuestionDB).all()

    def get_questions_by_test(self, test_id: str):
        return self.db.query(QuestionDB).filter(QuestionDB.test_id == test_id).all()

    def get_question_by_test_and_id(self, test_id: str, question_id: int):
        return self.db.query(QuestionDB).filter(QuestionDB.test_id == test_id, QuestionDB.id == question_id).first()

    def add_question_set_entry(self, question_set_id: int, question_id: int, user_email: str):
        entry = QuestionSetDB(
            question_set_id=question_set_id,
            question_id=question_id,
            user_email=user_email
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get_question_set_questions(self, question_set_id: int, user_email: str):
        
        entries = self.db.query(QuestionSetDB).filter(
            QuestionSetDB.question_set_id == question_set_id,
            QuestionSetDB.user_email == user_email
        ).all()
        question_ids = [e.question_id for e in entries]
        return self.db.query(QuestionDB).filter(QuestionDB.id.in_(question_ids)).all()

    def get_next_questions_for_topics(self, user_email: str, topics: list[str], num_questions_per_topic: int):
        next_questions = []
        for topic in topics:
            # Find the largest (batch_number, topic_number) already assigned for this user/topic
            subq = self.db.query(
                QuestionDB.topic_number,
                QuestionDB.batch_number
            ).join(
                QuestionSetDB, QuestionSetDB.question_id == QuestionDB.id
            ).filter(
                QuestionSetDB.user_email == user_email,
                QuestionDB.topic == topic
            ).order_by(
                QuestionDB.batch_number.desc(),
                QuestionDB.topic_number.desc()
            ).limit(1).first()
            # Get next questions for this topic
            query = self.db.query(QuestionDB).filter(QuestionDB.topic == topic)
            if subq:
                # Only get questions with batch_number > subq.batch_number or
                # batch_number == subq.batch_number and topic_number > subq.topic_number
                query = query.filter(
                    (QuestionDB.batch_number > subq.batch_number) |
                    ((QuestionDB.batch_number == subq.batch_number) & (QuestionDB.topic_number > subq.topic_number))
                )
            query = query.order_by(QuestionDB.batch_number, QuestionDB.topic_number).limit(num_questions_per_topic)
            next_questions.extend(query.all())
        return next_questions

class AnswerLogRepository:
    def __init__(self, db_session: Session):
        self.db = db_session

    def add_log(self, question_id: int, selected_answer: int, user_email: str):
        log = AnswerLogDB(
            question_id=question_id,
            selected_answer=selected_answer,
            user_email=user_email
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_logs_for_question(self, question_id: int):
        return self.db.query(AnswerLogDB).filter(AnswerLogDB.question_id == question_id).all()
    def get_logs_for_question(self, question_id: int):
        return self.db.query(QuestionLogDB).filter(QuestionLogDB.question_id == question_id).all()

    def get_logs_for_user(self, user_email: str):
        return self.db.query(AnswerLogDB).filter(AnswerLogDB.user_email == user_email).all()

class OpinionLogRepository:
    def __init__(self, db_session: Session):
        self.db = db_session

    def add_opinion(self, question_id: int, up: bool, user_email: str):  # <-- Add user_email param
        log = OpinionLogDB(
            question_id=question_id,
            up=up,
            user_email=user_email  # <-- Store user_email
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
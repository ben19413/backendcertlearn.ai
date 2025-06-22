from fastapi import FastAPI
from app.routers import questions

app = FastAPI()

app.include_router(questions.router)

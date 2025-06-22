from fastapi import FastAPI
from routers import questions

app = FastAPI()

app.include_router(questions.router)

# @app.post("/test")
# def test_endpoint(data: dict):
#     return {"message": "App is working!", "data": data}

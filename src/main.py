from fastapi import FastAPI
from src.auth.views import router as user_app_router

app = FastAPI(
    title='Todo List'
)

app.include_router(
    user_app_router
)

#!/bin/sh

sleep 10

alembic upgrade head

cd /app/todolist_app

gunicorn src.auth.router:user_app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind=0.0.0.0:8000 --reload

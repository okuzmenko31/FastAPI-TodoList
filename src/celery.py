from celery import Celery

app = Celery('src', broker='redis://redis:6379')
app.autodiscover_tasks()

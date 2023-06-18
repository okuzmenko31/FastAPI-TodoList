FROM python:3.9

ENV PYTHONBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /app/todolist_app
COPY . .

COPY requirements/base.txt /app/requirements/base.txt
COPY start.sh /app/start.sh
COPY celery.sh /app/celery.sh
RUN pip install -r /app/requirements/base.txt
RUN chmod +x /app/start.sh
RUN chmod +x /app/celery.sh

EXPOSE 8000

CMD ["/app/start.sh"]
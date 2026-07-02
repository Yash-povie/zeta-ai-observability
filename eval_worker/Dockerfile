FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/eval_worker
COPY ../shared_observability /app/shared_observability
COPY ../alembic /app/alembic
COPY ../alembic.ini /app/alembic.ini

ENV PYTHONUNBUFFERED=1
EXPOSE 8002

CMD ["uvicorn", "eval_worker.api:app", "--host", "0.0.0.0", "--port", "8002"]
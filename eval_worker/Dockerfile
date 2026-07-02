FROM python:3.11-slim

WORKDIR /app

COPY eval_worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY eval_worker ./eval_worker
COPY shared_observability ./shared_observability
COPY alembic ./alembic
COPY alembic.ini .

ENV PYTHONUNBUFFERED=1
EXPOSE 8002

CMD ["uvicorn", "eval_worker.api:app", "--host", "0.0.0.0", "--port", "8002"]

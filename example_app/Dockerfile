FROM python:3.11-slim

WORKDIR /app

COPY example_app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY example_app ./example_app
COPY shared_observability ./shared_observability

ENV PYTHONUNBUFFERED=1
EXPOSE 8001

CMD ["uvicorn", "example_app.main:app", "--host", "0.0.0.0", "--port", "8001"]

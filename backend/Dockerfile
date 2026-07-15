FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app

# SQLite file will live in /data volume when configured
ENV DATABASE_URL=sqlite:////data/ipam.db \
    CORS_ORIGINS=http://localhost,http://localhost:80,http://127.0.0.1,http://127.0.0.1:80,http://localhost:5173,http://localhost:5175

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

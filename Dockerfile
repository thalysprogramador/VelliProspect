# Velli Prospect V3 - Production Web Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV FLET_FORCE_WEB_SERVER true

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render injeta $PORT automaticamente
CMD ["sh", "-c", "python main.py"]

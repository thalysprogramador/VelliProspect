# Velli Prospect V3 - Production Web Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLET_FORCE_WEB_SERVER=true

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render injeta $PORT (default 10000). Precisamos repassar para o Flet.
CMD ["sh", "-c", "FLET_SERVER_PORT=${PORT:-10000} FLET_SERVER_IP=0.0.0.0 python main.py"]

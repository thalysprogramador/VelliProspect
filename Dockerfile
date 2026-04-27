# Velli Prospect V3 - Professional Web Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 8080

WORKDIR /app

# Instala bibliotecas de sistema essenciais para o Flet e busca
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgtk-3-0 \
    libpango-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

# Inicia o app garantindo que ele escute na porta correta
CMD ["python", "main.py"]

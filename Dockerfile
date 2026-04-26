# Velli Prospect V3 - Web Ready Dockerfile (Render Optimized)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 8080

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expõe a porta que o Render usará
EXPOSE 8080

# Inicia via Python direto para melhor estabilidade no Render
CMD ["python", "main.py"]

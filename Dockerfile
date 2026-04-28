# Velli Prospect V3 - Professional Web Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 8080

WORKDIR /app

# Removemos dependências GTK, desnecessárias para modo Web.

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

# Inicia o app usando o servidor web nativo do Flet
CMD ["sh", "-c", "flet run --web --port ${PORT:-8080} main.py"]

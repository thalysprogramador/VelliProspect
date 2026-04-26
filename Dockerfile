# Velli Prospect V3 - Web Ready Dockerfile
FROM python:3.11-slim

# Evita geração de arquivos .pyc e permite logs em tempo real
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV FLET_SERVER_PORT 8080
ENV FLET_SERVER_IP 0.0.0.0

WORKDIR /app

# Instala dependências de sistema (necessárias para algumas libs de rede/scraping)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia apenas requirements primeiro para aproveitar cache do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código
COPY . .

# Expõe a porta que o Flet usará
EXPOSE 8080

# Comando para rodar o app no modo Web (Web Server)
# --web especifica que o Flet deve rodar como servidor web
CMD ["flet", "run", "main.py", "--web", "--port", "8080"]

# 1) Imagem base Python
FROM python:3.11-slim AS base

# 2) Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    FLASK_ENV=production

# 3) Diretório de trabalho
WORKDIR /app

# 4) Instala dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
  && rm -rf /var/lib/apt/lists/*

# 5) Copia requirements e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6) Copia todo o código
COPY . .

# 7) Exponha porta da app
EXPOSE 65000

# 8) Comando padrão
CMD ["gunicorn", "--bind", "0.0.0.0:65000", "app:app", "--workers", "3"]

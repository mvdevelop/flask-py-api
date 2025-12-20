
# Imagem base

FROM python:3.11-slim

# Variáveis de ambiente

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production

# Diretório de trabalho

WORKDIR /app

# Dependências do sistema

RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ==============================
# Dependências Python
# ==============================
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ==============================
# Copia aplicação
# ==============================
COPY . .

# ==============================
# Diretório de uploads
# ==============================
RUN mkdir -p uploads/produtos && \
    chmod -R 755 uploads

# ==============================
# Porta (informativa)
# ==============================
EXPOSE 5000

# ==============================
# Start (PRODUÇÃO)
# ==============================
CMD ["gunicorn", "--bind", "0.0.0.0:${PORT}", "run:app"]


FROM python:3.11-slim

# ==============================
# Variáveis de ambiente
# ==============================
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# ==============================
# Diretório de trabalho
# ==============================
WORKDIR /app

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
# Porta (informativa)
# ==============================
EXPOSE 5000

# ==============================
# Start (Render)
# ==============================
CMD ["gunicorn", "--bind", "0.0.0.0:${PORT}", "run:app"]

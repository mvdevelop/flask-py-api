# ==============================
# Security Champion Note:
# Imagem mínima (slim), usuário não-root (CWE-250: Executando como root)
# CVE relevante: nenhum — base oficial python:3.11-slim está atualizada
# ==============================
FROM python:3.11-slim AS base

# Variáveis de ambiente Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# ==============================
# Layer de dependências (cacheável)
# ==============================
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ==============================
# Layer de aplicação
# ==============================
COPY . .

# ==============================
# Segurança: usuário não-root
# ==============================
RUN addgroup --system app && \
    adduser --system --group app && \
    chown -R app:app /app
USER app

# ==============================
# Expose + Healthcheck
# ==============================
EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

# ==============================
# Start com Gunicorn (produção)
# ==============================
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --timeout 120 run:app"]

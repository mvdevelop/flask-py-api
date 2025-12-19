
"""
Ponto de entrada para Vercel Serverless Functions
A Vercel espera um handler chamado 'app' ou 'application'
"""
import sys
import os

# Adiciona o diretório app ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.app import create_app
from flask import send_from_directory

# Cria a aplicação Flask
app = create_app('production')

# 🔹 Health check otimizado para Vercel
@app.route("/api")
def vercel_index():
    return {
        "message": "PyStore API on Vercel",
        "status": "online",
        "provider": "Vercel Serverless",
        "endpoints": {
            "health": "/api/health",
            "docs": "/api/swagger"
        }
    }

# 🔹 Otimização para Serverless
@app.before_request
def handle_serverless():
    """Otimizações para ambiente serverless"""
    # Desabilita algumas features que não funcionam bem no serverless
    if not hasattr(app, 'db_initialized'):
        # Inicializações leves aqui
        app.db_initialized = True

# Exporta o handler para Vercel
application = app  # A Vercel procura por 'application'


from app.app import create_app
import os

# Detecta ambiente
env = os.getenv('FLASK_ENV', 'production')

# Cria aplicação
app = create_app(env)

# 🔹 Swagger JSON (com fallback robusto)
@app.route("/static/swagger.json")
def swagger_json():
    """Serve o arquivo swagger.json ou retorna um fallback"""
    try:
        from flask import send_from_directory
        import os
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths = [
            os.path.join(base_dir, "app", "swagger", "swagger.json"),
            os.path.join(base_dir, "static", "swagger.json"),
            os.path.join(base_dir, "swagger.json"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                directory = os.path.dirname(path)
                filename = os.path.basename(path)
                return send_from_directory(directory, filename)
        
        # Se não encontrou, cria um fallback
        raise FileNotFoundError
        
    except:
        # Fallback JSON para Swagger
        return {
            "openapi": "3.0.0",
            "info": {
                "title": app.config.get('APP_NAME', 'PyStore API'),
                "version": "1.0.0",
                "description": "Documentação da API PyStore"
            },
            "servers": [
                {
                    "url": "/",
                    "description": "Servidor atual"
                }
            ],
            "paths": {},
            "components": {
                "securitySchemes": {
                    "BearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT"
                    }
                }
            }
        }, 200

# 🔹 Health check para Docker/Kubernetes
@app.route("/health")
def health():
    """Endpoint para health checks"""
    return {
        "status": "healthy",
        "service": "pystore-api",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }, 200


# ⚠️ ESTE BLOCO SÓ É EXECUTADO EM DESENVOLVIMENTO LOCAL
# Em produção, use: gunicorn run:app
if __name__ == "__main__":
    import sys
    
    # Verifica se está tentando rodar em produção com servidor de desenvolvimento
    if os.getenv('FLASK_ENV') == 'production':
        print("⚠️  AVISO: Usando servidor de desenvolvimento em modo produção!")
        print("   Recomendado: gunicorn --bind 0.0.0.0:5000 run:app")
        print("   Continuando em 3 segundos...")
        import time
        time.sleep(3)
    
    # Configurações
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print(f"🚀 Iniciando PyStore API em {host}:{port}")
    print(f"📁 Ambiente: {env}")
    print(f"🐛 Debug: {debug}")
    
    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=debug
        )
    except KeyboardInterrupt:
        print("\n👋 Encerrando aplicação...")
        sys.exit(0)

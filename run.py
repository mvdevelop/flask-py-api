
from app.app import create_app
import os
import sys

# Configuração do ambiente
env = os.getenv('FLASK_ENV', 'production')

# Detecta se está na Vercel
is_vercel = os.environ.get('VERCEL') == '1'

if is_vercel:
    print("🌐 Ambiente detectado: Vercel")
    # Na Vercel, o entry point é api/index.py
    env = 'production'
else:
    print("💻 Ambiente detectado: Local/Docker")

# Cria a aplicação
app = create_app(env)

# 🔹 Rota para servir swagger.json dinamicamente
@app.route("/static/swagger.json")
def swagger_json():
    """Serve o arquivo swagger.json apropriado para o ambiente"""
    try:
        from flask import send_from_directory
        import os
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Decide qual swagger usar baseado no ambiente
        if is_vercel:
            filename = "swagger_vercel.json"
            possible_paths = [
                os.path.join(base_dir, "static", filename),
                os.path.join(base_dir, filename),
                os.path.join(base_dir, "app", "swagger", filename),
            ]
        else:
            filename = "swagger_local.json"
            possible_paths = [
                os.path.join(base_dir, "static", "swagger.json"),
                os.path.join(base_dir, "static", filename),
                os.path.join(base_dir, "swagger.json"),
                os.path.join(base_dir, "app", "swagger", "swagger.json"),
            ]
        
        for path in possible_paths:
            if os.path.exists(path):
                directory = os.path.dirname(path)
                filename = os.path.basename(path)
                return send_from_directory(directory, filename)
        
        # Fallback se não encontrar arquivo
        raise FileNotFoundError("Swagger file not found")
        
    except Exception as e:
        # JSON de fallback minimalista
        from flask import jsonify
        return jsonify({
            "openapi": "3.0.0",
            "info": {
                "title": "PyStore API",
                "version": "1.0.0",
                "description": "API Documentation"
            },
            "paths": {
                "/": {
                    "get": {
                        "summary": "API Root",
                        "responses": {
                            "200": {
                                "description": "API is running"
                            }
                        }
                    }
                },
                "/health": {
                    "get": {
                        "summary": "Health Check",
                        "responses": {
                            "200": {
                                "description": "Service is healthy"
                            }
                        }
                    }
                }
            }
        }), 200

# ⚠️ BLOCO DE EXECUÇÃO APENAS PARA DESENVOLVIMENTO LOCAL
# Na Vercel, o entry point é api/index.py
if __name__ == "__main__" and not is_vercel:
    import datetime
    
    # Configurações do servidor
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    # Banner de inicialização
    print("=" * 60)
    print(f"🚀 Iniciando PyStore API")
    print(f"📍 Endereço: {host}:{port}")
    print(f"📁 Ambiente: {env}")
    print(f"🐛 Debug: {debug}")
    print(f"🕐 Início: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Aviso se for produção com servidor de desenvolvimento
    if env == 'production' and debug:
        print("⚠️  AVISO: Debug mode ativado em produção!")
        print("   Use: gunicorn --bind 0.0.0.0:5000 run:app")
        import time
        time.sleep(2)
    
    try:
        # Inicia o servidor Flask
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=debug and not is_vercel
        )
    except KeyboardInterrupt:
        print("\n👋 Encerrando aplicação...")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")
        sys.exit(1)
    
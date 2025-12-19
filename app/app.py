
from flask import Flask, jsonify, send_from_directory, request
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os
import datetime
import traceback

def create_app(config_name='default'):
    """Factory function para criar a aplicação Flask"""
    
    print("=" * 60)
    print(f"🚀 Criando app Flask - Ambiente: {config_name}")
    print("=" * 60)
    
    try:
        app = Flask(__name__)
        
        # 🔧 CONFIGURAÇÕES
        app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
        app.config['PROPAGATE_EXCEPTIONS'] = True
        
        # 🔐 JWT
        jwt_secret = os.environ.get("JWT_SECRET_KEY", "dev-secret-key")
        app.config["JWT_SECRET_KEY"] = jwt_secret
        JWTManager(app)
        print(f"🔐 JWT configurado")

        # 🔓 CORS
        CORS(app, resources={r"/*": {"origins": "*"}})

        # 🗄️ MONGODB ATLAS - CORREÇÃO CRÍTICA
        mongo_uri = os.environ.get("MONGO_URI")
        mongo_db_name = os.environ.get("MONGO_DB", "py_store")
        
        # Inicializa app.db como None por padrão
        app.db = None
        
        if mongo_uri:
            try:
                from pymongo import MongoClient
                print(f"🔗 Conectando ao MongoDB...")
                
                client = MongoClient(
                    mongo_uri,
                    serverSelectionTimeoutMS=10000,
                    retryWrites=True,
                    w="majority"
                )
                
                # Testa conexão
                client.admin.command('ping')
                app.db = client[mongo_db_name]
                
                print(f"✅ MongoDB Atlas conectado!")
                print(f"📊 Database: {mongo_db_name}")
                
            except Exception as e:
                print(f"❌ ERRO MongoDB: {type(e).__name__}")
                print(f"   Detalhes: {str(e)[:200]}")
                app.db = None  # Garante que seja None em caso de erro
        else:
            print("⚠️  MONGO_URI não configurada")
            app.db = None

        # 🔹 ROTA INICIAL CORRIGIDA
        @app.route("/", methods=["GET"])
        def index():
            # ⬇️ CORREÇÃO: Use 'app.db is not None' em vez de 'app.db'
            db_status = "connected" if app.db is not None else "disconnected"
            
            return jsonify({
                "message": "PyStore API 🚀",
                "status": "online",
                "database": db_status,  # Usa a variável corrigida
                "environment": config_name,
                "deployed_on": "Vercel" if os.environ.get('VERCEL') else "Local/Docker",
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "endpoints": {
                    "health": "/health",
                    "api": "/api",
                    "docs": "/docs"
                }
            })

        # 🔹 HEALTH CHECK CORRIGIDO
        @app.route("/health", methods=["GET"])
        def health_check():
            # ⬇️ CORREÇÃO: Mesma lógica aqui
            db_status = "connected" if app.db is not None else "disconnected"
            
            health_status = {
                "status": "healthy" if app.db is not None else "degraded",
                "service": "pystore-api",
                "database": db_status,
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "environment": config_name,
                "version": "1.0.0"
            }
            status_code = 200 if app.db is not None else 503
            return jsonify(health_status), status_code

        # 🔹 UPLOADS - Adaptado para Vercel
        @app.route("/uploads/produtos/<filename>", methods=["GET"])
        def serve_product_image(filename):
            if os.environ.get('VERCEL'):
                return jsonify({
                    "error": "File upload not available on Vercel",
                    "solution": "Use external image URLs (Cloudinary, S3, etc.)",
                    "filename": filename
                }), 501
            else:
                return jsonify({"error": "File not found"}), 404

        # 🔹 ROTAS DA API
        print("📦 Carregando blueprints...")
        
        try:
            from app.routes.product_routes import product_routes
            app.register_blueprint(product_routes, url_prefix="/api")
            print("✅ product_routes carregado")
        except ImportError as e:
            print(f"⚠️  product_routes não carregado: {e}")
            
            @app.route("/api/produtos", methods=["GET"])
            def produtos_fallback():
                return jsonify({
                    "products": [],
                    "message": "Products module not available",
                    "status": "fallback"
                }), 200
        
        # 🔹 SWAGGER UI
        try:
            SWAGGER_URL = "/docs"
            API_URL = "/static/swagger.json"
            
            swaggerui_blueprint = get_swaggerui_blueprint(
                SWAGGER_URL,
                API_URL,
                config={"app_name": "PyStore API"}
            )
            app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
            print("✅ Swagger UI configurado")
        except Exception as e:
            print(f"⚠️  Swagger não disponível: {e}")

        # 🔹 ROTA PARA SWAGGER.JSON
        @app.route("/static/swagger.json")
        def serve_swagger():
            """Serve swagger.json ou fallback"""
            try:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                possible_paths = [
                    os.path.join(base_dir, "..", "static", "swagger.json"),
                    os.path.join(base_dir, "swagger.json"),
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        directory = os.path.dirname(path)
                        filename = os.path.basename(path)
                        return send_from_directory(directory, filename)
                
                raise FileNotFoundError
                
            except:
                # Fallback JSON
                return jsonify({
                    "openapi": "3.0.0",
                    "info": {
                        "title": "PyStore API",
                        "version": "1.0.0",
                        "description": "API Documentation"
                    },
                    "paths": {
                        "/": {"get": {"summary": "API Root"}},
                        "/health": {"get": {"summary": "Health Check"}},
                        "/api/produtos": {"get": {"summary": "List Products"}}
                    }
                }), 200

        # 🔹 HANDLERS DE ERRO
        @app.errorhandler(404)
        def not_found(error):
            return jsonify({
                "error": "Not found",
                "message": "The requested endpoint does not exist"
            }), 404

        @app.errorhandler(500)
        def internal_error(error):
            return jsonify({
                "error": "Internal server error",
                "message": "An unexpected error occurred"
            }), 500

        print("=" * 60)
        print("✅ Aplicação Flask criada com sucesso!")
        print("=" * 60)
        
        return app
        
    except Exception as e:
        print(f"❌ ERRO FATAL ao criar app: {e}")
        traceback.print_exc()
        
        # Fallback mínimo
        app = Flask(__name__)
        
        @app.route('/')
        def fatal_fallback():
            return jsonify({
                "error": "Application initialization failed",
                "message": str(e)[:200]
            }), 500
        
        return app


from flask import Flask, jsonify, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os
import datetime
import traceback

def create_app(config_name='default'):
    """Factory function para criar a aplicação Flask"""
    
    # 🔍 DEBUG: Informações sobre o ambiente
    print("=" * 60)
    print(f"🚀 Criando app Flask - Ambiente: {config_name}")
    print(f"📁 Diretório: {os.getcwd()}")
    print(f"🔧 VERCEL: {os.environ.get('VERCEL', 'Não')}")
    print(f"🔧 MONGO_URI configurada: {'✅' if os.environ.get('MONGO_URI') else '❌'}")
    print("=" * 60)
    
    try:
        app = Flask(__name__)
        
        # 🔧 CONFIGURAÇÕES ESPECÍFICAS PARA VERCEL
        app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False  # Otimização
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 300  # Cache
        app.config['PROPAGATE_EXCEPTIONS'] = True  # Melhor tratamento de erros
        
        # 🔐 JWT - Usa variável de ambiente
        jwt_secret = os.environ.get(
            "JWT_SECRET_KEY", 
            "dev-secret-key-change-in-production"
        )
        app.config["JWT_SECRET_KEY"] = jwt_secret
        print(f"🔐 JWT Secret configurado: {'✅' if jwt_secret else '❌'}")
        
        JWTManager(app)

        # 🔓 CORS
        CORS(
            app,
            resources={r"/*": {"origins": "*"}},
            allow_headers="*",
            methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        )

        # 🗄️ MONGODB ATLAS - Conexão segura
        mongo_uri = os.environ.get("MONGO_URI")
        mongo_db_name = os.environ.get("MONGO_DB", "py_store")
        
        if mongo_uri:
            try:
                from pymongo import MongoClient
                print(f"🔗 Conectando ao MongoDB...")
                
                # Para debug seguro, mostra só parte da URI
                safe_uri = mongo_uri
                if '@' in mongo_uri:
                    safe_uri = 'mongodb+srv://***:***@' + mongo_uri.split('@')[1]
                print(f"   URI: {safe_uri[:80]}...")
                
                client = MongoClient(
                    mongo_uri,
                    serverSelectionTimeoutMS=10000,  # 10 segundos timeout
                    retryWrites=True,
                    w="majority",
                    connectTimeoutMS=10000,
                    socketTimeoutMS=10000
                )
                
                # Testa conexão
                print("   Testando conexão...")
                client.admin.command('ping')
                app.db = client[mongo_db_name]
                
                print(f"✅ MongoDB Atlas conectado!")
                print(f"📊 Database: {mongo_db_name}")
                
                # Lista collections (para debug)
                try:
                    collections = app.db.list_collection_names()
                    print(f"📁 Collections: {collections}")
                except:
                    print("📁 Collections: Não foi possível listar")
                
            except Exception as e:
                print(f"❌ ERRO MongoDB: {type(e).__name__}")
                print(f"   Detalhes: {str(e)[:200]}")
                app.db = None
        else:
            print("⚠️  MONGO_URI não configurada no ambiente")
            app.db = None

        # 📁 UPLOADS - Configuração adaptada
        app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1MB máximo
        
        # Cria diretório de uploads se não for Vercel
        if not os.environ.get('VERCEL'):
            try:
                upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads', 'produtos')
                os.makedirs(upload_folder, exist_ok=True)
                app.config["UPLOAD_FOLDER"] = upload_folder
                print(f"📁 Upload folder: {upload_folder}")
            except:
                pass

        # 🔹 ROTA INICIAL OTIMIZADA
        @app.route("/", methods=["GET"])
        def index():
            """Endpoint raiz da API"""
            return jsonify({
                "message": "PyStore API 🚀",
                "status": "online",
                "database": "connected" if app.db else "disconnected",
                "environment": config_name,
                "deployed_on": "Vercel" if os.environ.get('VERCEL') else "Local/Docker",
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "endpoints": {
                    "health": "/health",
                    "api": "/api",
                    "docs": "/docs"
                }
            })

        # 🔹 HEALTH CHECK MELHORADO
        @app.route("/health", methods=["GET"])
        def health_check():
            """Health check para monitoramento"""
            health_status = {
                "status": "healthy" if app.db else "degraded",
                "service": "pystore-api",
                "database": "connected" if app.db else "disconnected",
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "environment": config_name,
                "version": "1.0.0"
            }
            status_code = 200 if app.db else 503
            return jsonify(health_status), status_code

        # 🔹 UPLOADS - Endpoint adaptado para Vercel
        @app.route("/uploads/produtos/<filename>", methods=["GET"])
        def serve_product_image(filename):
            """Serve imagens ou retorna mensagem no Vercel"""
            if os.environ.get('VERCEL'):
                return jsonify({
                    "error": "File upload not available on Vercel",
                    "solution": "Use external image URLs (Cloudinary, S3, etc.)",
                    "filename": filename
                }), 501
            else:
                # Em ambiente local/Docker, tenta servir o arquivo
                try:
                    upload_folder = app.config.get("UPLOAD_FOLDER")
                    if upload_folder and os.path.exists(os.path.join(upload_folder, filename)):
                        return send_from_directory(upload_folder, filename)
                    else:
                        return jsonify({"error": "File not found"}), 404
                except:
                    return jsonify({"error": "File service unavailable"}), 500

        # 🔹 ROTAS DA API - Carregamento seguro
        print("📦 Carregando blueprints...")
        
        # Produtos
        try:
            from app.routes.product_routes import product_routes
            app.register_blueprint(product_routes, url_prefix="/api")
            print("✅ product_routes carregado")
        except ImportError as e:
            print(f"⚠️  product_routes não carregado: {e}")
            
            # Rota fallback para produtos
            @app.route("/api/produtos", methods=["GET"])
            def produtos_fallback():
                return jsonify({
                    "products": [],
                    "message": "Products module not available",
                    "status": "fallback"
                }), 200
        
        # Usuários
        try:
            from app.routes.user_routes import user_routes
            app.register_blueprint(user_routes, url_prefix="/api")
            print("✅ user_routes carregado")
        except ImportError:
            print("⚠️  user_routes não disponível")
        
        # Admin
        try:
            from app.routes.admin_routes import admin_routes
            app.register_blueprint(admin_routes, url_prefix="/api")
            print("✅ admin_routes carregado")
        except ImportError:
            print("⚠️  admin_routes não disponível")

        # 🔹 SWAGGER UI - Configuração dinâmica
        try:
            SWAGGER_URL = "/docs"
            API_URL = "/static/swagger.json"
            
            # Verifica qual swagger usar
            if os.environ.get('VERCEL'):
                API_URL = "/static/swagger_vercel.json"
                print("📘 Swagger: Usando versão Vercel")
            else:
                print("📘 Swagger: Usando versão local")
            
            swaggerui_blueprint = get_swaggerui_blueprint(
                SWAGGER_URL,
                API_URL,
                config={
                    "app_name": f"PyStore API ({'Vercel' if os.environ.get('VERCEL') else 'Local'})",
                    "docExpansion": "none"
                }
            )
            app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
            print("✅ Swagger UI configurado")
        except Exception as e:
            print(f"⚠️  Swagger não disponível: {e}")
            
            # Rota fallback para docs
            @app.route("/docs")
            def docs_fallback():
                return jsonify({
                    "message": "Swagger UI not available",
                    "endpoints": {
                        "health": "/health",
                        "api": "/api/produtos"
                    }
                }), 200

        # 🔹 HANDLERS DE ERRO GLOBAL
        @app.errorhandler(404)
        def not_found(error):
            return jsonify({
                "error": "Not found",
                "message": "The requested endpoint does not exist",
                "path": request.path if 'request' in locals() else "unknown"
            }), 404

        @app.errorhandler(500)
        def internal_error(error):
            print(f"🔥 ERRO 500: {error}")
            return jsonify({
                "error": "Internal server error",
                "message": "An unexpected error occurred",
                "timestamp": datetime.datetime.utcnow().isoformat()
            }), 500

        @app.errorhandler(Exception)
        def handle_all_exceptions(error):
            print(f"🔥 ERRO não tratado: {error}")
            traceback.print_exc()
            return jsonify({
                "error": "Server error",
                "message": str(error)[:200],
                "type": type(error).__name__
            }), 500

        print("=" * 60)
        print("✅ Aplicação Flask criada com sucesso!")
        print("=" * 60)
        
        return app
        
    except Exception as e:
        print(f"❌ ERRO FATAL ao criar app: {e}")
        traceback.print_exc()
        
        # Retorna um app mínimo em caso de falha catastrófica
        app = Flask(__name__)
        
        @app.route('/')
        def fatal_fallback():
            return jsonify({
                "error": "Application initialization failed",
                "message": str(e)[:200],
                "status": "error"
            }), 500
        
        @app.route('/health')
        def fatal_health():
            return jsonify({"status": "failed"}), 503
        
        return app

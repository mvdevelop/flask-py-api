
from flask import Flask, jsonify, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from pymongo import MongoClient
import os
import datetime

def create_app(config_name='default'):
    app = Flask(__name__)

    # 🔧 CONFIGURAÇÕES DINÂMICAS
    # ============================================
    
    # 🔐 JWT - Agora via variável de ambiente
    app.config["JWT_SECRET_KEY"] = os.environ.get(
        "JWT_SECRET_KEY", 
        "super-secret-admin-key"  # Fallback para desenvolvimento
    )
    JWTManager(app)

    # 🗄️ MONGODB ATLAS
    # ============================================
    mongo_uri = os.environ.get(
        "MONGO_URI",
        "mongodb://localhost:27017/"  # Fallback local
    )
    
    mongo_db_name = os.environ.get("MONGO_DB", "py_store")
    
    try:
        # Conecta ao MongoDB Atlas
        client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,  # Timeout de 5 segundos
            retryWrites=True,
            w="majority"
        )
        
        # Testa a conexão
        client.admin.command('ping')
        
        # Seleciona o banco de dados
        app.db = client[mongo_db_name]
        
        print(f"✅ Conectado ao MongoDB Atlas: {mongo_db_name}")
        print(f"📊 URI: {mongo_uri.split('@')[1] if '@' in mongo_uri else mongo_uri}")
        
    except Exception as e:
        print(f"⚠️  Aviso: Não foi possível conectar ao MongoDB")
        print(f"   Erro: {e}")
        print(f"   URI usada: {mongo_uri.split('@')[0] if '@' in mongo_uri else mongo_uri}...")
        print(f"   Usando modo offline (apenas leitura)")
        app.db = None

    # 🔓 CORS TOTALMENTE ABERTO (mantido)
    # ============================================
    CORS(
        app,
        resources={r"/*": {"origins": "*"}},
        allow_headers="*",
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )

    # 📁 CONFIGURAÇÃO DE UPLOAD
    # ============================================
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "..", "uploads", "produtos")
    
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB

    # Cria diretório se não existir
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # 🔹 ROTA INICIAL MELHORADA
    # ============================================
    @app.route("/", methods=["GET"])
    def index():
        return jsonify({
            "message": "API PyStore rodando 🚀",
            "status": "online",
            "database": "conectado" if app.db else "offline",
            "environment": os.environ.get("FLASK_ENV", "production"),
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "endpoints": {
                "api": "/api",
                "health": "/health",
                "swagger": "/swagger",
                "uploads": "/uploads/produtos/<filename>"
            }
        })

    # 🔹 HEALTH CHECK (novo - essencial para Docker)
    # ============================================
    @app.route("/health", methods=["GET"])
    def health_check():
        health_status = {
            "status": "healthy" if app.db else "degraded",
            "database": "connected" if app.db else "disconnected",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "service": "PyStore API",
            "version": "1.0.0"
        }
        
        status_code = 200 if app.db else 503  # 503 se DB offline
        return jsonify(health_status), status_code

    # 🔹 ROTA PÚBLICA PARA SERVER IMAGENS
    # ============================================
    @app.route("/uploads/produtos/<filename>")
    def serve_product_image(filename):
        return send_from_directory(
            app.config["UPLOAD_FOLDER"],
            filename
        )

    # 🔹 ROTA DE STATUS DO BANCO (para debug)
    # ============================================
    @app.route("/db-status", methods=["GET"])
    def db_status():
        if not app.db:
            return jsonify({
                "status": "offline",
                "message": "Banco de dados não conectado"
            }), 503
        
        try:
            # Tenta listar collections
            collections = app.db.list_collection_names()
            
            # Conta documentos em cada collection
            stats = {}
            for coll in collections:
                try:
                    count = app.db[coll].count_documents({})
                    stats[coll] = {
                        "documents": count,
                        "status": "ok"
                    }
                except:
                    stats[coll] = {
                        "documents": "error",
                        "status": "error"
                    }
            
            return jsonify({
                "status": "online",
                "database": os.environ.get("MONGO_DB", "py_store"),
                "collections": collections,
                "stats": stats,
                "connection": "MongoDB Atlas" if "@cluster" in mongo_uri else "MongoDB Local"
            }), 200
            
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

    # 🔹 ROTAS DA API
    # ============================================
    try:
        from app.routes.user_routes import user_routes
        from app.routes.product_routes import product_routes
        from app.routes.admin_routes import admin_routes
        
        app.register_blueprint(user_routes, url_prefix="/api")
        app.register_blueprint(product_routes, url_prefix="/api")
        app.register_blueprint(admin_routes, url_prefix="/api")
        
    except ImportError as e:
        print(f"⚠️  Aviso: Algum blueprint não pôde ser carregado: {e}")
        print("   As rotas correspondentes estarão indisponíveis")

    # 🔹 SWAGGER
    # ============================================
    SWAGGER_URL = "/swagger"
    API_URL = "/static/swagger.json"

    try:
        swaggerui_blueprint = get_swaggerui_blueprint(
            SWAGGER_URL,
            API_URL,
            config={
                "app_name": "PyStore API",
                "database": "MongoDB Atlas" if app.db else "Offline Mode"
            }
        )
        app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
    except:
        print("⚠️  Swagger UI não disponível - verifique se swagger.json existe")

    # 🔹 TRATAMENTO DE ERROS GLOBAL
    # ============================================
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": "Endpoint não encontrado",
            "message": "Verifique a documentação em /swagger"
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "error": "Erro interno do servidor",
            "message": "Contate o administrador do sistema"
        }), 500

    return app


from flask import Flask, jsonify, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os
import datetime

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # 🔧 CONFIGURAÇÕES ESPECÍFICAS PARA VERCEL
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False  # Otimização
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 300  # Cache
    
    # 🔐 JWT - Usa variável de ambiente
    app.config["JWT_SECRET_KEY"] = os.environ.get(
        "JWT_SECRET_KEY", 
        "vercel-secret-key-change-in-production"
    )
    JWTManager(app)

    # 🔓 CORS
    CORS(
        app,
        resources={r"/*": {"origins": "*"}},
        allow_headers="*",
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )

    # 🗄️ MONGODB ATLAS (igual, funciona na Vercel)
    mongo_uri = os.environ.get("MONGO_URI")
    mongo_db_name = os.environ.get("MONGO_DB", "py_store")
    
    if mongo_uri:
        try:
            from pymongo import MongoClient
            client = MongoClient(
                mongo_uri,
                serverSelectionTimeoutMS=5000,
                retryWrites=True,
                w="majority"
            )
            client.admin.command('ping')
            app.db = client[mongo_db_name]
            print(f"✅ MongoDB Atlas conectado")
        except Exception as e:
            print(f"⚠️  MongoDB não disponível: {e}")
            app.db = None
    else:
        print("⚠️  MONGO_URI não configurada")
        app.db = None

    # 📁 UPLOADS - DESABILITADO NA VERCEL (Serverless não tem storage)
    app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1MB apenas
    
    # 🔹 ROTA INICIAL OTIMIZADA
    @app.route("/", methods=["GET"])
    def index():
        return jsonify({
            "message": "PyStore API on Vercel 🚀",
            "status": "online",
            "database": "connected" if app.db else "disconnected",
            "provider": "Vercel Serverless",
            "environment": os.environ.get("VERCEL_ENV", "production"),
            "region": os.environ.get("VERCEL_REGION", "unknown"),
            "timestamp": datetime.datetime.utcnow().isoformat()
        })

    # 🔹 HEALTH CHECK LEVE
    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "healthy",
            "service": "pystore-api",
            "timestamp": datetime.datetime.utcnow().isoformat()
        }), 200

    # 🔹 UPLOADS - ENDPOINT DE MOCK (ou usar S3/Cloudinary)
    @app.route("/uploads/produtos/<filename>", methods=["GET"])
    def serve_product_image(filename):
        return jsonify({
            "error": "Uploads não disponíveis no Vercel",
            "message": "Use um serviço externo como S3 ou Cloudinary",
            "filename": filename
        }), 501

    # 🔹 ROTAS DA API
    try:
        from app.routes.user_routes import user_routes
        from app.routes.product_routes import product_routes
        from app.routes.admin_routes import admin_routes
        
        app.register_blueprint(user_routes, url_prefix="/api")
        app.register_blueprint(product_routes, url_prefix="/api")
        app.register_blueprint(admin_routes, url_prefix="/api")
        
        # Modificar rotas de upload nos blueprints
        print("✅ Rotas carregadas")
    except ImportError as e:
        print(f"⚠️  Blueprints não carregados: {e}")

    # 🔹 SWAGGER LEVE
    try:
        SWAGGER_URL = "/swagger"
        API_URL = "/swagger.json"
        
        swaggerui_blueprint = get_swaggerui_blueprint(
            SWAGGER_URL,
            API_URL,
            config={"app_name": "PyStore API (Vercel)"}
        )
        app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
    except:
        print("⚠️  Swagger não disponível")

    return app

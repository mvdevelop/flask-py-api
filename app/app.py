
# app/app.py - VERSÃO SIMPLIFICADA
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os
import datetime

def create_app(config_name='default'):
    """Factory function para criar a aplicação Flask"""
    
    print("=" * 60)
    print(f"🚀 Criando app Flask - Ambiente: {config_name}")
    print("=" * 60)
    
    app = Flask(__name__)
    
    # 🔧 CONFIGURAÇÕES
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
    
    # 🔐 JWT
    jwt_secret = os.environ.get("JWT_SECRET_KEY", "dev-secret-key")
    app.config["JWT_SECRET_KEY"] = jwt_secret
    JWTManager(app)
    print(f"🔐 JWT configurado")

    # 🔓 CORS
    CORS(app, resources={r"/*": {"origins": "*"}})

    # 🗄️ MONGODB - SIMPLIFICADO
    mongo_uri = os.environ.get("MONGO_URI")
    app.db = None
    
    if mongo_uri:
        try:
            from pymongo import MongoClient
            print(f"🔗 Conectando ao MongoDB...")
            
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            client.admin.command('ping')
            app.db = client[os.environ.get("MONGO_DB", "py_store")]
            
            print(f"✅ MongoDB Atlas conectado!")
        except Exception as e:
            print(f"⚠️  MongoDB não disponível: {e}")
            app.db = None
    else:
        print("⚠️  MONGO_URI não configurada")
        app.db = None

    # 🔹 ROTA INICIAL CORRIGIDA
    @app.route("/", methods=["GET"])
    def index():
        # CORREÇÃO: Use 'app.db is not None' em vez de 'app.db'
        db_status = "connected" if app.db is not None else "disconnected"
        
        return jsonify({
            "message": "PyStore API 🚀",
            "status": "online",
            "database": db_status,
            "environment": config_name,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })

    # 🔹 HEALTH CHECK CORRIGIDO
    @app.route("/health", methods=["GET"])
    def health_check():
        db_status = "connected" if app.db is not None else "disconnected"
        
        return jsonify({
            "status": "healthy" if app.db is not None else "degraded",
            "service": "pystore-api",
            "database": db_status,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })

    # 🔹 ROTAS DA API
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
                "message": "Products module not available"
            })

    print("=" * 60)
    print("✅ Aplicação Flask criada com sucesso!")
    print("=" * 60)
    
    return app

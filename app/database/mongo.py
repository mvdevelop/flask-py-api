
"""
Conexão com MongoDB compatível com Vercel e Docker
"""
import os
from pymongo import MongoClient
from flask import current_app

# Conexão global (para uso em modelos)
_db = None
_client = None

def init_db(app=None):
    """
    Inicializa a conexão com o MongoDB
    Pode receber um app Flask ou usar variáveis de ambiente
    """
    global _client, _db
    
    try:
        # Tenta pegar a URI do app Flask ou variável de ambiente
        mongo_uri = None
        
        if app and hasattr(app, 'config') and app.config.get('MONGO_URI'):
            mongo_uri = app.config['MONGO_URI']
        elif os.environ.get('MONGO_URI'):
            mongo_uri = os.environ.get('MONGO_URI')
        else:
            print("⚠️  MONGO_URI não configurada")
            return None
        
        # Nome do banco
        db_name = os.environ.get('MONGO_DB', 'py_store')
        
        # Conecta ao MongoDB
        _client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,
            retryWrites=True,
            w="majority",
            appname="PyStore-API"
        )
        
        # Testa a conexão
        _client.admin.command('ping')
        
        # Seleciona o banco
        _db = _client[db_name]
        
        print(f"✅ MongoDB conectado: {db_name}")
        
        # Se temos um app Flask, armazena a conexão nele
        if app:
            app.db = _db
            app.mongo_client = _client
        
        return _db
        
    except Exception as e:
        print(f"❌ Erro ao conectar ao MongoDB: {e}")
        
        # Tenta uma conexão de fallback local se estiver em desenvolvimento
        if os.environ.get('FLASK_ENV') == 'development':
            try:
                print("🔄 Tentando conexão local de fallback...")
                _client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
                _db = _client['py_store_dev']
                print("✅ Usando MongoDB local de fallback")
                return _db
            except:
                print("❌ Fallback também falhou")
        
        return None

def get_db():
    """
    Retorna a conexão com o banco
    Tenta inicializar se não estiver conectado
    """
    global _db
    
    if _db is None:
        # Tenta pegar do current_app (Vercel)
        try:
            if current_app and hasattr(current_app, 'db'):
                _db = current_app.db
                return _db
        except:
            pass
        
        # Tenta inicializar
        init_db()
    
    return _db

def close_db():
    """Fecha a conexão com o MongoDB"""
    global _client
    if _client:
        _client.close()
        print("📴 Conexão MongoDB fechada")

# Expor a conexão global
db = get_db()

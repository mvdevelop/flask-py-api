
"""
Inicialização do módulo app
"""
from .database.mongo import init_db

def init_app(app):
    """
    Inicializa extensões na aplicação Flask
    """
    # Inicializa MongoDB
    db = init_db(app)
    
    if db:
        # Cria índices após alguns segundos (para não bloquear startup)
        import threading
        import time
        
        def create_indexes_delayed():
            time.sleep(5)  # Espera 5 segundos
            try:
                from app.models.product_model import ProductModel
                ProductModel.ensure_indexes()
            except Exception as e:
                print(f"⚠️  Erro ao criar índices: {e}")
        
        # Executa em thread separada
        thread = threading.Thread(target=create_indexes_delayed, daemon=True)
        thread.start()
    
    return app

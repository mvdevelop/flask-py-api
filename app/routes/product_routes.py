
from flask import Blueprint, request, jsonify, current_app
from app.controllers.product_controller import ProductController
import time

product_routes = Blueprint("product_routes", __name__)

# 🔹 Middleware para verificar se estamos no Vercel
@product_routes.before_request
def check_vercel_environment():
    """Verifica se estamos rodando na Vercel e aplica limitações"""
    if request.method in ['POST', 'PUT', 'DELETE']:
        # Log para debug na Vercel
        current_app.logger.info(f"[VERCEL] {request.method} {request.path}")
    
    # Verifica timeout longo (Vercel tem limite de 10s)
    if hasattr(current_app, 'start_time'):
        elapsed = time.time() - current_app.start_time
        if elapsed > 8:  # Aviso em 8s (10s é o limite)
            return jsonify({
                "warning": "Request taking too long",
                "elapsed_seconds": round(elapsed, 2),
                "limit": "Vercel has 10 second timeout"
            }), 200

# 🔹 Health check específico para produtos
@product_routes.route("/produtos/health", methods=["GET"])
def products_health():
    """Health check otimizado para Vercel"""
    return jsonify({
        "status": "healthy",
        "service": "products-api",
        "environment": "Vercel" if 'VERCEL' in current_app.config else "Local",
        "timestamp": time.time()
    }), 200

# 🔹 Lista produtos (OTIMIZADO para Vercel)
@product_routes.route("/produtos", methods=["GET"])
def get_products():
    """
    Lista produtos com limitações para Vercel
    Query params:
    - limit: máximo de resultados (padrão: 20, máximo: 50)
    - page: página para paginação
    - simple: true/false - retorna apenas dados essenciais
    """
    # Otimizações específicas para Vercel
    limit = min(int(request.args.get('limit', 20)), 50)  # Máx 50 na Vercel
    page = int(request.args.get('page', 1))
    simple_mode = request.args.get('simple', 'false').lower() == 'true'
    
    # Adiciona parâmetros de otimização
    request.args = request.args.copy()
    request.args['vercel_limit'] = str(limit)
    request.args['vercel_simple'] = str(simple_mode)
    
    result = ProductController.get_products()
    
    # Se for JSON, adiciona metadados da Vercel
    if isinstance(result, tuple) and isinstance(result[0], dict):
        data, status = result
        if status == 200:
            data['_vercel'] = {
                "optimized": True,
                "max_limit": 50,
                "timeout_warning": "10 seconds",
                "note": "For large datasets, implement pagination"
            }
        return jsonify(data), status
    
    return result

# 🔹 Cria produto (ADAPTADO para Vercel - sem upload de arquivos)
@product_routes.route("/produtos", methods=["POST"])
def create_product():
    """
    Cria produto na Vercel
    IMPORTANTE: Na Vercel, não suporta upload de arquivos multipart/form-data
    Use JSON com URL da imagem:
    {
        "name": "Produto",
        "price": 100,
        "image_url": "https://cloudinary.com/image.jpg"
    }
    """
    # Verifica se é multipart/form-data (não funciona bem na Vercel)
    if 'multipart/form-data' in request.content_type:
        return jsonify({
            "error": "FormData upload not supported on Vercel",
            "solution": "Use JSON with image_url field",
            "example": {
                "name": "Product Name",
                "price": 99.90,
                "image_url": "https://your-cdn.com/image.jpg"
            }
        }), 415  # Unsupported Media Type
    
    # Para JSON, verifica se tem image_url
    if request.is_json:
        data = request.get_json()
        if not data.get('image_url') and 'image' not in data:
            return jsonify({
                "warning": "No image_url provided",
                "recommendation": "On Vercel, store only image URLs, not files",
                "services": ["Cloudinary", "AWS S3", "ImgBB", "Uploadcare"]
            }), 200
    
    # Adiciona flag de Vercel para o controller
    request.is_vercel = True
    
    return ProductController.create_product()

# 🔹 Upload alternativo para Vercel (apenas URL)
@product_routes.route("/produtos/upload-url", methods=["POST"])
def upload_product_url():
    """
    Endpoint específico para Vercel - aceita apenas URL de imagem
    """
    if not request.is_json:
        return jsonify({
            "error": "Content-Type must be application/json",
            "message": "This endpoint accepts only JSON with image_url"
        }), 415
    
    data = request.get_json()
    
    if not data.get('image_url'):
        return jsonify({
            "error": "Missing image_url",
            "example": {
                "image_url": "https://res.cloudinary.com/.../image.jpg",
                "product_id": "optional_product_id"
            }
        }), 400
    
    # Valida URL
    import re
    url_pattern = re.compile(r'^https?://')
    if not url_pattern.match(data['image_url']):
        return jsonify({
            "error": "Invalid URL format",
            "message": "URL must start with http:// or https://"
        }), 400
    
    return jsonify({
        "success": True,
        "message": "Image URL received",
        "image_url": data['image_url'],
        "storage": "URL stored in database (no file upload)",
        "service": "Vercel Serverless",
        "note": "The actual image is hosted externally"
    }), 200

# 🔹 Get produto por ID (OTIMIZADO)
@product_routes.route("/produtos/<string:product_id>", methods=["GET"])
def get_product(product_id):
    """
    Obtém um produto específico
    Otimizado para cache na Vercel
    """
    # Adiciona headers para cache da Vercel
    response = ProductController.get_product(product_id)
    
    # Se for uma resposta JSON válida
    if isinstance(response, tuple) and len(response) == 2:
        data, status = response
        if status == 200:
            # Adiciona headers de cache
            response_headers = {
                'Cache-Control': 'public, max-age=300',  # 5 minutos
                'CDN-Cache-Control': 'public, max-age=600',
                'Vercel-CDN-Cache-Control': 'max-age=3600'
            }
            return jsonify(data), status, response_headers
    
    return response

# 🔹 Delete produto
@product_routes.route("/produtos/<string:product_id>", methods=["DELETE"])
def delete_product(product_id):
    """
    Deleta um produto
    Na Vercel, não deleta arquivos físicos - apenas referências
    """
    # Adiciona contexto Vercel
    request.is_vercel = True
    return ProductController.delete_product(product_id)

# 🔹 Batch operations (otimizado para Vercel)
@product_routes.route("/produtos/batch", methods=["GET"])
def get_products_batch():
    """
    Operações em lote otimizadas para Vercel
    Retorna apenas dados essenciais
    """
    limit = min(int(request.args.get('limit', 10)), 30)
    fields = request.args.get('fields', 'name,price,image_url').split(',')
    
    # Garante que só campos essenciais são pedidos
    allowed_fields = ['name', 'price', 'image_url', 'category', 'id']
    fields = [f for f in fields if f in allowed_fields][:3]
    
    request.args = request.args.copy()
    request.args['batch_mode'] = 'true'
    request.args['fields'] = ','.join(fields)
    
    return ProductController.get_products()

# 🔹 Estatísticas leves (para Vercel)
@product_routes.route("/produtos/stats", methods=["GET"])
def get_stats():
    """
    Estatísticas leves otimizadas para Vercel
    """
    try:
        if hasattr(current_app, 'db') and current_app.db:
            # Consultas rápidas apenas
            total = current_app.db.products.count_documents({})
            
            # Amostra pequena para categorias
            pipeline = [
                {"$group": {"_id": "$category", "count": {"$sum": 1}}},
                {"$limit": 10},
                {"$sort": {"count": -1}}
            ]
            
            categories = list(current_app.db.products.aggregate(pipeline))
            
            return jsonify({
                "stats": {
                    "total_products": total,
                    "categories_sample": categories,
                    "optimized_for": "Vercel Serverless",
                    "note": "Limited aggregation for performance"
                }
            }), 200
        else:
            return jsonify({
                "error": "Database not available",
                "stats": {"total_products": 0}
            }), 503
    except Exception as e:
        return jsonify({
            "error": "Could not fetch stats",
            "message": str(e)[:100]  # Limita tamanho do erro
        }), 500

# 🔹 Error handler específico para Vercel
@product_routes.errorhandler(413)
def too_large(error):
    """Request too large para Vercel"""
    return jsonify({
        "error": "Request too large",
        "message": "Vercel has 1MB request limit",
        "limit": "1MB",
        "recommendation": "Use image URLs instead of file uploads"
    }), 413

@product_routes.errorhandler(500)
def server_error(error):
    """Erro interno - mensagem amigável para Vercel"""
    return jsonify({
        "error": "Internal server error",
        "environment": "Vercel Serverless",
        "support": "Check logs at vercel.com/dashboard",
        "note": "Timeout limit is 10 seconds"
    }), 500


from flask import request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import uuid
from app.models.product_model import ProductModel
import datetime

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

class ProductController:
    
    @staticmethod
    def _is_vercel_environment():
        """Detecta se está rodando na Vercel"""
        return 'VERCEL' in os.environ or 'ON_VERCEL' in os.environ or hasattr(request, 'is_vercel')
    
    @staticmethod
    def _get_upload_folder():
        """Retorna o folder de upload baseado no ambiente"""
        if current_app.config.get("UPLOAD_FOLDER"):
            return current_app.config["UPLOAD_FOLDER"]
        
        # Fallback para diferentes ambientes
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        if ProductController._is_vercel_environment():
            # Vercel não permite escrita persistente
            return os.path.join(base_dir, "..", "..", "tmp_uploads")
        else:
            # Docker/Local
            return os.path.join(base_dir, "..", "..", "uploads", "produtos")
    
    @staticmethod
    def _generate_image_url(filename, environment="unknown"):
        """Gera URL da imagem baseado no ambiente"""
        
        # Se já é uma URL completa, retorna como está
        if filename.startswith(('http://', 'https://')):
            return filename
            
        if environment == "vercel":
            # Na Vercel, não podemos servir arquivos estáticos facilmente
            # Use um serviço externo ou retorne um placeholder
            return f"https://via.placeholder.com/400x300?text={filename[:15]}"
        
        elif environment == "docker":
            # Em Docker, use a variável de ambiente ou padrão
            base_url = os.environ.get('API_BASE_URL', 'http://localhost:5000')
            return f"{base_url}/uploads/produtos/{filename}"
        
        elif environment == "render":
            # Se estiver no Render
            return f"https://flask-py-api.onrender.com/uploads/produtos/{filename}"
        
        else:
            # Fallback genérico
            return f"/uploads/produtos/{filename}"
    
    @staticmethod
    def create_product():
        """Cria produto compatível com Vercel e Docker"""
        
        # Detecta ambiente
        is_vercel = ProductController._is_vercel_environment()
        
        # Se for Vercel e tiver multipart, rejeita
        if is_vercel and 'multipart/form-data' in request.content_type:
            return jsonify({
                "error": "File upload not supported on Vercel",
                "solution": "Use JSON with 'image_url' field instead of file upload",
                "example": {
                    "nome": "Produto Exemplo",
                    "descricao": "Descrição",
                    "image_url": "https://cdn.exemplo.com/imagem.jpg"
                }
            }), 415
        
        nome = None
        descricao = None
        image_url = None
        uploaded_filename = None
        
        # 🔹 MODO 1: JSON (Vercel ou API pura)
        if request.is_json:
            data = request.get_json()
            nome = data.get("nome")
            descricao = data.get("descricao")
            image_url = data.get("image_url") or data.get("img")
            
            if not nome or not descricao:
                return jsonify({"error": "nome e descricao são obrigatórios"}), 400
        
        # 🔹 MODO 2: FormData (Docker/Local)
        else:
            nome = request.form.get("nome")
            descricao = request.form.get("descricao")
            file = request.files.get("img")
            
            if not nome or not descricao:
                return jsonify({"error": "nome e descricao são obrigatórios"}), 400
            
            # Upload de arquivo (apenas Docker/Local)
            if file and file.filename:
                if not allowed_file(file.filename):
                    return jsonify({"error": "Formato de imagem inválido"}), 400
                
                # 🔹 Gera nome único
                ext = os.path.splitext(file.filename)[1]
                unique_filename = f"{uuid.uuid4()}{ext}"
                filename = secure_filename(unique_filename)
                
                # Salva arquivo (não na Vercel)
                if not is_vercel:
                    upload_folder = ProductController._get_upload_folder()
                    os.makedirs(upload_folder, exist_ok=True)
                    filepath = os.path.join(upload_folder, filename)
                    file.save(filepath)
                    uploaded_filename = filename
                    
                    # Gera URL baseada no ambiente
                    environment = "docker" if 'DOCKER' in os.environ else "local"
                    image_url = ProductController._generate_image_url(filename, environment)
                else:
                    # Na Vercel, não salva arquivo
                    image_url = ProductController._generate_image_url(file.filename, "vercel")
            
            elif request.form.get("image_url"):
                # Se forneceu URL diretamente no form
                image_url = request.form.get("image_url")
        
        # Se não tem imagem/URL, usa placeholder
        if not image_url:
            image_url = f"https://via.placeholder.com/400x300?text={nome[:20]}"
        
        # 🔹 Cria produto no banco
        try:
            product_data = {
                "nome": nome,
                "descricao": descricao,
                "img": image_url,
                "original_filename": uploaded_filename,
                "created_at": datetime.datetime.utcnow(),
                "environment": "vercel" if is_vercel else "docker/local",
                "has_file": bool(uploaded_filename)
            }
            
            product = ProductModel.create(product_data)
            
            # Adiciona metadados de ambiente na resposta
            if isinstance(product, dict):
                product["_environment"] = {
                    "deployed_on": "Vercel" if is_vercel else "Docker/Local",
                    "file_upload": "disabled" if is_vercel else "enabled",
                    "image_storage": "external_url" if is_vercel else "local+url"
                }
            
            return jsonify(product), 201
            
        except Exception as e:
            return jsonify({
                "error": "Erro ao criar produto",
                "details": str(e),
                "environment": "Vercel" if is_vercel else "Docker"
            }), 500
    
    @staticmethod
    def get_products():
        """Obtém todos os produtos"""
        try:
            products = ProductModel.get_all()
            
            # Adiciona informações de ambiente
            response = {
                "products": products,
                "metadata": {
                    "count": len(products),
                    "environment": "Vercel" if ProductController._is_vercel_environment() else "Docker",
                    "timestamp": datetime.datetime.utcnow().isoformat()
                }
            }
            
            return jsonify(response), 200
        except Exception as e:
            return jsonify({
                "error": "Erro ao buscar produtos",
                "details": str(e)
            }), 500
    
    @staticmethod
    def get_product(product_id):
        """Obtém um produto específico"""
        try:
            product = ProductModel.get_by_id(product_id)
            
            if not product:
                return jsonify({"error": "Produto não encontrado"}), 404
            
            return jsonify(product), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @staticmethod
    def delete_product(product_id):
        """Deleta um produto"""
        try:
            # Primeiro obtém o produto para ver se tem arquivo
            product = ProductModel.get_by_id(product_id)
            
            if not product:
                return jsonify({"error": "Produto não encontrado"}), 404
            
            # Se tiver arquivo local e não estiver na Vercel, deleta
            if product.get('original_filename') and not ProductController._is_vercel_environment():
                try:
                    upload_folder = ProductController._get_upload_folder()
                    filepath = os.path.join(upload_folder, product['original_filename'])
                    if os.path.exists(filepath):
                        os.remove(filepath)
                except:
                    pass  # Ignora erro ao deletar arquivo
            
            # Deleta do banco
            result = ProductModel.delete(product_id)
            
            return jsonify({
                "success": True,
                "message": "Produto deletado",
                "product_id": product_id,
                "file_deleted": product.get('original_filename') is not None
            }), 200
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        
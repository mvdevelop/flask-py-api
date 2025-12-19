
from app.database.mongo import db
from bson.objectid import ObjectId
from flask import current_app
import datetime
import os

class ProductModel:
    
    @staticmethod
    def _get_collection():
        """
        Retorna a coleção de produtos.
        Em caso de falha, tenta recuperar do current_app (Vercel).
        """
        try:
            # Tenta usar o db do módulo database
            if db and hasattr(db, 'produtos'):
                return db.produtos
        except:
            pass
        
        # Fallback: tenta pegar do current_app (útil para Vercel)
        try:
            if current_app and hasattr(current_app, 'db'):
                return current_app.db.produtos
        except:
            pass
        
        # Último fallback: tenta criar conexão direta (não recomendado)
        raise Exception("Database connection not available")
    
    @staticmethod
    def _is_vercel_environment():
        """Detecta se está rodando na Vercel"""
        return 'VERCEL' in os.environ or hasattr(current_app, 'is_vercel') if current_app else False
    
    @staticmethod
    def create(data):
        """
        Cria um novo produto com metadados adicionais
        Compatível com Vercel e Docker
        """
        # Coleta básica de dados
        product = {
            "nome": data.get("nome", "").strip(),
            "descricao": data.get("descricao", "").strip(),
            "img": data.get("img") or data.get("image_url", ""),
            "original_filename": data.get("original_filename"),
            "environment": "vercel" if ProductModel._is_vercel_environment() else "docker/local",
            "has_file": data.get("has_file", False),
            "created_at": data.get("created_at", datetime.datetime.utcnow()),
            "updated_at": data.get("updated_at", datetime.datetime.utcnow()),
            "active": True
        }
        
        # Adiciona preço se existir
        if "preco" in data or "price" in data:
            product["preco"] = float(data.get("preco") or data.get("price") or 0)
        
        # Adiciona categoria se existir
        if "categoria" in data or "category" in data:
            product["categoria"] = data.get("categoria") or data.get("category", "uncategorized")
        
        # Tags/etiquetas
        if "tags" in data:
            product["tags"] = data.get("tags", [])
        
        # Se for Vercel, marca que a imagem é externa
        if ProductModel._is_vercel_environment():
            product["image_storage"] = "external_url"
            product["vercel_deployed"] = True
        
        # Insere no banco
        try:
            collection = ProductModel._get_collection()
            result = collection.insert_one(product)
            product["_id"] = str(result.inserted_id)
            
            # Log
            print(f"✅ Produto criado: {product['nome']} (ID: {product['_id'][:8]}...)")
            
            return product
            
        except Exception as e:
            print(f"❌ Erro ao criar produto: {e}")
            raise Exception(f"Database error: {str(e)}")
    
    @staticmethod
    def get_all(filters=None, limit=100, skip=0):
        """
        Retorna todos os produtos com opções de filtro
        Otimizado para Vercel (limite padrão de 100)
        """
        try:
            collection = ProductModel._get_collection()
            
            # Filtros padrão
            query = {"active": True}
            
            # Aplica filtros personalizados
            if filters:
                if "categoria" in filters:
                    query["categoria"] = filters["categoria"]
                if "min_preco" in filters:
                    query["preco"] = {"$gte": float(filters["min_preco"])}
                if "max_preco" in filters:
                    if "preco" in query:
                        query["preco"]["$lte"] = float(filters["max_preco"])
                    else:
                        query["preco"] = {"$lte": float(filters["max_preco"])}
                if "tags" in filters:
                    query["tags"] = {"$in": filters["tags"]}
            
            # Limita resultados (especialmente importante para Vercel)
            limit = min(limit, 200)  # Máximo absoluto
            
            # Executa query
            cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
            
            produtos = []
            for p in cursor:
                # Converte ObjectId para string
                p["_id"] = str(p["_id"])
                
                # Garante que img existe e é uma URL válida
                if not p.get("img") or not p["img"].startswith(("http://", "https://", "/")):
                    p["img"] = f"https://via.placeholder.com/400x300?text={p.get('nome', 'Produto')[:15]}"
                
                # Adiciona campo simplificado para frontend
                p["thumbnail"] = p.get("img")
                
                produtos.append(p)
            
            # Conta total (para paginação)
            total = collection.count_documents(query) if skip == 0 else None
            
            return {
                "products": produtos,
                "pagination": {
                    "total": total,
                    "limit": limit,
                    "skip": skip,
                    "has_more": len(produtos) == limit
                },
                "environment": "vercel" if ProductModel._is_vercel_environment() else "docker"
            }
            
        except Exception as e:
            print(f"❌ Erro ao buscar produtos: {e}")
            return {
                "products": [],
                "pagination": {"total": 0, "limit": limit, "skip": skip, "has_more": False},
                "error": str(e)[:100]
            }
    
    @staticmethod
    def get_by_id(product_id, raise_exception=False):
        """
        Retorna um produto pelo ID
        """
        try:
            # Valida ID
            if not product_id or not ObjectId.is_valid(product_id):
                if raise_exception:
                    raise ValueError("Invalid product ID format")
                return None
            
            collection = ProductModel._get_collection()
            product = collection.find_one({"_id": ObjectId(product_id), "active": True})
            
            if not product:
                if raise_exception:
                    raise Exception("Product not found")
                return None
            
            # Converte ObjectId para string
            product["_id"] = str(product["_id"])
            
            # Garante URL da imagem
            if not product.get("img") or not product["img"].startswith(("http://", "https://", "/")):
                product["img"] = f"https://via.placeholder.com/600x400?text={product.get('nome', 'Produto')}"
            
            # Adiciona metadados
            product["retrieved_at"] = datetime.datetime.utcnow().isoformat()
            
            return product
            
        except Exception as e:
            print(f"❌ Erro ao buscar produto {product_id}: {e}")
            if raise_exception:
                raise
            return None
    
    @staticmethod
    def update(product_id, update_data):
        """
        Atualiza um produto
        """
        try:
            if not ObjectId.is_valid(product_id):
                raise ValueError("Invalid product ID")
            
            # Remove campos que não devem ser atualizados
            update_data.pop("_id", None)
            update_data.pop("created_at", None)
            
            # Adiciona updated_at
            update_data["updated_at"] = datetime.datetime.utcnow()
            
            collection = ProductModel._get_collection()
            result = collection.update_one(
                {"_id": ObjectId(product_id)},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                return {"success": False, "message": "Product not found"}
            
            return {
                "success": True,
                "matched_count": result.matched_count,
                "modified_count": result.modified_count,
                "product_id": product_id
            }
            
        except Exception as e:
            print(f"❌ Erro ao atualizar produto {product_id}: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def delete(product_id, soft_delete=True):
        """
        Deleta um produto
        soft_delete=True: marca como inativo (padrão)
        soft_delete=False: remove completamente
        """
        try:
            if not ObjectId.is_valid(product_id):
                return {"deleted": False, "error": "Invalid product ID"}
            
            collection = ProductModel._get_collection()
            
            if soft_delete:
                # Soft delete: marca como inativo
                result = collection.update_one(
                    {"_id": ObjectId(product_id)},
                    {"$set": {"active": False, "deleted_at": datetime.datetime.utcnow()}}
                )
                message = "Product marked as deleted"
            else:
                # Hard delete: remove completamente
                result = collection.delete_one({"_id": ObjectId(product_id)})
                message = "Product permanently deleted"
            
            deleted = result.modified_count > 0 if soft_delete else result.deleted_count > 0
            
            return {
                "deleted": deleted,
                "message": message if deleted else "Product not found",
                "product_id": product_id,
                "soft_delete": soft_delete
            }
            
        except Exception as e:
            print(f"❌ Erro ao deletar produto {product_id}: {e}")
            return {"deleted": False, "error": str(e)}
    
    @staticmethod
    def search(query, limit=50):
        """
        Busca produtos por texto
        """
        try:
            collection = ProductModel._get_collection()
            
            # Cria índice de texto se não existir
            indexes = collection.index_information()
            if "nome_text_descricao_text" not in indexes:
                collection.create_index([("nome", "text"), ("descricao", "text")])
            
            # Busca por texto
            cursor = collection.find(
                {"$text": {"$search": query}, "active": True},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(min(limit, 100))
            
            produtos = []
            for p in cursor:
                p["_id"] = str(p["_id"])
                produtos.append(p)
            
            return {
                "results": produtos,
                "query": query,
                "count": len(produtos)
            }
            
        except Exception as e:
            print(f"❌ Erro na busca: {e}")
            return {"results": [], "query": query, "error": str(e)[:100]}
    
    @staticmethod
    def get_categories():
        """
        Retorna lista de categorias únicas
        """
        try:
            collection = ProductModel._get_collection()
            
            pipeline = [
                {"$match": {"active": True, "categoria": {"$exists": True, "$ne": ""}}},
                {"$group": {"_id": "$categoria", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 20}
            ]
            
            categories = list(collection.aggregate(pipeline))
            
            return [
                {"name": cat["_id"], "count": cat["count"]}
                for cat in categories
            ]
            
        except Exception as e:
            print(f"❌ Erro ao buscar categorias: {e}")
            return []
    
    @staticmethod
    def get_stats():
        """
        Retorna estatísticas dos produtos
        Otimizado para Vercel (consultas rápidas)
        """
        try:
            collection = ProductModel._get_collection()
            
            # Contagem total (apenas ativos)
            total = collection.count_documents({"active": True})
            
            # Contagem por ambiente
            vercel_count = collection.count_documents({"environment": "vercel", "active": True})
            docker_count = collection.count_documents({"environment": "docker/local", "active": True})
            
            # Último produto criado
            last_product = collection.find_one(
                {"active": True},
                sort=[("created_at", -1)]
            )
            
            if last_product:
                last_product["_id"] = str(last_product["_id"])
            
            return {
                "stats": {
                    "total_products": total,
                    "vercel_products": vercel_count,
                    "docker_products": docker_count,
                    "with_images": collection.count_documents({"img": {"$exists": True, "$ne": ""}, "active": True}),
                    "last_added": last_product.get("created_at").isoformat() if last_product and last_product.get("created_at") else None
                },
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Erro ao buscar estatísticas: {e}")
            return {
                "stats": {"error": str(e)[:100]},
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
    
    @staticmethod
    def ensure_indexes():
        """
        Cria índices para melhor performance
        Deve ser chamado na inicialização da app
        """
        try:
            collection = ProductModel._get_collection()
            
            # Índice para busca por created_at (listagens)
            collection.create_index([("created_at", -1)])
            
            # Índice para categoria + created_at
            collection.create_index([("categoria", 1), ("created_at", -1)])
            
            # Índice para active flag
            collection.create_index([("active", 1)])
            
            # Índice para ambiente (debug)
            collection.create_index([("environment", 1)])
            
            print("✅ Índices do MongoDB criados/verificados")
            
        except Exception as e:
            print(f"⚠️  Não foi possível criar índices: {e}")
            
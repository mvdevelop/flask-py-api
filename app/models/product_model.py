"""
ProductModel — Product data access layer.
Security: Uses get_db() to avoid premature connection at import time.
"""
from app.database.mongo import get_db
from bson.objectid import ObjectId
import datetime
import logging

logger = logging.getLogger(__name__)


class ProductModel:

    @staticmethod
    def _collection():
        db = get_db()
        if not db:
            raise Exception("MongoDB não inicializado")
        if not hasattr(db, "produtos"):
            raise Exception("Coleção produtos não disponível")
        return db.produtos

    @staticmethod
    def create(data: dict):
        product = {
            "nome": data["nome"].strip(),
            "descricao": data["descricao"].strip(),
            "img": data.get("img"),
            "preco": float(data["preco"]) if "preco" in data and data["preco"] else None,
            "categoria": data.get("categoria"),
            "tags": data.get("tags", []),
            "active": True,
            "created_at": datetime.datetime.utcnow(),
            "updated_at": datetime.datetime.utcnow(),
        }

        collection = ProductModel._collection()
        result = collection.insert_one(product)

        product["_id"] = str(result.inserted_id)
        return product

    @staticmethod
    def get_all(limit: int = 100, skip: int = 0):
        collection = ProductModel._collection()

        cursor = (
            collection
            .find({"active": True})
            .sort("created_at", -1)
            .skip(skip)
            .limit(min(limit, 100))
        )

        products = []
        for p in cursor:
            p["_id"] = str(p["_id"])
            products.append(p)

        total = collection.count_documents({"active": True})

        return {
            "count": total,
            "products": products,
        }

    @staticmethod
    def get_by_id(product_id: str):
        if not ObjectId.is_valid(product_id):
            return None

        collection = ProductModel._collection()
        product = collection.find_one({
            "_id": ObjectId(product_id),
            "active": True,
        })

        if not product:
            return None

        product["_id"] = str(product["_id"])
        return product

    @staticmethod
    def update(product_id: str, data: dict):
        if not ObjectId.is_valid(product_id):
            return False

        # Strip campos protegidos contra mass assignment
        data.pop("_id", None)
        data.pop("created_at", None)
        data.pop("active", None)
        data.pop("password", None)  # defesa extra

        data["updated_at"] = datetime.datetime.utcnow()

        collection = ProductModel._collection()
        result = collection.update_one(
            {"_id": ObjectId(product_id), "active": True},
            {"$set": data},
        )

        return result.matched_count > 0

    @staticmethod
    def delete(product_id: str):
        if not ObjectId.is_valid(product_id):
            return False

        collection = ProductModel._collection()
        result = collection.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": {"active": False, "updated_at": datetime.datetime.utcnow()}}
        )

        return result.modified_count > 0

    @staticmethod
    def search(text: str, limit: int = 50):
        collection = ProductModel._collection()

        cursor = collection.find(
            {"$text": {"$search": text}, "active": True}
        ).limit(min(limit, 50))

        results = []
        for p in cursor:
            p["_id"] = str(p["_id"])
            results.append(p)

        return results

    @staticmethod
    def ensure_indexes():
        """Cria índices necessários — chamado via init_app."""
        collection = ProductModel._collection()
        collection.create_index([("nome", "text"), ("descricao", "text")])
        collection.create_index([("created_at", -1)])
        collection.create_index([("categoria", 1)])
        collection.create_index([("active", 1)])
        logger.info("MongoDB indexes ready")

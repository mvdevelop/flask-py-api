
from app.database.mongo import db
from bson.objectid import ObjectId
import datetime

class ProductModel:

    @staticmethod
    def _collection():
        if not db or not hasattr(db, "produtos"):
            raise Exception("MongoDB not initialized")
        return db.produtos

    # ==============================
    # CREATE
    # ==============================
    @staticmethod
    def create(data: dict):
        product = {
            "nome": data["nome"].strip(),
            "descricao": data["descricao"].strip(),
            "img": data.get("img"),
            "preco": float(data["preco"]) if "preco" in data else None,
            "categoria": data.get("categoria"),
            "tags": data.get("tags", []),
            "active": True,
            "created_at": datetime.datetime.utcnow(),
            "updated_at": datetime.datetime.utcnow()
        }

        collection = ProductModel._collection()
        result = collection.insert_one(product)

        product["_id"] = str(result.inserted_id)
        return product

    # ==============================
    # READ
    # ==============================
    @staticmethod
    def get_all(limit=100, skip=0):
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
            "products": products
        }

    @staticmethod
    def get_by_id(product_id):
        if not ObjectId.is_valid(product_id):
            return None

        collection = ProductModel._collection()
        product = collection.find_one({
            "_id": ObjectId(product_id),
            "active": True
        })

        if not product:
            return None

        product["_id"] = str(product["_id"])
        return product

    # ==============================
    # UPDATE
    # ==============================
    @staticmethod
    def update(product_id, data):
        if not ObjectId.is_valid(product_id):
            return False

        data.pop("_id", None)
        data.pop("created_at", None)

        data["updated_at"] = datetime.datetime.utcnow()

        collection = ProductModel._collection()
        result = collection.update_one(
            {"_id": ObjectId(product_id), "active": True},
            {"$set": data}
        )

        return result.matched_count > 0

    # ==============================
    # DELETE (soft)
    # ==============================
    @staticmethod
    def delete(product_id):
        if not ObjectId.is_valid(product_id):
            return False

        collection = ProductModel._collection()
        result = collection.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": {"active": False, "updated_at": datetime.datetime.utcnow()}}
        )

        return result.modified_count > 0

    # ==============================
    # SEARCH
    # ==============================
    @staticmethod
    def search(text, limit=50):
        collection = ProductModel._collection()

        cursor = collection.find(
            {"$text": {"$search": text}, "active": True}
        ).limit(min(limit, 50))

        results = []
        for p in cursor:
            p["_id"] = str(p["_id"])
            results.append(p)

        return results

    # ==============================
    # INDEXES
    # ==============================
    @staticmethod
    def ensure_indexes():
        collection = ProductModel._collection()

        collection.create_index([("nome", "text"), ("descricao", "text")])
        collection.create_index([("created_at", -1)])
        collection.create_index([("categoria", 1)])
        collection.create_index([("active", 1)])

        print("✅ MongoDB indexes ready")

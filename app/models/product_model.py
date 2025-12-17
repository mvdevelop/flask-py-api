
from app.database.mongo import db
from bson.objectid import ObjectId

class ProductModel:

    @staticmethod
    def create(data):
        product = {
            "nome": data.get("nome"),
            "descricao": data.get("descricao"),
            "img": data.get("img")  # 👈 URL da imagem
        }

        result = db.produtos.insert_one(product)
        product["_id"] = str(result.inserted_id)

        return product

    @staticmethod
    def get_all():
        produtos = []

        for p in db.produtos.find():
            produtos.append({
                "_id": str(p["_id"]),
                "nome": p.get("nome"),
                "descricao": p.get("descricao"),
                "img": p.get("img")  # 👈 URL pronta para render
            })

        return produtos

    @staticmethod
    def get_by_id(product_id):
        product = db.produtos.find_one({"_id": ObjectId(product_id)})

        if not product:
            return None

        product["_id"] = str(product["_id"])
        return product

    @staticmethod
    def delete(product_id):
        result = db.produtos.delete_one({"_id": ObjectId(product_id)})
        return result.deleted_count > 0


from app.database.mongo import db
from bson.objectid import ObjectId

class ProductModel:

    @staticmethod
    def create(data):
        product = {
            "nome": data["nome"],
            "descricao": data["descricao"],
            "img": data["img"]
        }

        result = db.produtos.insert_one(product)
        product["_id"] = str(result.inserted_id)

        return product

    @staticmethod
    def get_all():
        produtos = []

        for p in db.produtos.find():
            p["_id"] = str(p["_id"])
            produtos.append(p)

        return produtos

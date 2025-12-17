
from app.database.mongo import db
from bson.objectid import ObjectId
import bcrypt

class AdminModel:

    @staticmethod
    def create_admin(data):
        hashed = bcrypt.hashpw(
            data["password"].encode("utf-8"),
            bcrypt.gensalt()
        )

        admin = {
            "email": data["email"],
            "password": hashed,
            "role": "admin"
        }

        result = db.admins.insert_one(admin)
        admin["_id"] = str(result.inserted_id)
        del admin["password"]

        return admin

    @staticmethod
    def find_by_email(email):
        return db.admins.find_one({"email": email})

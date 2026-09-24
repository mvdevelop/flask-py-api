"""
AdminModel — Admin data access layer.
Security: Passwords hashed com bcrypt (CWE-916: Use of Password Hash With Insufficient Effort).
"""
from app.database.mongo import get_db
from bson.objectid import ObjectId
import bcrypt
import logging

logger = logging.getLogger(__name__)


class AdminModel:

    @staticmethod
    def create_admin(data):
        """Cria admin — senha hashada com bcrypt (13 salt rounds)."""
        # bcrypt.gensalt(rounds=13) — NIST SP 800-63B recomenda mínimo 10
        hashed = bcrypt.hashpw(
            data["password"].encode("utf-8"),
            bcrypt.gensalt(rounds=13),
        )

        db = get_db()
        admin = {
            "email": data["email"].lower().strip(),  # normaliza email
            "password": hashed,
            "role": "admin",
            "created_at": None,  # preenche no controller ou omitir
        }

        result = db.admins.insert_one(admin)
        admin["_id"] = str(result.inserted_id)
        del admin["password"]  # NUNCA retornar hash

        return admin

    @staticmethod
    def find_by_email(email):
        """Busca admin por email — sem expor password."""
        db = get_db()
        # Normaliza email para evitar duplicatas de capitalização
        normalized = email.lower().strip()
        return db.admins.find_one({"email": normalized})

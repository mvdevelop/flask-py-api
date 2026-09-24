"""
AdminController — autenticação e autorização.
Security Champion Note:
- bcrypt para password hashing (CWE-916)
- Rate limiting no login (CWE-307)
- Log de auditoria sem PII (CWE-532)
- Mensagens genéricas (CWE-204)
"""
from flask import request, jsonify
from flask_jwt_extended import create_access_token
from datetime import timedelta
import bcrypt
from app.models.admin_model import AdminModel
from app.schemas import AdminLoginSchema
from app.middlewares.rate_limit import rate_limit, clear_rate_limit
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)

# Configurações de rate limit
MAX_LOGIN_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 300  # 5 minutos


class AdminController:

    @staticmethod
    @rate_limit(limit=MAX_LOGIN_ATTEMPTS, window=LOGIN_WINDOW_SECONDS, scope="login")
    def login():
        """Login admin — validado + rate limited (CWE-307, CWE-20)."""
        client_ip = request.remote_addr or "unknown"

        data = request.get_json()
        if not data:
            return jsonify({"error": "Dados JSON obrigatórios"}), 400

        # Valida input com Pydantic (CWE-20)
        try:
            schema = AdminLoginSchema(**data)
        except ValidationError as e:
            return jsonify({"error": "Dados inválidos", "details": e.errors()}), 400

        admin = AdminModel.find_by_email(schema.email)

        if not admin:
            # Mensagem genérica — não revela se email existe (CWE-204)
            logger.info(f"Login falhou | ip={client_ip[:8]}... | motivo=usuario_nao_encontrado")
            return jsonify({"error": "Credenciais inválidas"}), 401

        # Verifica senha com bcrypt (constant-time) (CWE-916)
        try:
            password_valid = bcrypt.checkpw(
                schema.password.encode("utf-8"),
                admin["password"],
            )
        except (ValueError, TypeError):
            logger.info(f"Login falhou | ip={client_ip[:8]}... | motivo=hash_invalido")
            return jsonify({"error": "Credenciais inválidas"}), 401

        if not password_valid:
            logger.info(f"Login falhou | ip={client_ip[:8]}... | motivo=senha_incorreta")
            return jsonify({"error": "Credenciais inválidas"}), 401

        # Sucesso — limpa rate limit deste IP
        clear_rate_limit(client_ip, scope="login")

        # Cria token JWT com claims mínimas, expiração curta
        token = create_access_token(
            identity=str(admin["_id"]),
            additional_claims={"role": "admin"},
            expires_delta=timedelta(hours=1),
        )

        # Log de auditoria — sem PII (CWE-532)
        # Hash truncado do admin_id para correlação sem exposição
        logger.info(
            f"Login admin OK | admin_id={admin['_id'][:8]}... | ip={client_ip[:8]}..."
        )

        return jsonify({
            "token": token,
            "expires_in": 3600,  # 1 hora
            "token_type": "Bearer",
            "admin": {
                "id": str(admin["_id"]),
                "email": admin["email"],
            },
        }), 200

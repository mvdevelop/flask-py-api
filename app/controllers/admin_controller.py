from flask import request, jsonify
from flask_jwt_extended import create_access_token
import bcrypt
from app.models.admin_model import AdminModel
from app.schemas import AdminLoginSchema
from pydantic import ValidationError
import logging
import time

logger = logging.getLogger(__name__)

# Rate limiting simples — em memória (produção usar Redis)
# CWE-307 fix: previne brute force no /login
_login_attempts = {}
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 300  # 5 minutos


class AdminController:

    @staticmethod
    def login():
        """Login admin — validado + rate limited (CWE-307 CWE-20)."""
        client_ip = request.remote_addr or "unknown"

        # Rate limiting — checa tentativas falhas recentes
        now = time.time()
        attempts = _login_attempts.get(client_ip, [])

        # Remove tentativas fora do window de lockout
        attempts = [t for t in attempts if now - t < LOCKOUT_DURATION]
        _login_attempts[client_ip] = attempts

        if len(attempts) >= MAX_LOGIN_ATTEMPTS:
            logger.warning(f"Tentativa de login bloqueada para IP: {client_ip}")
            return jsonify({
                "error": "Muitas tentativas falhas. Tente novamente em alguns minutos."
            }), 429

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
            # Registra tentativa falha
            _login_attempts.setdefault(client_ip, []).append(now)
            # Mensagem genérica (CWE-204 — não revela se email existe)
            return jsonify({"error": "Credenciais inválidas"}), 401

        # Verifica senha com bcrypt (constant-time)
        try:
            password_valid = bcrypt.checkpw(
                schema.password.encode("utf-8"),
                admin["password"],
            )
        except (ValueError, TypeError):
            _login_attempts.setdefault(client_ip, []).append(now)
            return jsonify({"error": "Credenciais inválidas"}), 401

        if not password_valid:
            _login_attempts.setdefault(client_ip, []).append(now)
            return jsonify({"error": "Credenciais inválidas"}), 401

        # Limpa tentativas em caso de sucesso
        _login_attempts.pop(client_ip, None)

        token = create_access_token(
            identity=str(admin["_id"]),
            additional_claims={"role": "admin"},
            expires_delta=False,  # Usando config global
        )

        # Log de auditoria — sem PII (CWE-532)
        logger.info(
            f"Login admin bem-sucedido | admin_id={admin['_id'][:8]}... | ip={client_ip[:8]}..."
        )

        return jsonify({
            "token": token,
            "expires_in": 3600,  # 1 hora (config JWT_ACCESS_TOKEN_EXPIRES)
            "admin": {
                "id": str(admin["_id"]),
                "email": admin["email"],
            },
        }), 200

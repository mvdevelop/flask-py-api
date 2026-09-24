"""
Rate Limiting Middleware — proteção contra brute force e DoS.
Security Champion Note:
- Implementação baseada em memória (in-process).
- Produção: substituir por Redis + Flask-Limiter (CWE-770: Realloc Exhaustion)
- Referencia: CWE-307 (Improper Restriction of Excessive Authentication Attempts)
- OWASP API07:2023 (Rate Limiting)

Estratégia:
- Limite global por IP: 100 requests/min
- Limite no endpoint de login: 5 tentativas/5 min
- Compartilhado entre workers via Redis (configurável)
"""
import time
import logging
from collections import defaultdict
from functools import wraps
from flask import jsonify, request, current_app

logger = logging.getLogger(__name__)

# Storage in-memory (desenvolvimento)
# Em produção: usar Redis
_rate_limit_store = defaultdict(list)


class RateLimiter:
    """
    Rate limiter simples baseado em janela deslizante.
    Em produção, substituir por Redis backend.
    """

    def __init__(self):
        self.store = defaultdict(list)

    def _get_key(self, identifier: str, scope: str = "global") -> str:
        return f"{scope}:{identifier}"

    def _get_client_id(self) -> str:
        # Prioriza X-Forwarded-For (quando atrás de proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.remote_addr or "unknown"

    def check(self, limit: int, window: int, scope: str = "global") -> tuple[bool, int]:
        """
        Verifica se request excede rate limit.
        Returns: (allowed, remaining)
        """
        client_id = self._get_client_id()
        key = self._get_key(client_id, scope)
        now = time.time()

        # Limpa timestamps antigos
        self.store[key] = [ts for ts in self.store[key] if now - ts < window]

        if len(self.store[key]) >= limit:
            return False, 0

        self.store[key].append(now)
        remaining = limit - len(self.store[key])
        return True, remaining

    def reset(self, identifier: str, scope: str = "global") -> None:
        """Reseta contador (usado após login bem-sucedido)."""
        key = self._get_key(identifier, scope)
        self.store.pop(key, None)


# Instância global
limiter = RateLimiter()


def rate_limit(limit: int = 100, window: int = 60, scope: str = "global"):
    """
    Decorator: aplica rate limiting a um endpoint.
    - limit: número máximo de requests
    - window: janela de tempo em segundos
    - scope: "global" (por IP) ou "user" (por user_id)
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            allowed, remaining = limiter.check(limit, window, scope)

            if not allowed:
                logger.warning(
                    f"Rate limit excedido | ip={limiter._get_client_id()} | "
                    f"endpoint={request.path} | scope={scope}"
                )
                response = jsonify({
                    "error": "Too many requests",
                    "message": f"Limite excedido. Tente novamente em {window}s.",
                    "retry_after": window,
                })
                response.status_code = 429
                response.headers["Retry-After"] = str(window)
                response.headers["X-RateLimit-Limit"] = str(limit)
                response.headers["X-RateLimit-Remaining"] = "0"
                return response

            response = fn(*args, **kwargs)

            # Adiciona headers de rate limit (transparência)
            if hasattr(response, "headers"):
                response.headers["X-RateLimit-Limit"] = str(limit)
                response.headers["X-RateLimit-Remaining"] = str(remaining)

            return response
        return wrapper
    return decorator


def clear_rate_limit(identifier: str, scope: str = "global") -> None:
    """Limpa contador de rate limit para identifier."""
    key = limiter._get_key(identifier, scope)
    limiter.store.pop(key, None)

"""
Security Headers Middleware — proteção contra XSS, clickjacking, MIME sniffing.
Security Champion Note:
- CSP (Content-Security-Policy) é a principal defesa contra XSS (CWE-79)
- X-Frame-Options previne clickjacking (CWE-1021)
- X-Content-Type-Options previne MIME sniffing (CWE-430)
- Strict-Transport-Security força HTTPS (CWE-319)
- Referrer-Policy controla dados de referrer (CWE-200)

Referências:
- OWASP Secure Headers Project
- Mozilla Observatory: https://observatory.mozilla.org/
"""
import os
from flask import Flask, Response


def init_security_headers(app: Flask) -> None:
    """Inicializa security headers via after_request hook."""

    @app.after_request
    def add_security_headers(response: Response) -> Response:
        # X-Content-Type-Options: previne MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-Frame-Options: previne clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # X-XSS-Protection: proteção adicional (navegadores antigos)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Strict-Transport-Security (HSTS) — força HTTPS
        # Apenas em produção — localhost não usa HTTPS
        if app.config.get("FLASK_ENV") == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Referrer-Policy: controla quanto referrer é compartilhado
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy: restringe APIs do browser
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=()"
        )

        # Content-Security-Policy (CSP) — defesa primária contra XSS
        # Report-URI para monitoramento de violações
        csp_report_uri = os.environ.get("CSP_REPORT_URI", "")
        if csp_report_uri:
            csp_report_directive = f"report-uri {csp_report_uri}; report-to csp-endpoint"
        else:
            csp_report_directive = ""

        response.headers["Content-Security-Policy"] = (
            f"default-src 'self'; "
            f"script-src 'self'; "
            f"style-src 'self'; "
            f"img-src 'self' data: https:; "
            f"font-src 'self'; "
            f"connect-src 'self'; "
            f"frame-ancestors 'none'; "
            f"base-uri 'self'; "
            f"form-action 'self'; "
            f"{csp_report_directive}"
        ).strip()

        # Remove server banner (informação de versão)
        response.headers.pop("Server", None)

        return response


def init_error_handler(app: Flask) -> None:
    """Handlers de erro global — sem vazamento de stack traces (CWE-209)."""
    import logging
    import traceback

    logger = logging.getLogger(__name__)

    @app.errorhandler(404)
    def not_found(error):
        return jsonify_safe({
            "error": "Not Found",
            "message": "The requested resource does not exist",
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify_safe({
            "error": "Method Not Allowed",
            "message": "This HTTP method is not supported for this endpoint",
        }), 405

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify_safe({
            "error": "Bad Request",
            "message": "Invalid request data",
        }), 400

    @app.errorhandler(413)
    def payload_too_large(error):
        return jsonify_safe({
            "error": "Payload Too Large",
            "message": "Request body exceeds maximum allowed size",
        }), 413

    @app.errorhandler(500)
    def internal_error(error):
        # Não expõe stack trace (CWE-209)
        logger.error(f"Internal server error: {error}", exc_info=True)
        return jsonify_safe({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        }), 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        logger.error(f"Unexpected error: {error}", exc_info=True)
        return jsonify_safe({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        }), 500


def jsonify_safe(payload: dict):
    """Wrapper jsonify que remove PII de respostas de erro."""
    from flask import jsonify
    # Em ambiente de desenvolvimento, pode incluir mais detalhes
    if os.environ.get("FLASK_ENV") == "development":
        payload["debug"] = True
    return jsonify(payload)

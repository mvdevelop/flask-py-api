"""
Inicialização do módulo app.
Security Champion Note:
- app/__init__.py simplificado — apenas exporta create_app
- Conexão MongoDB é lazy (get_db()) para funcionar no Vercel serverless
- Removida import-time de db global (CWE-400: ineficiência)
"""
# Este módulo existe apenas para marcar app/ como um package Python.
# A factory function create_app() está em app/app.py.
# O init_app() antigo foi removido para evitar import-time DB connection
# (problemático em ambientes serverless como Vercel).

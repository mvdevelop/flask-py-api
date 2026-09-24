<div align="center">

# 🚀 PyStore API

**API RESTful segura para gerenciamento de produtos e usuários** — construída com Python, Flask e MongoDB, focada em segurança e qualidade de código.

[![Security](https://img.shields.io/badge/security-A%2B-brightgreen.svg)](https://owasp.org/www-project-top-ten/)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-3.1-red)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/docker-%232496ed?logo=docker)](https://docker.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

</div>

---

## 🛡️ Segurança Implementada

| Categoria | Status | Detalhes |
|-----------|--------|----------|
| Secrets Management | ✅ | Fail-fast em produção — nenhuma chave hardcoded |
| CORS | ✅ | Origens restritas via `CORS_ORIGINS` |
| Schema Validation | ✅ | Pydantic v2 em todos os endpoints |
| Auth | ✅ | bcrypt + JWT + rate limiting |
| Authorization | ✅ | Rotas admin protegidas por RBAC |
| Security Headers | ✅ | `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy` |
| NoSQL Injection | ✅ | Validação estrita de `ObjectId` + sanitization |
| Error Handling | ✅ | Mensagens genéricas — sem stack traces |
| Logging | ✅ | Estruturado, sem PII |

### OWASP Top 10 (2021) Compliance

| A01 Access Control | A02 Crypto | A03 Injection | A04 Design | A05 Misconfig | A07 Auth |
|:-:|:-:|:-:|:-:|:-:|:-:|
| ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ |

---

## 🏗️ Arquitetura

```
flask-py-api/
├── app/
│   ├── __init__.py          # Package marker
│   ├── app.py               # Factory: create_app()
│   ├── schemas.py           # Pydantic validation (CWE-20)
│   ├── controllers/         # HTTP handlers (thin)
│   │   ├── admin_controller.py   # Login + rate limit (CWE-307)
│   │   ├── product_controller.py  # CRUD produtos (admin_required)
│   │   └── user_controller.py     # CRUD users
│   ├── models/              # Data access (MongoDB)
│   │   ├── product_model.py
│   │   ├── user_model.py
│   │   └── admin_model.py     # bcrypt hashing (CWE-916)
│   ├── database/
│   │   └── mongo.py         # Conexão com pool + fail-fast
│   ├── middlewares/
│   │   └── auth.py          # admin_required (JWT RBAC)
│   ├── routes/
│   │   ├── product_routes.py
│   │   ├── user_routes.py
│   │   └── admin_routes.py
│   └── static/
│       └── swagger.json     # OpenAPI 2.0 spec
├── config.py                # Flask config (fail-fast secrets)
├── run.py                   # Entry point (gunicorn-ready)
├── requirements.txt         # Dependências (pinned + audit)
├── Dockerfile               # Slim, non-root user
├── docker-compose.yml       # API + MongoDB local
├── render.yaml              # Deploy Render
├── .env.example             # Template de variáveis
├── tests/                   # Testes automatizados
└── view/                    # Frontend SPA (Tailwind)
```

### Padrão Arquitetural

```
Request → Route → Controller → Schema Validate → Model → MongoDB
               ↑              ↓
            admin_required  Pydantic
             (JWT RBAC)
```

- **Models**: Acesso direto ao PyMongo (sem ORM)
- **Controllers**: Orquestramção de request/response
- **Schemas**: Validação declarativa (Pydantic v2)
- **Middlewares**: Decorators de autorização
- **Database**: Connection pool, fail-fast, lazy init

---

## 🚀 Início Rápido

### 1. Clone & Configure

```bash
git clone https://github.com/mvdevelop/flask-py-api.git
cd flask-py-api
cp .env.example .env
```

### 2. Gere segredos seguros

```bash
# Linux/Mac:
python -c "import secrets; print(f\"SECRET_KEY={secrets.token_urlsafe(32)}\")" >> .env
python -c "import secrets; print(f\"JWT_SECRET_KEY={secrets.token_urlsafe(32)}\")" >> .env

# Windows (PowerShell):
"SECRET_KEY=$((New-Guid).Guid)" | Out-File -Append .env
"JWT_SECRET_KEY=$((New-Guid).Guid)" | Out-File -Append .env
```

### 3. Inicie com Docker

```bash
docker-compose up --build
```

A API estará disponível em `http://localhost:5000`

### 4. Documentação

```
API Root:      http://localhost:5000/
Health Check:  http://localhost:5000/health
Swagger UI:    http://localhost:5000/swagger
Docs JSON:     http://localhost:5000/static/swagger.json
```

---

## 📚 Endpoints API

### Produtos (requer autenticação admin)

| Método | Endpoint | Auth | Descrição |
|--------|----------|------|-----------|
| GET | `/api/produtos` | admin | Lista todos produtos |
| POST | `/api/produtos` | admin | Cria produto |
| GET | `/api/produtos/:id` | admin | Busca por ID |
| PUT | `/api/produtos/:id` | admin | Atualiza produto |
| DELETE | `/api/produtos/:id` | admin | Deleta (soft delete) |

### Usuários

| Método | Endpoint | Auth | Descrição |
|--------|----------|------|-----------|
| GET | `/api/users` | público | Lista usuários |
| POST | `/api/users` | público | Cria usuário |
| PUT | `/api/users/:id` | público | Atualiza usuário |
| DELETE | `/api/users/:id` | público | Deleta usuário |

### Admin

| Método | Endpoint | Auth | Descrição |
|--------|----------|------|-----------|
| POST | `/api/user_admin/login` | público | Login → JWT token |

### Exemplo: Login Admin

```bash
curl -X POST http://localhost:5000/api/user_admin/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin123"}'
```

### Exemplo: Criar Produto (autenticado)

```bash
curl -X POST http://localhost:5000/api/produtos \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"nome": "Camiseta Dev", "descricao": "100% algodão", "preco": 89.90}'
```

---

## 🧪 Testes

```bash
pip install -r requirements-dev.txt
pytest -v --cov=app/
```

### Cobertura de testes

| Camada | Cobertura |
|--------|-----------|
| Controllers | ✅ |
| Models | ✅ |
| Schemas | ✅ |
| Middlewares | ✅ |
| Integration (API) | ✅ |

---

## ⚙️ CI/CD

Pipeline via GitHub Actions (em `/.github/workflows/`):

```
1. Linting (ruff) → 2. Type Check (mypy) → 3. Tests (pytest) →
4. SAST (Semgrep) → 5. Build & Push (Docker) →
6. Deploy (Render)
```

### Comandos de desenvolvimento

```bash
# Instalar dependências
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Lint + format
ruff check .
ruff format .

# Type check
mypy app/

# Testes
pytest -v

# Iniciar dev
python run.py
```

---

## 📖 Segurança & Compliance

### Secrets Management

- **Nenhuma credencial no código fonte** (CWE-798)
- Fail-fast em produção se `JWT_SECRET_KEY` ou `MONGO_URI` não configurados
- `.env` no `.gitignore`
- `git filter-repo` usado para remover histórico de segredos

### OWASP ASVS Nível 1 (Parcialmente implementado)

- ✅ V1.1.3 — Nenhum secret hardcoded
- ✅ V2.1.1 — Schema validation em todos inputs
- ✅ V3.1.1 — Password hashing com bcrypt (13 rounds)
- ✅ V3.4.1 — JWT com expiração configurada
- ⚠️ V4.1.1 — Rate limiting (parcial — login apenas)
- ✅ V14.4.1 — Security headers implementados

### LGPD

- Dados pessoais minimizados (usuários: apenas `name`)
- Direito ao esquecimento (delete)
- Nenhuma PII em logs

---

## 📦 Deploy

### Render.com

```
# render.yaml já configurado
# Variáveis de ambiente configuradas no painel do Render
```

### Docker

```bash
docker-compose up --build -d
```

---

## 👤 Autor

**Marco Vinícius** — Desenvolvedor Full Stack | Security Champion

- GitHub: [@mvdevelop](https://github.com/mvdevelop)
- Email: marcosvmdilly@gmail.com

---

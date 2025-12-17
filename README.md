
# Flask Python API

API simples desenvolvida em **Python** utilizando **Flask**, organizada no **padrão MVC** e documentada com **Swagger (Swagger UI)**.

---

## 🚀 Tecnologias

- Python 3.10+
- Flask
- Flask-Swagger-UI
- Swagger (OpenAPI 2.0)
- Virtualenv (venv)

---

## 📁 Estrutura do Projeto

flask-py-api/
├── app/
│ ├── controllers/
│ ├── models/
│ ├── routes/
│ ├── swagger/
│ │ └── swagger.json
│ └── app.py
├── run.py
├── requirements.txt
└── README.md

yaml
Copiar código

---

## ⚙️ Instalação

### 1️⃣ Clone o repositório

```bash
git clone https://github.com/mvdevelop/flask-py-api.git
cd flask-py-api
2️⃣ Crie e ative o ambiente virtual
bash
Copiar código
python3 -m venv venv
source venv/bin/activate
3️⃣ Instale as dependências
bash
Copiar código
pip install -r requirements.txt
▶️ Executando a aplicação
bash
Copiar código
python run.py

A aplicação estará disponível em:

arduino
Copiar código
http://localhost:3000
📚 Documentação (Swagger)
A API possui documentação interativa via Swagger UI:

bash
Copiar código
http://localhost:3000/swagger
🛣️ Endpoints Disponíveis
🔹 Listar usuários
http
Copiar código
GET /api/users
🔹 Criar usuário
http
Copiar código
POST /api/users
Body:

json
Copiar código
{
  "name": "João"
}
🔹 Atualizar usuário
http
Copiar código
PUT /api/users/{id}
Body:

json
Copiar código
{
  "name": "Novo Nome"
}
🔹 Remover usuário
http
Copiar código
DELETE /api/users/{id}
🧠 Padrão de Arquitetura
Este projeto segue o padrão MVC (Model–View–Controller):

Model: responsável pelos dados e regras de negócio

Controller: responsável pela lógica e validações

Routes: responsável pelo roteamento da API

🧪 Testes
Os endpoints podem ser testados diretamente pelo:

Swagger UI

Postman / Insomnia

Curl

📌 Observações
Os dados são armazenados em memória (sem banco de dados)

Ideal para estudos, testes e projetos iniciais

Fácil adaptação para bancos como SQLite, PostgreSQL ou MongoDB

🔮 Próximos Passos
Persistência com banco de dados

Autenticação JWT

Validações com Pydantic / Marshmallow

Migração para FastAPI

👤 Autor
mvdevelop
GitHub: https://github.com/mvdevelop

📄 Licença
Este projeto está sob a licença MIT.

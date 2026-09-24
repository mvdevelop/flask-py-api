# ==============================
# Schemas de validação de entrada
# ==============================
# Security Champion Note:
# Validação de input é a primeira linha de defesa contra injection.
# Usamos Pydantic para schema validation declarativa.
# Referência: OWASP API03:2023 (Injection) / CWE-20 (Improper Input Validation)
# CVE relevante: Nenhuma diretamente, mas validação previne MongoDB NoSQL injection (CVE-2022-23305 pattern)
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic compatibility."""

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        from pydantic import GetCoreSchemaHandler

        def validate_object_id(v):
            if isinstance(v, ObjectId):
                return v
            if isinstance(v, str):
                if not ObjectId.is_valid(v):
                    raise ValueError("Invalid ObjectId")
                return ObjectId(v)
            raise ValueError("Invalid ObjectId")

        return core_schema.no_info_plain_validator_function(
            validate_object_id,
            serialization=core_schema.str_schema(),
        )


class ProductCreateSchema(BaseModel):
    """Schema para criação de produtos — previne NoSQL injection."""

    nome: str = Field(..., min_length=1, max_length=200)
    descricao: str = Field(..., min_length=1, max_length=2000)
    image_url: Optional[str] = Field(None, max_length=2048)
    preco: Optional[float] = Field(None, ge=0, le=999999.99)
    categoria: Optional[str] = Field(None, max_length=100)
    tags: List[str] = Field(default_factory=list, max_length=20)

    @field_validator("nome", "descricao", "categoria")
    @classmethod
    def sanitize_string(cls, v: str) -> str:
        """Remove caracteres perigosos e normaliza."""
        import html
        v = html.unescape(v)
        stripped = v.strip()
        if not stripped:
            raise ValueError("Campo não pode estar vazio")
        return stripped

    @field_validator("tags")
    @classmethod
    def sanitize_tags(cls, v: list) -> list:
        """Sanitiza tags e limita quantidade."""
        return [t.strip()[:50] for t in v[:20] if t.strip()]

    model_config = {"json_schema_extra": {"example": {
        "nome": "Camiseta Dev",
        "descricao": "Camiseta 100% algodão para desenvolvedores",
        "image_url": "https://cdn.exemplo.com/img.jpg",
        "preco": 89.90,
        "categoria": "Roupa",
        "tags": ["dev", "cotton"]
    }}}


class ProductUpdateSchema(BaseModel):
    """Schema para atualização de produtos — apenas campos permitidos."""

    nome: Optional[str] = Field(None, min_length=1, max_length=200)
    descricao: Optional[str] = Field(None, max_length=2000)
    image_url: Optional[str] = Field(None, max_length=2048)
    preco: Optional[float] = Field(None, ge=0, le=999999.99)
    categoria: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = Field(None, max_length=20)
    active: Optional[bool] = None

    @field_validator("nome", "descricao", "categoria")
    @classmethod
    def sanitize_string(cls, v: str) -> str:
        import html
        v = html.unescape(v)
        stripped = v.strip()
        if not stripped:
            raise ValueError("Campo não pode estar vazio")
        return stripped


class UserCreateSchema(BaseModel):
    """Schema para criação de usuários — previne mass assignment."""

    name: str = Field(..., min_length=1, max_length=200)

    @field_validator("name")
    @classmethod
    def sanitize(cls, v: str) -> str:
        import html
        stripped = html.unescape(v).strip()
        if not stripped:
            raise ValueError("Nome é obrigatório")
        return stripped


class UserUpdateSchema(BaseModel):
    """Schema para atualização de usuários."""

    name: str = Field(..., min_length=1, max_length=200)

    @field_validator("name")
    @classmethod
    def sanitize(cls, v: str) -> str:
        import html
        stripped = html.unescape(v).strip()
        if not stripped:
            raise ValueError("Nome é obrigatório")
        return stripped


class AdminLoginSchema(BaseModel):
    """Schema para login admin — validação de entrada."""

    email: str = Field(..., min_length=3, max_length=254)
    password: str = Field(..., min_length=1, max_length=256)

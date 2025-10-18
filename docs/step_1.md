# Estrutura do Projeto e Configuração Inicial

Neste primeiro step, vamos criar a estrutura base do projeto FastAPI seguindo as melhores práticas de arquitetura em camadas, implementar endpoints robustos e configurar validação avançada com Pydantic.

---

## 🎯 O que você vai aprender

- Estrutura de projeto em camadas profissional
- Configuração com Pydantic Settings
- Implementação de endpoints CRUD completos
- Validação avançada com Pydantic
- Tratamento de erros estruturado
- Dependências reutilizáveis
- Sistema de logging e monitoramento

---

## 🏗️ Estrutura do Projeto em Camadas

### 📁 Estrutura Recomendada

A arquitetura em camadas oferece melhor organização e separação de responsabilidades:

```bash
src/
├── main.py                 # Ponto de entrada da aplicação
├── api/
│   ├── __init__.py
│   ├── dependencies.py     # Dependências comuns
│   └── v1/
│       ├── __init__.py
│       ├── api.py         # Agregador de routers
│       └── endpoints/
│           ├── __init__.py
│           ├── items.py
│           ├── users.py
│           └── categories.py
├── core/
│   ├── __init__.py
│   ├── config.py          # Configurações
│   └── security.py        # Segurança
├── db/
│   ├── __init__.py
│   ├── session.py         # Sessão do banco
│   ├── models/
│   │   ├── __init__.py
│   │   ├── item.py
│   │   └── user.py
│   └── repository/
│       ├── __init__.py
│       ├── base.py
│       ├── item_repository.py
│       └── user_repository.py
├── schemas/
│   ├── __init__.py
│   ├── item.py
│   ├── user.py
│   └── token.py
├── services/
│   ├── __init__.py
│   ├── base_service.py
│   ├── item_service.py
│   └── user_service.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    └── test_items.py
```

**Vantagens desta estrutura em camadas:**

- ✅ **Arquitetura em camadas** bem definida (API → Service → Repository → DB)
- ✅ **Separação clara** de responsabilidades por domínio
- ✅ **Escalabilidade** para projetos grandes
- ✅ **Testabilidade** com injeção de dependências

---

## ⚙️ Configuração de Ambiente

### 🔧 Arquivo de Configuração (.env)

Primeiro, crie um arquivo `.env` na raiz do projeto para armazenar variáveis sensíveis:

```bash
# Configurações da aplicação
APP_NAME="Minha API FastAPI"
APP_VERSION="1.0.0"
DEBUG=true

# Configurações do banco de dados
DATABASE_URL="sqlite:///./app.db"
# Para PostgreSQL: postgresql://user:password@localhost/dbname
# Para MySQL: mysql://user:password@localhost/dbname

# Configurações de segurança
SECRET_KEY="sua-chave-secreta-super-segura-aqui"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Configurações de email (opcional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-de-app
```

### 📋 Classe de Configurações

```python
# (app/core/config.py)
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """
    Configurações da aplicação usando Pydantic.
    
    As configurações são carregadas automaticamente do arquivo .env
    e podem ser sobrescritas por variáveis de ambiente do sistema.
    """
    # Configurações básicas da aplicação
    app_name: str = "FastAPI Guide API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Configurações do banco de dados
    database_url: str = "sqlite:///./app.db"
    
    # Configurações de segurança JWT
    secret_key: str = "change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Configurações de email (opcional)
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_user: str | None = None
    smtp_password: str | None = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Instância global das configurações
settings = Settings()
```

**Por que usar Pydantic Settings?**

- ✅ **Validação automática** de tipos
- ✅ **Carregamento automático** do .env
- ✅ **Documentação integrada** dos campos
- ✅ **Sobrescrita por variáveis** de ambiente

---

## 🚀 Aplicação Principal

### 🎯 Configuração Completa da Aplicação

```python
# (app/main.py)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.core.config import settings
from app.routes import auth, users, tasks

# Criar instância do FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    ## API Completa com FastAPI
    
    Uma API moderna e robusta que inclui:
    * **Autenticação JWT** - Sistema seguro de login
    * **Gerenciamento de Usuários** - CRUD completo
    * **Sistema de Tarefas** - Organização pessoal
    * **Documentação Automática** - Swagger UI integrado
    
    ### Como usar
    1. Registre-se em `/auth/register`
    2. Faça login em `/auth/login`
    3. Use o token nas rotas protegidas
    """,
    contact={
        "name": "Sua Equipe de Desenvolvimento",
        "email": "dev@suaempresa.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Configurar CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],  # URLs do frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de segurança para hosts confiáveis
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.suaempresa.com"]
)

# Incluir rotas
app.include_router(auth.router, prefix="/auth", tags=["Autenticação"])
app.include_router(users.router, prefix="/users", tags=["Usuários"])
app.include_router(tasks.router, prefix="/tasks", tags=["Tarefas"])

# Rota de saúde da aplicação
@app.get("/", tags=["Sistema"])
def root():
    """
    Endpoint de verificação de saúde da API.
    
    Retorna informações básicas sobre o status da aplicação.
    """
    return {
        "message": f"Bem-vindo à {settings.app_name}!",
        "version": settings.app_version,
        "status": "online",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health", tags=["Sistema"])
def health_check():
    """
    Endpoint detalhado de verificação de saúde.
    
    Usado por ferramentas de monitoramento para verificar
    se a aplicação está funcionando corretamente.
    """
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": "development" if settings.debug else "production"
    }

# Evento de inicialização
@app.on_event("startup")
async def startup_event():
    """Executado quando a aplicação inicia"""
    print(f"🚀 {settings.app_name} v{settings.app_version} iniciada!")
    print(f"📚 Documentação disponível em: http://localhost:8000/docs")

# Evento de encerramento
@app.on_event("shutdown")
async def shutdown_event():
    """Executado quando a aplicação é encerrada"""
    print(f"👋 {settings.app_name} encerrada!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
```

### 🔧 Componentes da Aplicação Principal

**1. Configuração do FastAPI:**

- ✅ **Título e versão** dinâmicos das configurações
- ✅ **Descrição rica** com Markdown
- ✅ **Informações de contato** e licença
- ✅ **URLs personalizadas** para documentação

**2. Middlewares de Segurança:**

- ✅ **CORS**: Controla acesso de diferentes origens
- ✅ **TrustedHost**: Previne ataques de Host Header
- ✅ **Configuração flexível** para desenvolvimento e produção

**3. Organização de Rotas:**

- ✅ **Prefixos organizados** por funcionalidade
- ✅ **Tags para documentação** automática
- ✅ **Separação modular** de responsabilidades

**4. Endpoints de Sistema:**

- ✅ **Health check** para monitoramento
- ✅ **Informações da aplicação** para debugging
- ✅ **Eventos de ciclo de vida** para logs

---

## 🎯 Próximos Passos

Agora que você tem a estrutura base configurada, no próximo step vamos implementar:

1. **Modelos de dados** com SQLAlchemy
2. **Schemas de validação** com Pydantic
3. **Primeiros endpoints** funcionais
4. **Sistema de autenticação** JWT

### 🚀 Para Testar Agora

1. Crie a estrutura de pastas
2. Configure o arquivo `.env`
3. Implemente `config.py` e `main.py`
4. Execute: `uvicorn app.main:app --reload`
5. Acesse: `http://localhost:8000/docs`

**Resultado esperado:** Documentação automática funcionando com endpoints básicos de sistema!

---

## 📝 Exemplos Avançados de Request Body

### Múltiplos Bodies

```python
@router.post("/items/{item_id}/review")
def create_review(
    item_id: int,
    review: ReviewCreate,
    metadata: dict = Body(...)
):
    return {"item_id": item_id, "review": review, "metadata": metadata}
```

### Headers e Cookies

```python
from fastapi import Header, Cookie

@router.get("/items/")
def get_items(
    user_agent: str | None = Header(None),
    session_id: str | None = Cookie(None)
):
    return {"user_agent": user_agent, "session_id": session_id}
```

---

## ✅ Validações Avançadas

### Validações de Campo

```python
from pydantic import BaseModel, Field, validator

class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0, description="Preço deve ser positivo")
    email: str = Field(..., regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Nome não pode estar vazio')
        return v.strip().title()
    
    @validator('price')
    def price_must_be_reasonable(cls, v):
        if v > 10000:
            raise ValueError('Preço muito alto')
        return v
```

### Validações de Modelo

```python
from pydantic import BaseModel, root_validator

class ItemUpdate(BaseModel):
    name: str | None = None
    price: float | None = None
    discount_price: float | None = None
    
    @root_validator
    def validate_prices(cls, values):
        price = values.get('price')
        discount_price = values.get('discount_price')
        
        if price and discount_price and discount_price >= price:
            raise ValueError('Preço com desconto deve ser menor que o preço normal')
        
        return values
```

---

## 📚 Documentação Automática

### Configurando Metadados

```python
from fastapi import FastAPI

app = FastAPI(
    title="FastAPI Guide API",
    description="""
    API completa para aprendizado de FastAPI.
    
    ## Items
    Você pode **criar**, **ler**, **atualizar** e **deletar** itens.
    
    ## Users
    Gerenciamento completo de usuários.
    """,
    version="1.0.0",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Seu Nome",
        "url": "http://example.com/contact/",
        "email": "contato@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)
```

### Tags e Metadados de Endpoints

```python
@router.post(
    "/",
    response_model=ItemResponse,
    status_code=201,
    summary="Criar novo item",
    description="Criar um novo item no sistema com validação completa",
    response_description="Item criado com sucesso",
    tags=["Items"]
)
def create_item(item_data: ItemCreate):
    """
    Criar um novo item com todas as informações:
    
    - **name**: nome do item (obrigatório)
    - **description**: descrição detalhada (opcional)
    - **price**: preço em reais (obrigatório, > 0)
    - **category_id**: ID da categoria (obrigatório)
    """
    pass
```

---

## 🧪 Testando sua API

### Teste Manual

Execute a aplicação:

```bash
uvicorn main:app --reload
```

Acesse:

- **API**: `http://localhost:8000`
- **Documentação Swagger**: `http://localhost:8000/docs`
- **Documentação ReDoc**: `http://localhost:8000/redoc`

### Teste com curl

```bash
# GET - Listar itens
curl -X GET "http://localhost:8000/api/v1/items/"

# POST - Criar item
curl -X POST "http://localhost:8000/api/v1/items/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Notebook",
    "description": "Notebook para desenvolvimento",
    "price": 2500.00,
    "category_id": 1
  }'

# GET - Buscar item específico
curl -X GET "http://localhost:8000/api/v1/items/1"

# PUT - Atualizar item
curl -X PUT "http://localhost:8000/api/v1/items/1" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Notebook Gamer",
    "price": 3000.00
  }'

# DELETE - Deletar item
curl -X DELETE "http://localhost:8000/api/v1/items/1"
```

---

## 🎯 Próximos Passos

Agora que você tem uma API completa funcionando, está pronto para:

1. Integrar com banco de dados real
2. Implementar autenticação e autorização
3. Adicionar testes automatizados
4. Configurar cache e otimizações

---

## 📝 Exercícios Práticos

### Exercício 1: Expandir a API

Adicione endpoints para categorias:

- `GET /categories/` - Listar categorias
- `POST /categories/` - Criar categoria
- `GET /categories/{id}` - Buscar categoria
- `PUT /categories/{id}` - Atualizar categoria
- `DELETE /categories/{id}` - Deletar categoria

### Exercício 2: Validações Customizadas

Implemente validações para:

- Nome do item deve ser único
- Preço não pode ser negativo
- Categoria deve existir antes de criar item

### Exercício 3: Filtros Avançados

Adicione filtros para:

- Buscar itens por faixa de preço
- Ordenar por preço, nome ou data
- Buscar itens criados em período específico

---

**Anterior:** [Step 0: Fundamentos](step_0.md) | **Próximo:** [Step 2: Banco de Dados](step_2.md)

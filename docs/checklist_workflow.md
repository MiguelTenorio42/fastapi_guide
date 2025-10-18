# 🚀 Workflow Completo FastAPI

Este é um guia prático e sequencial para criar uma API FastAPI profissional do zero até a produção.

## 📋 Checklist Geral

### ✅ Fase 1: Configuração Inicial

- [ ] Ambiente de desenvolvimento configurado
- [ ] Estrutura de projeto criada
- [ ] Dependências instaladas
- [ ] Git inicializado

### ✅ Fase 2: Desenvolvimento Core

- [ ] Modelos de dados definidos
- [ ] Endpoints básicos criados
- [ ] Autenticação implementada
- [ ] Validações configuradas

### ✅ Fase 3: Produção

- [ ] Testes implementados
- [ ] Docker configurado
- [ ] Deploy realizado
- [ ] Monitoramento ativo

---

## 1️⃣ Configuração Inicial

### 1.1 Ambiente de Desenvolvimento

- [ ] Python 3.13+ instalado
- [ ] Editor/IDE configurado (VS Code recomendado)
- [ ] Git configurado
- [ ] Terminal/PowerShell disponível

:::{dropdown} 📋 Comandos para Configuração

```bash
# Criar e navegar para o diretório
mkdir meu-projeto-fastapi
cd meu-projeto-fastapi

# Inicializar Git
git init

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

:::

### 1.2 Estrutura do Projeto

- [ ] Criar estrutura de diretórios
- [ ] Configurar arquivos base (.gitignore, README.md)
- [ ] Organizar módulos por responsabilidade

:::{dropdown} 📋 Estrutura Recomendada

```bash
meu-projeto-fastapi/
├── src/
│   ├── __init__.py
│   ├── main.py          # Aplicação principal
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py    # Configurações
│   │   └── security.py  # Autenticação/Segurança
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── users.py # Rotas de usuários
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models/      # Modelos SQLAlchemy
│   │   └── session.py   # Sessão do banco
├── schemas/
│   ├── __init__.py
│   └── user.py          # Schemas Pydantic
└── services/
    ├── __init__.py
    └── user_service.py  # Lógica de negócio
```

:::

### 1.3 Dependências Essenciais

- [ ] **FastAPI** - Framework principal
- [ ] **Uvicorn** - Servidor ASGI
- [ ] **SQLAlchemy** - ORM
- [ ] **Pydantic** - Validação de dados
- [ ] **Python-jose** - JWT tokens
- [ ] **Passlib** - Hash de senhas
- [ ] **Python-multipart** - Upload de arquivos

:::{dropdown} 📋 Estrutura Recomendada

```bash
# Instalar dependências principais
pip install fastapi uvicorn sqlalchemy pydantic python-jose[cryptography] passlib[bcrypt] python-multipart

# Criar requirements.txt
pip freeze > requirements.txt
```

:::

---

## 2️⃣ Desenvolvimento Core

### 2.1 Estrutura Base

- [ ] Criar aplicação FastAPI
- [ ] Configurar roteamento
- [ ] Implementar middleware básico
- [ ] Configurar CORS

:::{dropdown} 📋 Estrutura de Diretórios

```bash
src/
├── main.py              # Ponto de entrada
├── core/
│   ├── config.py        # Configurações
│   └── security.py      # Autenticação
├── api/v1/
│   └── users.py         # Endpoints
├── db/
│   ├── models/
│   │   └── user.py      # Modelos SQLAlchemy
│   └── session.py       # Conexão DB
├── schemas/
│   ├── __init__.py
│   └── user.py          # Schemas Pydantic
└── services/
    ├── __init__.py
    └── user_service.py  # Lógica de negócio
```

:::

### 2.2 Configuração Básica

- [ ] Criar aplicação FastAPI principal
- [ ] Configurar CORS se necessário
- [ ] Configurar middleware básico
- [ ] Testar servidor local

:::{dropdown} 📋 Código do main.py

```python
# src/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.v1 import users
from src.core.config import settings

app = FastAPI(
    title=settings.project_name,
    version="1.0.0",
    description="API FastAPI Profissional"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configurar adequadamente em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas
app.include_router(users.router, prefix=settings.api_v1_prefix)

@app.get("/")
def read_root():
    return {"message": "API FastAPI funcionando!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

:::

### 2.3 Configurações

- [ ] Criar arquivo de configurações
- [ ] Configurar variáveis de ambiente
- [ ] Implementar settings com Pydantic
- [ ] Configurar diferentes ambientes (dev/prod)

:::{dropdown} 📋 Arquivo de Configuração

```python
# src/core/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    project_name: str = "FastAPI Project"
    api_v1_prefix: str = "/api/v1"
    
    # Database
    database_url: str = "sqlite:///./app.db"
    
    # Security
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    backend_cors_origins: list = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"

settings = Settings()
```

:::

### 2.4 Banco de Dados

- [ ] Configurar SQLAlchemy
- [ ] Criar modelos de dados
- [ ] Implementar sessão do banco
- [ ] Configurar migrações (Alembic)

:::{dropdown} 📋 Configuração do Banco

```python
# src/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.core.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

:::

---

## 3️⃣ Modelos e Schemas

### 3.1 Modelos SQLAlchemy

- [ ] Criar modelo User
- [ ] Definir relacionamentos
- [ ] Configurar índices
- [ ] Implementar timestamps

:::{dropdown} 📋 Modelo User

```python
# src/db/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from src.db.session import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

:::

### 3.2 Schemas Pydantic

- [ ] Criar schemas de entrada
- [ ] Criar schemas de saída
- [ ] Implementar validações
- [ ] Configurar exemplos para documentação

:::{dropdown} 📋 Schemas Pydantic

```python
# schemas/user.py
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    username: str
    is_active: bool = True

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = None
    is_active: bool | None = None

class UserInDB(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime | None
    
    class Config:
        orm_mode = True

class User(UserInDB):
    pass
```

:::

---

## 4️⃣ Autenticação e Segurança

### 4.1 Sistema de Autenticação

- [ ] Implementar hash de senhas
- [ ] Criar sistema JWT
- [ ] Implementar login/logout
- [ ] Configurar dependências de autenticação

:::{dropdown} 📋 Sistema de Segurança

```python
# src/core/security.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from src.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
```

:::

### 4.2 Endpoints de Autenticação

- [ ] Endpoint de registro
- [ ] Endpoint de login
- [ ] Endpoint de refresh token
- [ ] Middleware de autenticação

:::{dropdown} 📋 Endpoints de Auth

```python
# src/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src.db.session import get_db
from src.core.security import verify_password, create_access_token
from src.services.user_service import get_user_by_email

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}
```

:::

---

## 5️⃣ Endpoints e Rotas

### 5.1 CRUD de Usuários

- [ ] GET /users - Listar usuários
- [ ] POST /users - Criar usuário
- [ ] GET /users/{id} - Buscar usuário
- [ ] PUT /users/{id} - Atualizar usuário
- [ ] DELETE /users/{id} - Deletar usuário

:::{dropdown} 📋 Rotas de Usuários

```python
# src/api/v1/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.db.session import get_db
from src.schemas.user import User, UserCreate, UserUpdate
from src.services.user_service import (
    get_users, get_user, create_user, update_user, delete_user
)

router = APIRouter()

@router.get("/", response_model=list[User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = get_users(db, skip=skip, limit=limit)
    return users

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(user: UserCreate, db: Session = Depends(get_db)):
    return create_user(db=db, user=user)

@router.get("/{user_id}", response_model=User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/{user_id}", response_model=User)
def update_user_endpoint(
    user_id: int, user: UserUpdate, db: Session = Depends(get_db)
):
    return update_user(db=db, user_id=user_id, user=user)

@router.delete("/{user_id}")
def delete_user_endpoint(user_id: int, db: Session = Depends(get_db)):
    return delete_user(db=db, user_id=user_id)
```

:::

### 5.2 Validações e Tratamento de Erros

- [ ] Implementar validações customizadas
- [ ] Configurar tratamento de exceções
- [ ] Criar responses padronizados
- [ ] Implementar logging de erros

:::{dropdown} 📋 Tratamento de Erros

```python
# src/core/exceptions.py
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "Validation error",
            "details": exc.errors()
        }
    )
```

:::

---

## 6️⃣ Testes

### 6.1 Configuração de Testes

- [ ] Instalar pytest e dependências
- [ ] Configurar banco de teste
- [ ] Criar fixtures básicas
- [ ] Configurar cliente de teste

:::{dropdown} 📋 Configuração de Testes

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.main import app
from src.db.session import get_db, Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)
```

:::

### 6.2 Testes de Endpoints

- [ ] Testar criação de usuários
- [ ] Testar autenticação
- [ ] Testar validações
- [ ] Testar casos de erro

:::{dropdown} 📋 Testes de Usuários

```python
# tests/test_users.py
def test_create_user(client):
    response = client.post(
        "/api/v1/users/",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"

def test_read_users(client):
    response = client.get("/api/v1/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

:::

---

## 7️⃣ Docker e Deploy

### 7.1 Containerização

- [ ] Criar Dockerfile
- [ ] Configurar docker-compose
- [ ] Otimizar imagem Docker
- [ ] Configurar variáveis de ambiente

:::{dropdown} 📋 Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

:::

### 7.2 Deploy em Produção

- [ ] Configurar servidor de produção
- [ ] Configurar proxy reverso (Nginx)
- [ ] Implementar HTTPS
- [ ] Configurar monitoramento

:::{dropdown} 📋 Docker Compose

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/fastapi_db
    depends_on:
      - db
    
  db:
    image: postgres:13
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=fastapi_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

:::

---

## 8️⃣ Monitoramento e Logs

### 8.1 Logging

- [ ] Configurar sistema de logs
- [ ] Implementar logs estruturados
- [ ] Configurar rotação de logs
- [ ] Monitorar performance

:::{dropdown} 📋 Configuração de Logs

```python
# src/core/logging.py
import logging
import sys
from pathlib import Path

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("app.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Configurar logger específico para a aplicação
    logger = logging.getLogger("fastapi_app")
    return logger
```

:::

### 8.2 Métricas e Saúde

- [ ] Endpoint de health check
- [ ] Métricas de performance
- [ ] Monitoramento de recursos
- [ ] Alertas automáticos

:::{dropdown} 📋 Health Check

```python
# src/api/v1/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.db.session import get_db

router = APIRouter()

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "FastAPI Application",
        "version": "1.0.0"
    }

@router.get("/health/db")
def database_health_check(db: Session = Depends(get_db)):
    try:
        # Teste simples de conexão
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
```

:::

---

## ✅ Checklist Final

### Antes do Deploy

- [ ] Todos os testes passando
- [ ] Documentação atualizada
- [ ] Variáveis de ambiente configuradas
- [ ] Logs configurados
- [ ] Backup do banco configurado

### Pós Deploy

- [ ] Health checks funcionando
- [ ] Monitoramento ativo
- [ ] SSL/HTTPS configurado
- [ ] Performance otimizada
- [ ] Documentação acessível

### Manutenção

- [ ] Atualizações de segurança
- [ ] Backup regular
- [ ] Monitoramento de logs
- [ ] Análise de performance
- [ ] Feedback dos usuários

---

## 🔗 Links Úteis

- [Documentação FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Pydantic Docs](https://pydantic-docs.helpmanual.io/)
- [Pytest Docs](https://docs.pytest.org/)
- [Docker Docs](https://docs.docker.com/)
- [Nginx Docs](https://nginx.org/en/docs/)

---

**🎯 Próximos Passos:** Após completar este workflow, considere implementar funcionalidades avançadas como cache (Redis), filas de tarefas (Celery), WebSockets, ou integração com serviços externos.

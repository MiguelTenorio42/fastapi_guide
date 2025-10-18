# Banco de Dados e Persistência

Agora vamos integrar sua API com um banco de dados real, implementar modelos SQLAlchemy e configurar migrações com Alembic.

## 🎯 O que você vai aprender

- Configurar PostgreSQL com FastAPI
- Criar modelos SQLAlchemy
- Implementar Repository Pattern
- Configurar e usar Alembic para migrações
- Gerenciar sessões de banco de dados
- Implementar CRUD completo

---

## 🗄️ Configuração do Banco de Dados

### Escolha do Driver

**Sync vs Async:**
- **Sync (psycopg):** Modo tradicional, estável, mais fácil de debugar
- **Async (asyncpg):** Melhor performance com alta concorrência

**Recomendação:** Comece com Sync e evolua para Async se necessário.

### Dependências

```bash
pip install sqlalchemy psycopg2-binary alembic
```

Para async:
```bash
pip install sqlalchemy[asyncio] asyncpg
```

### Variáveis de Ambiente (.env)

```bash
# Database
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/fastapi_guide
POOL_SIZE=5
MAX_OVERFLOW=10
ECHO_SQL=false
```
# Para desenvolvimento com Docker
POSTGRES_USER=fastapi_user
POSTGRES_PASSWORD=fastapi_password
POSTGRES_DB=fastapi_guide
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

### Docker Compose para Desenvolvimento

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: fastapi_user
      POSTGRES_PASSWORD: fastapi_password
      POSTGRES_DB: fastapi_guide
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

---

## ⚙️ Configuração SQLAlchemy

### 🎯 Conceitos Fundamentais

**SQLAlchemy** é o ORM (Object-Relational Mapping) mais poderoso do Python, oferecendo:

- **Core**: Interface de baixo nível para SQL
- **ORM**: Mapeamento objeto-relacional de alto nível
- **Engine**: Gerenciamento de conexões e pool
- **Session**: Unidade de trabalho para transações

### 📊 Comparação de Drivers

| Driver | Tipo | Performance | Estabilidade | Uso Recomendado |
|--------|------|-------------|--------------|-----------------|
| `psycopg2` | Síncrono | Boa | Excelente | Aplicações tradicionais |
| `asyncpg` | Assíncrono | Excelente | Boa | Alta concorrência |
| `psycopg` | Híbrido | Muito Boa | Excelente | Projetos modernos |

### Configurações Tipadas (core/config.py)

```python
from pydantic_settings import BaseSettings
from pydantic import Field, PostgresDsn, validator
from typing import Optional, Dict, Any
from enum import Enum

class DatabaseMode(str, Enum):
    SYNC = "sync"
    ASYNC = "async"

class DatabaseSettings(BaseSettings):
    """Configurações avançadas do banco de dados"""
    
    # URLs de conexão
    DATABASE_URL: PostgresDsn = Field(
        ..., 
        description="URL de conexão com PostgreSQL"
    )
    
    # Pool de conexões
    POOL_SIZE: int = Field(default=5, ge=1, le=20)
    MAX_OVERFLOW: int = Field(default=10, ge=0, le=50)
    POOL_TIMEOUT: int = Field(default=30, ge=5, le=300)
    POOL_RECYCLE: int = Field(default=3600, ge=300, le=7200)
    
    # Configurações de comportamento
    ECHO_SQL: bool = Field(default=False)
    POOL_PRE_PING: bool = Field(default=True)
    
    # Modo de operação
    DATABASE_MODE: DatabaseMode = Field(default=DatabaseMode.SYNC)
    
    @validator('DATABASE_URL')
    def validate_database_url(cls, v):
        """Valida e ajusta URL do banco"""
        if not str(v).startswith(('postgresql://', 'postgresql+psycopg://', 'postgresql+asyncpg://')):
            raise ValueError('URL deve ser PostgreSQL válida')
        return v
    
    @property
    def sync_url(self) -> str:
        """URL para conexão síncrona"""
        url = str(self.DATABASE_URL)
        return url.replace('postgresql+asyncpg://', 'postgresql+psycopg://')
    
    @property
    def async_url(self) -> str:
        """URL para conexão assíncrona"""
        url = str(self.DATABASE_URL)
        return url.replace('postgresql+psycopg://', 'postgresql+asyncpg://')
    
    @property
    def engine_config(self) -> dict[str, Any]:
        """Configurações do engine"""
        return {
            'pool_size': self.POOL_SIZE,
            'max_overflow': self.MAX_OVERFLOW,
            'pool_timeout': self.POOL_TIMEOUT,
            'pool_recycle': self.POOL_RECYCLE,
            'pool_pre_ping': self.POOL_PRE_PING,
            'echo': self.ECHO_SQL,
        }

# Instância global
db_settings = DatabaseSettings()
    
    # Database connection retry
    DB_CONNECT_RETRY: int = Field(default=3)
    DB_CONNECT_TIMEOUT: int = Field(default=30)
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### Engine e Sessão (db/session.py)

```python
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import logging

from core.config import settings

logger = logging.getLogger(__name__)

# Configurar engine com pool de conexões
engine = create_engine(
    str(settings.DATABASE_URL),
    poolclass=QueuePool,
    pool_size=settings.POOL_SIZE,
    max_overflow=settings.MAX_OVERFLOW,
    pool_pre_ping=True,  # Verifica conexões antes de usar
    pool_recycle=3600,   # Recicla conexões a cada hora
    echo=settings.ECHO_SQL,
    future=True  # SQLAlchemy 2.0 style
)

# Event listeners para logging
@event.listens_for(engine, "connect")
def receive_connect(dbapi_connection, connection_record):
    logger.info("Nova conexão estabelecida com o banco de dados")

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    logger.debug("Conexão retirada do pool")

# Criar SessionLocal
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True
)

# Base para modelos
Base = declarative_base()

# Dependência para obter sessão
def get_db():
    """
    Dependência para obter sessão do banco de dados.
    Garante que a sessão seja fechada após o uso.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Erro na sessão do banco: {e}")
        db.rollback()
        raise
    finally:
        db.close()
```

---

## 📊 Modelos SQLAlchemy Avançados

### 🧱 Modelo Base com Mixins (db/models/base.py)

```python
from sqlalchemy import Column, Integer, DateTime, Boolean, String, func
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Any, Dict

Base = declarative_base()

class TimestampMixin:
    """Mixin para campos de timestamp automáticos"""
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False,
        comment="Data de criação do registro"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Data da última atualização"
    )

class SoftDeleteMixin:
    """Mixin para soft delete (exclusão lógica)"""
    deleted_at = Column(
        DateTime(timezone=True), 
        nullable=True,
        comment="Data de exclusão lógica"
    )
    is_deleted = Column(
        Boolean, 
        default=False, 
        nullable=False,
        index=True,
        comment="Flag de exclusão lógica"
    )
    
    def soft_delete(self):
        """Marca registro como deletado logicamente"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
    
    def restore(self):
        """Restaura registro deletado"""
        self.is_deleted = False
        self.deleted_at = None

class AuditMixin:
    """Mixin para auditoria de alterações"""
    created_by = Column(Integer, nullable=True, comment="ID do usuário criador")
    updated_by = Column(Integer, nullable=True, comment="ID do último usuário que alterou")
    version = Column(Integer, default=1, nullable=False, comment="Versão do registro")

class BaseModel(Base, TimestampMixin, SoftDeleteMixin):
    """
    Modelo base com funcionalidades comuns:
    - ID auto-incremento
    - Timestamps automáticos
    - Soft delete
    - Métodos utilitários
    """
    __abstract__ = True
    
    id = Column(
        Integer, 
        primary_key=True, 
        index=True,
        comment="Chave primária auto-incremento"
    )
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Gera nome da tabela automaticamente baseado no nome da classe"""
        return cls.__name__.lower() + 's'
    
    def to_dict(self) -> dict[str, Any]:
        """Converte modelo para dicionário"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
            if not column.name.startswith('_')
        }
    
    def update_from_dict(self, data: dict[str, Any], exclude: set = None) -> None:
        """
        Atualiza modelo a partir de dicionário
        
        Args:
            data: Dicionário com os dados
            exclude: Campos a serem excluídos da atualização
        """
        exclude = exclude or {'id', 'created_at', 'updated_at'}
        
        for key, value in data.items():
            if key not in exclude and hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def get_active(cls, db: Session):
        """Retorna query apenas com registros não deletados"""
        return db.query(cls).filter(cls.is_deleted == False)
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"
```

### 👤 Modelo de Usuário com Relacionamentos (db/models/user.py)

```python
from sqlalchemy import Column, String, Boolean, Text, Enum as SQLEnum, Integer
from sqlalchemy.orm import relationship
from enum import Enum
from db.models.base import BaseModel, AuditMixin

class UserRole(str, Enum):
    """Roles de usuário no sistema"""
    ADMIN = "admin"
    MODERATOR = "moderator" 
    USER = "user"
    GUEST = "guest"

class UserStatus(str, Enum):
    """Status do usuário"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"

class User(BaseModel, AuditMixin):
    """
    Modelo de usuário com funcionalidades avançadas:
    - Autenticação e autorização
    - Perfil completo
    - Relacionamentos com outras entidades
    """
    __tablename__ = "users"
    
    # Campos de autenticação
    username = Column(
        String(50), 
        unique=True, 
        index=True, 
        nullable=False,
        comment="Nome de usuário único"
    )
    email = Column(
        String(255), 
        unique=True, 
        index=True, 
        nullable=False,
        comment="Email único do usuário"
    )
    hashed_password = Column(
        String(255), 
        nullable=False,
        comment="Senha hasheada"
    )
    
    # Informações pessoais
    full_name = Column(String(255), nullable=True, comment="Nome completo")
    bio = Column(Text, nullable=True, comment="Biografia do usuário")
    avatar_url = Column(String(500), nullable=True, comment="URL do avatar")
    
    # Status e permissões
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False, index=True)
    status = Column(SQLEnum(UserStatus), default=UserStatus.PENDING, nullable=False)
    
    # Relacionamentos
    items = relationship(
        "Item", 
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="dynamic"  # Carregamento sob demanda para performance
    )
    
    # Métodos de negócio
    @property
    def is_admin(self) -> bool:
        """Verifica se usuário é administrador"""
        return self.role == UserRole.ADMIN
    
    @property
    def can_moderate(self) -> bool:
        """Verifica se usuário pode moderar"""
        return self.role in [UserRole.ADMIN, UserRole.MODERATOR]
    
    @property
    def item_count(self) -> int:
        """Conta itens do usuário"""
        return self.items.filter(Item.is_deleted == False).count()
    
    def can_edit_item(self, item) -> bool:
        """Verifica se pode editar um item"""
        return self.is_admin or item.owner_id == self.id
    
    def activate(self):
        """Ativa usuário"""
        self.is_active = True
        self.status = UserStatus.ACTIVE
    
    def deactivate(self):
        """Desativa usuário"""
        self.is_active = False
        self.status = UserStatus.INACTIVE
```

### 📦 Modelo de Item com Categorização (db/models/item.py)

```python
from sqlalchemy import Column, String, Text, Float, Integer, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from enum import Enum
from db.models.base import BaseModel

class ItemStatus(str, Enum):
    """Status do item"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"

class ItemPriority(str, Enum):
    """Prioridade do item"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Item(BaseModel):
    """
    Modelo de item com relacionamentos e validações:
    - Pertence a um usuário (owner)
    - Pode ter uma categoria
    - Status e prioridade
    - Campos de negócio específicos
    """
    __tablename__ = "items"
    
    # Campos básicos
    title = Column(
        String(200), 
        nullable=False, 
        index=True,
        comment="Título do item"
    )
    description = Column(Text, nullable=True, comment="Descrição detalhada")
    
    # Campos de negócio
    price = Column(
        Float, 
        nullable=True,
        comment="Preço do item"
    )
    quantity = Column(
        Integer, 
        default=0, 
        nullable=False,
        comment="Quantidade disponível"
    )
    
    # Status e controle
    status = Column(
        SQLEnum(ItemStatus), 
        default=ItemStatus.DRAFT, 
        nullable=False,
        index=True
    )
    priority = Column(
        SQLEnum(ItemPriority), 
        default=ItemPriority.MEDIUM, 
        nullable=False
    )
    is_featured = Column(Boolean, default=False, nullable=False)
    
    # Relacionamentos
    # Muitos-para-um: Item pertence a um usuário
    owner_id = Column(
        Integer, 
        ForeignKey('users.id'), 
        nullable=False, 
        index=True,
        comment="ID do proprietário"
    )
    owner = relationship("User", back_populates="items")
    
    # Muitos-para-um: Item pode ter uma categoria
    category_id = Column(
        Integer, 
        ForeignKey('categories.id'), 
        nullable=True, 
        index=True,
        comment="ID da categoria"
    )
    category = relationship("Category", back_populates="items")
    
    # Métodos de negócio
    @property
    def is_available(self) -> bool:
        """Verifica se item está disponível"""
        return (
            self.status == ItemStatus.PUBLISHED and 
            not self.is_deleted and 
            self.quantity > 0
        )
    
    @property
    def is_low_stock(self) -> bool:
        """Verifica se estoque está baixo"""
        return self.quantity <= 5
    
    def publish(self):
        """Publica o item"""
        self.status = ItemStatus.PUBLISHED
    
    def archive(self):
        """Arquiva o item"""
        self.status = ItemStatus.ARCHIVED
    
    def add_stock(self, amount: int):
        """Adiciona estoque"""
        if amount > 0:
            self.quantity += amount
    
    def remove_stock(self, amount: int) -> bool:
        """Remove estoque se disponível"""
        if self.quantity >= amount:
            self.quantity -= amount
            return True
        return False
```

class Item(BaseModel):
    __tablename__ = "items"
    
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False, index=True)
    discount_price = Column(Float, nullable=True)
    is_available = Column(Boolean, default=True, nullable=False)
    stock_quantity = Column(Integer, default=0, nullable=False)
    
    # Foreign Keys
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    
    # Relacionamentos
    category = relationship("Category", back_populates="items")
    
    def __repr__(self):
        return f"<Item(id={self.id}, name='{self.name}', price={self.price})>"
    
    @property
    def effective_price(self):
        """Retorna o preço efetivo (com desconto se houver)"""
        return self.discount_price if self.discount_price else self.price
    
    @property
    def is_in_stock(self):
        """Verifica se o item está em estoque"""
        return self.stock_quantity > 0
```

### Modelo de Usuário (db/models/user.py)

```python
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from db.models.base import BaseModel

class User(BaseModel):
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
```

---

## 🏗️ Repository Pattern

### Repository Base (db/repository/base.py)

```python
from typing import Generic, TypeVar, Type, Optional, List, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from pydantic import BaseModel

from db.session import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db
    
    def get(self, id: int) -> ModelType | None:
        """Buscar por ID"""
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: dict[str, Any] | None = None,
        order_by: str | None = None,
        order_desc: bool = False
    ) -> tuple[list[ModelType], int]:
        """Buscar múltiplos registros com filtros e paginação"""
        query = self.db.query(self.model)
        
        # Aplicar filtros
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    if isinstance(value, str):
                        # Busca parcial para strings
                        query = query.filter(
                            getattr(self.model, field).ilike(f"%{value}%")
                        )
                    else:
                        query = query.filter(getattr(self.model, field) == value)
        
        # Contar total
        total = query.count()
        
        # Aplicar ordenação
        if order_by and hasattr(self.model, order_by):
            order_field = getattr(self.model, order_by)
            if order_desc:
                query = query.order_by(desc(order_field))
            else:
                query = query.order_by(asc(order_field))
        
        # Aplicar paginação
        items = query.offset(skip).limit(limit).all()
        
        return items, total
    
    def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Criar novo registro"""
        obj_data = obj_in.dict() if hasattr(obj_in, 'dict') else obj_in
        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def update(
        self, 
        db_obj: ModelType, 
        obj_in: UpdateSchemaType
    ) -> ModelType:
        """Atualizar registro existente"""
        obj_data = obj_in.dict(exclude_unset=True) if hasattr(obj_in, 'dict') else obj_in
        
        for field, value in obj_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def delete(self, id: int) -> bool:
        """Deletar registro por ID"""
        obj = self.get(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False
    
    def exists(self, id: int) -> bool:
        """Verificar se registro existe"""
        return self.db.query(self.model.id).filter(self.model.id == id).first() is not None
```

### Repository de Item (db/repository/item_repository.py)

```python
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from db.models.item import Item
from db.repository.base import BaseRepository
from schemas.item import ItemCreate, ItemUpdate

class ItemRepository(BaseRepository[Item, ItemCreate, ItemUpdate]):
    def __init__(self, db: Session):
        super().__init__(Item, db)
    
    def get_by_name(self, name: str) -> Item | None:
        """Buscar item por nome"""
        return self.db.query(Item).filter(Item.name == name).first()
    
    def get_by_category(self, category_id: int) -> list[Item]:
        """Buscar itens por categoria"""
        return self.db.query(Item).filter(Item.category_id == category_id).all()
    
    def get_available_items(self, skip: int = 0, limit: int = 100) -> tuple[list[Item], int]:
        """Buscar apenas itens disponíveis"""
        query = self.db.query(Item).filter(Item.is_available == True)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total
    
    def get_items_with_category(self, skip: int = 0, limit: int = 100) -> tuple[list[Item], int]:
        """Buscar itens com informações da categoria"""
        query = self.db.query(Item).options(joinedload(Item.category))
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total
    
    def search_items(self, search_term: str, skip: int = 0, limit: int = 100) -> tuple[list[Item], int]:
        """Buscar itens por termo de busca"""
        query = self.db.query(Item).filter(
            Item.name.ilike(f"%{search_term}%") |
            Item.description.ilike(f"%{search_term}%")
        )
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total
    
    def get_items_by_price_range(
        self, 
        min_price: float, 
        max_price: float,
        skip: int = 0, 
        limit: int = 100
    ) -> tuple[list[Item], int]:
        """Buscar itens por faixa de preço"""
        query = self.db.query(Item).filter(
            Item.price >= min_price,
            Item.price <= max_price
        )
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total
```

---

## 🔄 Migrações com Alembic

### Configuração Inicial

```bash
# Inicializar Alembic
alembic init alembic

# Editar alembic.ini
sqlalchemy.url = postgresql+psycopg://user:password@localhost:5432/fastapi_guide
```

### Configuração do Alembic (alembic/env.py)

```python
import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Adicionar src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.config import settings
from db.session import Base
from db.models import *  # Importar todos os modelos

# Configuração do Alembic
config = context.config

# Configurar logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadados dos modelos
target_metadata = Base.metadata

def get_url():
    return str(settings.DATABASE_URL)

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### Comandos de Migração

```bash
# Criar migração
alembic revision --autogenerate -m "Create initial tables"

# Aplicar migrações
alembic upgrade head

# Ver histórico
alembic history

# Reverter migração
alembic downgrade -1

# Ver SQL que será executado
alembic upgrade head --sql
```

---

## 🔧 Serviços com Repository

### Serviço de Item (services/item_service.py)

```python
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from db.repository.item_repository import ItemRepository
from schemas.item import ItemCreate, ItemUpdate, Item
from core.exceptions import ItemNotFoundError, ItemAlreadyExistsError

class ItemService:
    def __init__(self, repository: ItemRepository):
        self.repository = repository
    
    def get_item(self, item_id: int) -> Item | None:
        """Buscar item por ID"""
        db_item = self.repository.get(item_id)
        return Item.from_orm(db_item) if db_item else None
    
    def get_items(
        self,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
        category_id: int | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        available_only: bool = False
    ) -> tuple[list[Item], int]:
        """Buscar itens com filtros"""
        
        if search:
            db_items, total = self.repository.search_items(search, skip, limit)
        elif min_price is not None and max_price is not None:
            db_items, total = self.repository.get_items_by_price_range(
                min_price, max_price, skip, limit
            )
        elif available_only:
            db_items, total = self.repository.get_available_items(skip, limit)
        else:
            filters = {}
            if category_id:
                filters['category_id'] = category_id
            
            db_items, total = self.repository.get_multi(
                skip=skip, 
                limit=limit, 
                filters=filters
            )
        
        items = [Item.from_orm(item) for item in db_items]
        return items, total
    
    def create_item(self, item_data: ItemCreate) -> Item:
        """Criar novo item"""
        # Verificar se já existe item com mesmo nome
        existing_item = self.repository.get_by_name(item_data.name)
        if existing_item:
            raise ItemAlreadyExistsError(f"Item with name '{item_data.name}' already exists")
        
        db_item = self.repository.create(item_data)
        return Item.from_orm(db_item)
    
    def update_item(self, item_id: int, item_data: ItemUpdate) -> Item | None:
        """Atualizar item existente"""
        db_item = self.repository.get(item_id)
        if not db_item:
            return None
        
        # Verificar se novo nome já existe (se fornecido)
        if item_data.name and item_data.name != db_item.name:
            existing_item = self.repository.get_by_name(item_data.name)
            if existing_item:
                raise ItemAlreadyExistsError(f"Item with name '{item_data.name}' already exists")
        
        updated_item = self.repository.update(db_item, item_data)
        return Item.from_orm(updated_item)
    
    def delete_item(self, item_id: int) -> bool:
        """Deletar item"""
        return self.repository.delete(item_id)
    
    def get_items_by_category(self, category_id: int) -> list[Item]:
        """Buscar itens por categoria"""
        db_items = self.repository.get_by_category(category_id)
        return [Item.from_orm(item) for item in db_items]
```

---

## 🎯 Próximos Passos

Agora que você tem persistência completa, está pronto para:

1. **Step 3:** Implementar autenticação e autorização
2. **Step 4:** Adicionar testes automatizados
3. **Step 5:** Configurar cache e otimizações
4. **Step 6:** Implementar WebSockets

---

## 📝 Exercícios Práticos

### Exercício 1: Modelo Completo
Crie um modelo `Order` com:
- Relacionamento com User e Items
- Status do pedido (pending, confirmed, shipped, delivered)
- Total calculado automaticamente

### Exercício 2: Repository Avançado
Implemente métodos no ItemRepository para:
- Buscar itens mais vendidos
- Buscar itens com estoque baixo
- Relatório de itens por categoria

### Exercício 3: Migração Complexa
Crie uma migração que:
- Adiciona campo `slug` na tabela items
- Popula o slug baseado no nome
- Cria índice único no slug

---

**Anterior:** [Step 1: Primeira API](step_1.md) | **Próximo:** [Step 3: Autenticação](step_3.md)
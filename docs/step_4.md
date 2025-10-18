# Testes Automatizados

Implementar uma suíte completa de testes automatizados com pytest, incluindo testes unitários, de integração e end-to-end.

## 🎯 O que você vai aprender

- Conceitos fundamentais de testes automatizados
- Configurar pytest com FastAPI
- Testes unitários de serviços e repositories
- Testes de integração com banco de dados
- Testes de endpoints (API testing)
- Mocking e fixtures
- Coverage e relatórios
- Testes de autenticação
- TDD (Test-Driven Development) e BDD (Behavior-Driven Development)
- Estratégias de teste e boas práticas

---

## 📖 Conceitos Fundamentais de Testes

### Por que Testar?

Os testes automatizados são essenciais para:

1. **Confiança**: Garantir que o código funciona como esperado
2. **Documentação**: Os testes servem como documentação viva do comportamento
3. **Design**: Forçam você a pensar no design da API antes da implementação
4. **Refatoração**: Permitem mudanças seguras no código
5. **Qualidade**: Detectam bugs antes que cheguem à produção

### Pirâmide de Testes

```
    /\
   /  \
  / E2E \     ← Poucos testes, mais lentos, mais caros
 /______\
/        \
| Integration |  ← Testes moderados, velocidade média
|____________|
|            |
|    Unit     |  ← Muitos testes, rápidos, baratos
|____________|
```

#### 1. Testes Unitários (Base da Pirâmide)
- **O que são**: Testam unidades isoladas de código (funções, métodos, classes)
- **Características**: Rápidos, isolados, determinísticos
- **Exemplo**:

```python
def calculate_discount(price: float, discount_percent: float) -> float:
    """Calcula o preço com desconto."""
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Discount must be between 0 and 100")
    return price * (1 - discount_percent / 100)

# Teste unitário
def test_calculate_discount():
    # Arrange
    price = 100.0
    discount = 10.0
    
    # Act
    result = calculate_discount(price, discount)
    
    # Assert
    assert result == 90.0

def test_calculate_discount_invalid_percentage():
    with pytest.raises(ValueError, match="Discount must be between 0 and 100"):
        calculate_discount(100.0, 150.0)
```

#### 2. Testes de Integração (Meio da Pirâmide)
- **O que são**: Testam a interação entre componentes
- **Tipos**:
  - **Integração com Banco de Dados**
  - **Integração entre Serviços**
  - **Integração com APIs Externas**

```python
# Teste de integração com banco de dados
def test_user_repository_integration(db_session):
    # Arrange
    user_repo = UserRepository(db_session)
    user_data = {
        "email": "test@example.com",
        "full_name": "Test User",
        "hashed_password": "hashed_password"
    }
    
    # Act
    created_user = user_repo.create(user_data)
    found_user = user_repo.get_by_email("test@example.com")
    
    # Assert
    assert created_user.id is not None
    assert found_user.email == "test@example.com"
```

#### 3. Testes End-to-End (Topo da Pirâmide)
- **O que são**: Testam o fluxo completo da aplicação
- **Características**: Mais lentos, mais complexos, mais próximos do usuário real

```python
def test_user_registration_flow(client):
    # Arrange
    user_data = {
        "email": "newuser@example.com",
        "password": "securepassword123",
        "full_name": "New User"
    }
    
    # Act - Registrar usuário
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 201
    
    # Act - Fazer login
    login_data = {
        "username": "newuser@example.com",
        "password": "securepassword123"
    }
    login_response = client.post("/auth/login", data=login_data)
    assert login_response.status_code == 200
    
    # Act - Acessar perfil
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    profile_response = client.get("/users/me", headers=headers)
    
    # Assert
    assert profile_response.status_code == 200
    assert profile_response.json()["email"] == "newuser@example.com"
```

### Testes de API com curl

Para testes manuais rápidos:

```bash
# Registrar usuário
curl -X POST "http://localhost:8000/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "password": "password123",
       "full_name": "Test User"
     }'

# Login
curl -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=test@example.com&password=password123"

# Acessar endpoint protegido
curl -X GET "http://localhost:8000/users/me" \
     -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### TDD (Test-Driven Development)

O TDD segue o ciclo **Red-Green-Refactor**:

1. **🔴 Red**: Escreva um teste que falha
2. **🟢 Green**: Escreva o código mínimo para passar
3. **🔵 Refactor**: Melhore o código mantendo os testes passando

```python
# 1. RED - Teste que falha (função não existe ainda)
def test_user_can_be_created():
    user_service = UserService()
    user_data = {"email": "test@example.com", "name": "Test"}
    
    user = user_service.create_user(user_data)
    
    assert user.email == "test@example.com"
    assert user.id is not None

# 2. GREEN - Implementação mínima
class UserService:
    def create_user(self, user_data):
        user = User(
            id=1,
            email=user_data["email"],
            name=user_data["name"]
        )
        return user

# 3. REFACTOR - Melhorar a implementação
class UserService:
    def __init__(self, user_repository):
        self.user_repository = user_repository
    
    def create_user(self, user_data):
        # Validações, regras de negócio, etc.
        return self.user_repository.create(user_data)
```

### BDD (Behavior-Driven Development)

O BDD usa a estrutura **Given-When-Then**:

```python
def test_user_login_with_valid_credentials():
    """
    Given: Um usuário registrado no sistema
    When: O usuário tenta fazer login com credenciais válidas
    Then: O login deve ser bem-sucedido e retornar um token
    """
    # Given - Preparar o cenário
    user_repo = Mock()
    auth_service = AuthService(user_repo)
    
    user = User(email="test@example.com", hashed_password="hashed_pass")
    user_repo.get_by_email.return_value = user
    
    # When - Executar a ação
    with patch('core.security.verify_password', return_value=True):
        result = auth_service.authenticate_user("test@example.com", "password")
    
    # Then - Verificar o resultado
    assert result == user
```

### Mocking e Test Doubles

#### Tipos de Test Doubles:

1. **Dummy**: Objetos que são passados mas nunca usados
2. **Fake**: Implementações funcionais simplificadas
3. **Stub**: Retornam respostas pré-programadas
4. **Spy**: Gravam informações sobre como foram chamados
5. **Mock**: Objetos pré-programados com expectativas

```python
from unittest.mock import Mock, patch

# Mock simples
def test_email_service_with_mock():
    # Arrange
    email_service = Mock()
    user_service = UserService(email_service=email_service)
    
    # Act
    user_service.send_welcome_email("test@example.com")
    
    # Assert
    email_service.send_email.assert_called_once_with(
        to="test@example.com",
        subject="Welcome!"
    )

# Patch para substituir dependências
@patch('services.user_service.EmailService')
def test_user_creation_sends_email(mock_email_service):
    # Arrange
    user_service = UserService()
    
    # Act
    user_service.create_user({"email": "test@example.com"})
    
    # Assert
    mock_email_service.return_value.send_welcome_email.assert_called_once()
```

### Fixtures

Fixtures preparam o ambiente de teste:

```python
import pytest

# Fixture de função (padrão)
@pytest.fixture
def user_data():
    return {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "password123"
    }

# Fixture de classe
@pytest.fixture(scope="class")
def database_connection():
    conn = create_connection()
    yield conn
    conn.close()

# Fixture de módulo
@pytest.fixture(scope="module")
def expensive_resource():
    resource = create_expensive_resource()
    yield resource
    cleanup_resource(resource)

# Fixture de sessão
@pytest.fixture(scope="session")
def test_config():
    return load_test_configuration()

# Usando fixtures
def test_user_creation(user_data, db_session):
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    
    assert user.id is not None
```

### Code Coverage

Coverage mede quanto do seu código é executado pelos testes:

```bash
# Executar testes com coverage
pytest --cov=src --cov-report=html --cov-report=term-missing

# Relatório detalhado
pytest --cov=src --cov-report=html --cov-fail-under=80
```

**Tipos de Coverage:**
- **Line Coverage**: Linhas executadas
- **Branch Coverage**: Caminhos de decisão executados
- **Function Coverage**: Funções chamadas

**Interpretação:**
- **80-90%**: Boa cobertura
- **90-95%**: Excelente cobertura
- **95%+**: Cobertura excepcional (pode ser excessiva)

### Estratégias de Teste

#### 1. Arrange-Act-Assert (AAA)
```python
def test_user_creation():
    # Arrange - Preparar dados e dependências
    user_data = {"email": "test@example.com", "name": "Test"}
    user_service = UserService()
    
    # Act - Executar a ação sendo testada
    user = user_service.create_user(user_data)
    
    # Assert - Verificar o resultado
    assert user.email == "test@example.com"
    assert user.id is not None
```

#### 2. Testes Parametrizados
```python
@pytest.mark.parametrize("email,expected_valid", [
    ("valid@example.com", True),
    ("invalid-email", False),
    ("@example.com", False),
    ("test@", False),
])
def test_email_validation(email, expected_valid):
    result = is_valid_email(email)
    assert result == expected_valid
```

---

## 🧪 Configuração do Ambiente de Testes

### Dependências de Teste

```bash
pip install pytest pytest-asyncio pytest-cov httpx faker factory-boy
```

### Configuração do pytest (pytest.ini)

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --strict-config
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
    auth: Authentication tests
```

### Configuração de Teste (tests/conftest.py)

```python
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from core.config import settings
from db.session import Base, get_db
from db.models import *  # Importar todos os modelos

# Database de teste em memória
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Criar todas as tabelas
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Limpar todas as tabelas após cada teste
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database session override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Limpar overrides
    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers(client, test_user):
    """Create authentication headers for test user."""
    login_data = {
        "username": test_user.username,
        "password": "testpassword123"
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    token_data = response.json()
    access_token = token_data["token"]["access_token"]
    
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def admin_headers(client, admin_user):
    """Create authentication headers for admin user."""
    login_data = {
        "username": admin_user.username,
        "password": "adminpassword123"
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    token_data = response.json()
    access_token = token_data["token"]["access_token"]
    
    return {"Authorization": f"Bearer {access_token}"}
```

---

## 🏭 Factories para Dados de Teste

### Factory Base (tests/factories/base.py)

```python
import factory
from factory.alchemy import SQLAlchemyModelFactory
from faker import Faker

fake = Faker('pt_BR')

class BaseFactory(SQLAlchemyModelFactory):
    """Factory base com configurações comuns"""
    
    class Meta:
        abstract = True
        sqlalchemy_session_persistence = "commit"
```

### Factory de Usuário (tests/factories/user_factory.py)

```python
import factory
from factory.alchemy import SQLAlchemyModelFactory
from tests.factories.base import BaseFactory, fake
from db.models.user import User
from db.models.role import Role
from core.security import get_password_hash

class RoleFactory(BaseFactory):
    class Meta:
        model = Role
    
    name = factory.Sequence(lambda n: f"role_{n}")
    description = factory.LazyAttribute(lambda obj: f"Description for {obj.name}")
    is_active = True

class UserFactory(BaseFactory):
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    full_name = factory.LazyFunction(fake.name)
    hashed_password = factory.LazyFunction(lambda: get_password_hash("testpassword123"))
    is_active = True
    is_superuser = False
    role = factory.SubFactory(RoleFactory)

class AdminUserFactory(UserFactory):
    username = factory.Sequence(lambda n: f"admin_{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    is_superuser = True
    hashed_password = factory.LazyFunction(lambda: get_password_hash("adminpassword123"))

class InactiveUserFactory(UserFactory):
    username = factory.Sequence(lambda n: f"inactive_{n}")
    is_active = False
```

### Factory de Item (tests/factories/item_factory.py)

```python
import factory
from decimal import Decimal
from tests.factories.base import BaseFactory, fake
from db.models.item import Item
from db.models.category import Category

class CategoryFactory(BaseFactory):
    class Meta:
        model = Category
    
    name = factory.Sequence(lambda n: f"category_{n}")
    description = factory.LazyFunction(fake.text)
    is_active = True

class ItemFactory(BaseFactory):
    class Meta:
        model = Item
    
    name = factory.LazyFunction(fake.word)
    description = factory.LazyFunction(fake.text)
    price = factory.LazyFunction(lambda: round(fake.pyfloat(min_value=1, max_value=1000), 2))
    discount_price = None
    is_available = True
    stock_quantity = factory.LazyFunction(lambda: fake.pyint(min_value=0, max_value=100))
    category = factory.SubFactory(CategoryFactory)

class ItemWithDiscountFactory(ItemFactory):
    discount_price = factory.LazyAttribute(
        lambda obj: round(obj.price * 0.8, 2)  # 20% de desconto
    )

class OutOfStockItemFactory(ItemFactory):
    stock_quantity = 0
    is_available = False
```

---

## 🔧 Fixtures de Teste

### Fixtures de Usuário (tests/fixtures/user_fixtures.py)

```python
import pytest
from tests.factories.user_factory import UserFactory, AdminUserFactory, RoleFactory

@pytest.fixture
def test_role(db_session):
    """Create a test role."""
    role = RoleFactory(name="user", description="Regular user role")
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role

@pytest.fixture
def admin_role(db_session):
    """Create an admin role."""
    role = RoleFactory(name="admin", description="Administrator role")
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role

@pytest.fixture
def test_user(db_session, test_role):
    """Create a test user."""
    user = UserFactory(role=test_role)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def admin_user(db_session, admin_role):
    """Create an admin user."""
    user = AdminUserFactory(role=admin_role)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def multiple_users(db_session, test_role):
    """Create multiple test users."""
    users = []
    for i in range(5):
        user = UserFactory(role=test_role)
        db_session.add(user)
        users.append(user)
    
    db_session.commit()
    for user in users:
        db_session.refresh(user)
    
    return users
```

### Fixtures de Item (tests/fixtures/item_fixtures.py)

```python
import pytest
from tests.factories.item_factory import ItemFactory, CategoryFactory

@pytest.fixture
def test_category(db_session):
    """Create a test category."""
    category = CategoryFactory()
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category

@pytest.fixture
def test_item(db_session, test_category):
    """Create a test item."""
    item = ItemFactory(category=test_category)
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item

@pytest.fixture
def multiple_items(db_session, test_category):
    """Create multiple test items."""
    items = []
    for i in range(10):
        item = ItemFactory(category=test_category)
        db_session.add(item)
        items.append(item)
    
    db_session.commit()
    for item in items:
        db_session.refresh(item)
    
    return items
```

---

## 🧪 Testes Unitários

### Testes de Modelos (tests/unit/test_models.py)

```python
import pytest
from datetime import datetime
from db.models.user import User
from db.models.item import Item
from db.models.category import Category
from tests.factories.user_factory import UserFactory
from tests.factories.item_factory import ItemFactory, CategoryFactory

class TestUserModel:
    def test_user_creation(self, db_session):
        """Test user model creation."""
        user = UserFactory()
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.is_active is True
        assert "@" in user.email
    
    def test_user_repr(self, db_session):
        """Test user string representation."""
        user = UserFactory(username="testuser", email="test@example.com")
        db_session.add(user)
        db_session.commit()
        
        expected = f"<User(id={user.id}, username='testuser', email='test@example.com')>"
        assert repr(user) == expected
    
    def test_user_has_permission(self, db_session):
        """Test user permission checking."""
        user = UserFactory(is_superuser=True)
        db_session.add(user)
        db_session.commit()
        
        # Superuser tem todas as permissões
        assert user.has_permission("users", "read") is True
        assert user.has_permission("items", "create") is True
    
    def test_user_get_permissions(self, db_session):
        """Test getting user permissions."""
        user = UserFactory(is_superuser=True)
        db_session.add(user)
        db_session.commit()
        
        permissions = user.get_permissions()
        assert "*:*" in permissions

class TestItemModel:
    def test_item_creation(self, db_session):
        """Test item model creation."""
        category = CategoryFactory()
        item = ItemFactory(category=category)
        
        db_session.add(category)
        db_session.add(item)
        db_session.commit()
        
        assert item.id is not None
        assert item.name is not None
        assert item.price > 0
        assert item.category_id == category.id
    
    def test_effective_price_without_discount(self, db_session):
        """Test effective price calculation without discount."""
        item = ItemFactory(price=100.0, discount_price=None)
        db_session.add(item)
        db_session.commit()
        
        assert item.effective_price == 100.0
    
    def test_effective_price_with_discount(self, db_session):
        """Test effective price calculation with discount."""
        item = ItemFactory(price=100.0, discount_price=80.0)
        db_session.add(item)
        db_session.commit()
        
        assert item.effective_price == 80.0
    
    def test_is_in_stock(self, db_session):
        """Test stock verification."""
        item_in_stock = ItemFactory(stock_quantity=10)
        item_out_of_stock = ItemFactory(stock_quantity=0)
        
        db_session.add(item_in_stock)
        db_session.add(item_out_of_stock)
        db_session.commit()
        
        assert item_in_stock.is_in_stock is True
        assert item_out_of_stock.is_in_stock is False
```

### Testes de Serviços (tests/unit/test_services.py)

```python
import pytest
from unittest.mock import Mock, patch
from services.item_service import ItemService
from services.auth_service import AuthService
from schemas.item import ItemCreate, ItemUpdate
from schemas.user import UserCreate
from core.exceptions import ItemNotFoundError, ItemAlreadyExistsError

class TestItemService:
    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository."""
        return Mock()
    
    @pytest.fixture
    def item_service(self, mock_repository):
        """Create item service with mock repository."""
        return ItemService(mock_repository)
    
    def test_get_item_success(self, item_service, mock_repository):
        """Test successful item retrieval."""
        # Arrange
        mock_item = Mock()
        mock_item.id = 1
        mock_item.name = "Test Item"
        mock_repository.get.return_value = mock_item
        
        # Act
        result = item_service.get_item(1)
        
        # Assert
        mock_repository.get.assert_called_once_with(1)
        assert result is not None
    
    def test_get_item_not_found(self, item_service, mock_repository):
        """Test item not found."""
        # Arrange
        mock_repository.get.return_value = None
        
        # Act
        result = item_service.get_item(999)
        
        # Assert
        mock_repository.get.assert_called_once_with(999)
        assert result is None
    
    def test_create_item_success(self, item_service, mock_repository):
        """Test successful item creation."""
        # Arrange
        item_data = ItemCreate(
            name="New Item",
            description="Test description",
            price=99.99,
            category_id=1
        )
        
        mock_repository.get_by_name.return_value = None
        mock_created_item = Mock()
        mock_repository.create.return_value = mock_created_item
        
        # Act
        result = item_service.create_item(item_data)
        
        # Assert
        mock_repository.get_by_name.assert_called_once_with("New Item")
        mock_repository.create.assert_called_once_with(item_data)
        assert result is not None
    
    def test_create_item_already_exists(self, item_service, mock_repository):
        """Test creating item that already exists."""
        # Arrange
        item_data = ItemCreate(
            name="Existing Item",
            description="Test description",
            price=99.99,
            category_id=1
        )
        
        mock_existing_item = Mock()
        mock_repository.get_by_name.return_value = mock_existing_item
        
        # Act & Assert
        with pytest.raises(ItemAlreadyExistsError):
            item_service.create_item(item_data)
        
        mock_repository.get_by_name.assert_called_once_with("Existing Item")
        mock_repository.create.assert_not_called()

class TestAuthService:
    @pytest.fixture
    def mock_user_repository(self):
        return Mock()
    
    @pytest.fixture
    def auth_service(self, mock_user_repository):
        return AuthService(mock_user_repository)
    
    @patch('services.auth_service.verify_password')
    def test_authenticate_user_success(self, mock_verify_password, auth_service, mock_user_repository):
        """Test successful user authentication."""
        # Arrange
        mock_user = Mock()
        mock_user.hashed_password = "hashed_password"
        mock_user_repository.get_by_username.return_value = mock_user
        mock_verify_password.return_value = True
        
        # Act
        result = auth_service.authenticate_user("testuser", "password")
        
        # Assert
        mock_user_repository.get_by_username.assert_called_once_with("testuser")
        mock_verify_password.assert_called_once_with("password", "hashed_password")
        assert result == mock_user
    
    @patch('services.auth_service.verify_password')
    def test_authenticate_user_wrong_password(self, mock_verify_password, auth_service, mock_user_repository):
        """Test authentication with wrong password."""
        # Arrange
        mock_user = Mock()
        mock_user.hashed_password = "hashed_password"
        mock_user_repository.get_by_username.return_value = mock_user
        mock_verify_password.return_value = False
        
        # Act
        result = auth_service.authenticate_user("testuser", "wrong_password")
        
        # Assert
        assert result is None
    
    def test_authenticate_user_not_found(self, auth_service, mock_user_repository):
        """Test authentication with non-existent user."""
        # Arrange
        mock_user_repository.get_by_username.return_value = None
        mock_user_repository.get_by_email.return_value = None
        
        # Act
        result = auth_service.authenticate_user("nonexistent", "password")
        
        # Assert
        assert result is None
```

---

## 🔗 Testes de Integração

### Testes de Repository (tests/integration/test_repositories.py)

```python
import pytest
from db.repository.item_repository import ItemRepository
from db.repository.user_repository import UserRepository
from tests.factories.item_factory import ItemFactory, CategoryFactory
from tests.factories.user_factory import UserFactory, RoleFactory
from schemas.item import ItemCreate, ItemUpdate

class TestItemRepository:
    @pytest.fixture
    def item_repository(self, db_session):
        return ItemRepository(db_session)
    
    def test_create_item(self, item_repository, db_session):
        """Test creating an item through repository."""
        category = CategoryFactory()
        db_session.add(category)
        db_session.commit()
        
        item_data = ItemCreate(
            name="Test Item",
            description="Test description",
            price=99.99,
            category_id=category.id
        )
        
        created_item = item_repository.create(item_data)
        
        assert created_item.id is not None
        assert created_item.name == "Test Item"
        assert created_item.price == 99.99
        assert created_item.category_id == category.id
    
    def test_get_item_by_name(self, item_repository, db_session):
        """Test getting item by name."""
        category = CategoryFactory()
        item = ItemFactory(name="Unique Item", category=category)
        
        db_session.add(category)
        db_session.add(item)
        db_session.commit()
        
        found_item = item_repository.get_by_name("Unique Item")
        
        assert found_item is not None
        assert found_item.name == "Unique Item"
        assert found_item.id == item.id
    
    def test_get_items_by_category(self, item_repository, db_session):
        """Test getting items by category."""
        category1 = CategoryFactory()
        category2 = CategoryFactory()
        
        item1 = ItemFactory(category=category1)
        item2 = ItemFactory(category=category1)
        item3 = ItemFactory(category=category2)
        
        db_session.add_all([category1, category2, item1, item2, item3])
        db_session.commit()
        
        items = item_repository.get_by_category(category1.id)
        
        assert len(items) == 2
        assert all(item.category_id == category1.id for item in items)
    
    def test_search_items(self, item_repository, db_session):
        """Test searching items by term."""
        category = CategoryFactory()
        item1 = ItemFactory(name="Python Book", category=category)
        item2 = ItemFactory(name="Java Guide", category=category)
        item3 = ItemFactory(name="FastAPI Tutorial", description="Learn Python FastAPI", category=category)
        
        db_session.add_all([category, item1, item2, item3])
        db_session.commit()
        
        items, total = item_repository.search_items("Python")
        
        assert total == 2  # item1 e item3
        item_names = [item.name for item in items]
        assert "Python Book" in item_names
        assert "FastAPI Tutorial" in item_names
    
    def test_get_available_items(self, item_repository, db_session):
        """Test getting only available items."""
        category = CategoryFactory()
        available_item = ItemFactory(is_available=True, category=category)
        unavailable_item = ItemFactory(is_available=False, category=category)
        
        db_session.add_all([category, available_item, unavailable_item])
        db_session.commit()
        
        items, total = item_repository.get_available_items()
        
        assert total == 1
        assert items[0].id == available_item.id
        assert items[0].is_available is True

class TestUserRepository:
    @pytest.fixture
    def user_repository(self, db_session):
        return UserRepository(db_session)
    
    def test_get_by_username(self, user_repository, db_session):
        """Test getting user by username."""
        role = RoleFactory()
        user = UserFactory(username="testuser", role=role)
        
        db_session.add(role)
        db_session.add(user)
        db_session.commit()
        
        found_user = user_repository.get_by_username("testuser")
        
        assert found_user is not None
        assert found_user.username == "testuser"
        assert found_user.id == user.id
    
    def test_get_by_email(self, user_repository, db_session):
        """Test getting user by email."""
        role = RoleFactory()
        user = UserFactory(email="test@example.com", role=role)
        
        db_session.add(role)
        db_session.add(user)
        db_session.commit()
        
        found_user = user_repository.get_by_email("test@example.com")
        
        assert found_user is not None
        assert found_user.email == "test@example.com"
        assert found_user.id == user.id
```

---

## 🌐 Testes de API (End-to-End)

### Testes de Autenticação (tests/e2e/test_auth_api.py)

```python
import pytest
from fastapi.testclient import TestClient

class TestAuthAPI:
    def test_register_user_success(self, client):
        """Test successful user registration."""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "SecurePass123",
            "full_name": "New User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "hashed_password" not in data
    
    def test_register_user_duplicate_username(self, client, test_user):
        """Test registration with duplicate username."""
        user_data = {
            "username": test_user.username,
            "email": "different@example.com",
            "password": "SecurePass123"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    def test_login_success(self, client, test_user):
        """Test successful login."""
        login_data = {
            "username": test_user.username,
            "password": "testpassword123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["token"]["token_type"] == "bearer"
        assert "access_token" in data["token"]
        assert "refresh_token" in data["token"]
    
    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password."""
        login_data = {
            "username": test_user.username,
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        login_data = {
            "username": "nonexistent",
            "password": "password123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
    
    def test_get_current_user(self, client, auth_headers):
        """Test getting current user info."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "email" in data
        assert "permissions" in data
    
    def test_get_current_user_without_token(self, client):
        """Test getting current user without authentication."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
    
    def test_refresh_token(self, client, test_user):
        """Test token refresh."""
        # Primeiro fazer login
        login_data = {
            "username": test_user.username,
            "password": "testpassword123"
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        refresh_token = login_response.json()["token"]["refresh_token"]
        
        # Usar refresh token
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_change_password(self, client, auth_headers):
        """Test password change."""
        password_data = {
            "current_password": "testpassword123",
            "new_password": "NewSecurePass123",
            "confirm_password": "NewSecurePass123"
        }
        
        response = client.post(
            "/api/v1/auth/change-password", 
            json=password_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert "Password changed successfully" in response.json()["message"]
```

### Testes de Items API (tests/e2e/test_items_api.py)

```python
import pytest

class TestItemsAPI:
    def test_get_items_without_auth(self, client):
        """Test getting items without authentication."""
        response = client.get("/api/v1/items/")
        assert response.status_code == 401
    
    def test_get_items_with_auth(self, client, auth_headers, multiple_items):
        """Test getting items with authentication."""
        response = client.get("/api/v1/items/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) > 0
    
    def test_get_items_with_pagination(self, client, auth_headers, multiple_items):
        """Test items pagination."""
        response = client.get(
            "/api/v1/items/?skip=0&limit=5", 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 5
        assert data["skip"] == 0
        assert data["limit"] == 5
    
    def test_get_item_by_id(self, client, auth_headers, test_item):
        """Test getting specific item by ID."""
        response = client.get(
            f"/api/v1/items/{test_item.id}", 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_item.id
        assert data["name"] == test_item.name
    
    def test_get_nonexistent_item(self, client, auth_headers):
        """Test getting non-existent item."""
        response = client.get("/api/v1/items/999", headers=auth_headers)
        assert response.status_code == 404
    
    def test_create_item_without_permission(self, client, auth_headers):
        """Test creating item without proper permissions."""
        item_data = {
            "name": "New Item",
            "description": "Test item",
            "price": 99.99,
            "category_id": 1
        }
        
        response = client.post(
            "/api/v1/items/", 
            json=item_data,
            headers=auth_headers
        )
        
        # Assumindo que usuário normal não tem permissão de criar
        assert response.status_code == 403
    
    def test_create_item_with_admin(self, client, admin_headers, test_category):
        """Test creating item with admin permissions."""
        item_data = {
            "name": "Admin Created Item",
            "description": "Item created by admin",
            "price": 149.99,
            "category_id": test_category.id
        }
        
        response = client.post(
            "/api/v1/items/", 
            json=item_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Admin Created Item"
        assert data["price"] == 149.99
    
    def test_update_item_with_admin(self, client, admin_headers, test_item):
        """Test updating item with admin permissions."""
        update_data = {
            "name": "Updated Item Name",
            "price": 199.99
        }
        
        response = client.put(
            f"/api/v1/items/{test_item.id}",
            json=update_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Item Name"
        assert data["price"] == 199.99
    
    def test_delete_item_with_admin(self, client, admin_headers, test_item):
        """Test deleting item with admin permissions."""
        response = client.delete(
            f"/api/v1/items/{test_item.id}",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verificar se item foi realmente deletado
        get_response = client.get(
            f"/api/v1/items/{test_item.id}",
            headers=admin_headers
        )
        assert get_response.status_code == 404
    
    def test_search_items(self, client, auth_headers, multiple_items):
        """Test searching items."""
        response = client.get(
            "/api/v1/items/?search=test",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        # Verificar se todos os itens retornados contêm o termo de busca
        for item in data["items"]:
            assert ("test" in item["name"].lower() or 
                   "test" in item["description"].lower())
```

---

## 📊 Testes de Performance

### Testes de Carga (tests/performance/test_load.py)

```python
import pytest
import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor

class TestPerformance:
    @pytest.mark.slow
    def test_concurrent_requests(self, client, auth_headers):
        """Test API performance under concurrent load."""
        def make_request():
            response = client.get("/api/v1/items/", headers=auth_headers)
            return response.status_code
        
        # Executar 50 requests concorrentes
        with ThreadPoolExecutor(max_workers=10) as executor:
            start_time = time.time()
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [future.result() for future in futures]
            end_time = time.time()
        
        # Verificar se todas as requests foram bem-sucedidas
        assert all(status == 200 for status in results)
        
        # Verificar se o tempo total foi razoável (menos de 5 segundos)
        total_time = end_time - start_time
        assert total_time < 5.0
        
        # Calcular requests por segundo
        rps = len(results) / total_time
        print(f"Requests per second: {rps:.2f}")
        assert rps > 10  # Pelo menos 10 RPS
    
    @pytest.mark.slow
    def test_database_query_performance(self, db_session, multiple_items):
        """Test database query performance."""
        from db.repository.item_repository import ItemRepository
        
        repo = ItemRepository(db_session)
        
        # Medir tempo de query
        start_time = time.time()
        items, total = repo.get_multi(limit=100)
        end_time = time.time()
        
        query_time = end_time - start_time
        print(f"Query time: {query_time:.4f} seconds")
        
        # Query deve ser rápida (menos de 100ms)
        assert query_time < 0.1
        assert len(items) > 0
```

---

## 🎯 Comandos de Teste

### Executar Todos os Testes

```bash
# Executar todos os testes
pytest

# Executar com coverage
pytest --cov=src --cov-report=html

# Executar apenas testes unitários
pytest -m unit

# Executar apenas testes de integração
pytest -m integration

# Executar apenas testes e2e
pytest -m e2e

# Executar testes em paralelo
pytest -n auto

# Executar testes com output detalhado
pytest -v -s

# Executar testes específicos
pytest tests/unit/test_models.py::TestUserModel::test_user_creation
```

### Scripts de Teste (scripts/test.py)

```python
#!/usr/bin/env python3
"""
Script para executar diferentes tipos de teste
"""
import subprocess
import sys
import argparse

def run_command(command):
    """Execute command and return result."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    return result.returncode == 0

def main():
    parser = argparse.ArgumentParser(description="Run tests")
    parser.add_argument("--type", choices=["unit", "integration", "e2e", "all"], 
                       default="all", help="Type of tests to run")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    
    args = parser.parse_args()
    
    # Base command
    cmd = "pytest"
    
    # Add test type marker
    if args.type != "all":
        cmd += f" -m {args.type}"
    
    # Add coverage
    if args.coverage:
        cmd += " --cov=src --cov-report=html --cov-report=term-missing"
    
    # Add parallel execution
    if args.parallel:
        cmd += " -n auto"
    
    # Add verbose output
    cmd += " -v"
    
    # Run tests
    success = run_command(cmd)
    
    if not success:
        print("Tests failed!")
        sys.exit(1)
    
    print("All tests passed!")

if __name__ == "__main__":
    main()
```

---

## 🎯 Próximos Passos

Com testes implementados, você pode:

1. **Step 5:** Implementar cache e otimizações
2. **Step 6:** Adicionar WebSockets
3. **Step 7:** Deploy e monitoramento

---

## 📝 Exercícios Práticos

### Exercício 1: Testes de Validação
Crie testes para validar:
- Schemas Pydantic
- Validações de senha
- Validações de email

### Exercício 2: Testes de Erro
Implemente testes para:
- Tratamento de exceções
- Códigos de erro HTTP
- Mensagens de erro personalizadas

### Exercício 3: Testes de Segurança
Crie testes para:
- Tentativas de acesso não autorizado
- Injeção SQL
- Rate limiting

---

## Implementação Prática de Testes

Agora que configuramos o ambiente de testes, vamos implementar testes práticos para nossos modelos, serviços e endpoints.

### Testes de Modelos

#### Testando o Modelo User

```python
# tests/unit/test_models.py
import pytest
from datetime import date
from sqlalchemy.exc import IntegrityError
from app.models.user import User

class TestUserModel:
    def test_create_user(self, db_session):
        """Testa a criação de um usuário"""
        user = User(
            name="João Silva",
            email="joao@example.com",
            password="hashed_password",
            birth_date=date(1990, 1, 1)
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.name == "João Silva"
        assert user.email == "joao@example.com"
        assert user.is_active is True  # valor padrão
    
    def test_email_unique_constraint(self, db_session):
        """Testa que emails devem ser únicos"""
        user1 = User(
            name="João",
            email="joao@example.com",
            password="password1"
        )
        user2 = User(
            name="Maria",
            email="joao@example.com",  # mesmo email
            password="password2"
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_user_str_representation(self, db_session):
        """Testa a representação string do usuário"""
        user = User(
            name="João Silva",
            email="joao@example.com",
            password="password"
        )
        assert str(user) == "João Silva"
    
    def test_user_is_active_default(self, db_session):
        """Testa que usuários são ativos por padrão"""
        user = User(
            name="João",
            email="joao@example.com",
            password="password"
        )
        assert user.is_active is True
    
    def test_calculate_age(self, db_session):
        """Testa o cálculo da idade"""
        user = User(
            name="João",
            email="joao@example.com",
            password="password",
            birth_date=date(1990, 1, 1)
        )
        # Assumindo que temos um método calculate_age
        # age = user.calculate_age()
        # assert age >= 33  # em 2023
```

#### Testando o Modelo Item

```python
class TestItemModel:
    def test_create_item(self, db_session, user_factory):
        """Testa a criação de um item"""
        user = user_factory()
        item = Item(
            name="Produto Teste",
            description="Descrição do produto",
            price=99.99,
            user_id=user.id
        )
        db_session.add(item)
        db_session.commit()
        
        assert item.id is not None
        assert item.name == "Produto Teste"
        assert item.price == 99.99
        assert item.user_id == user.id
    
    def test_item_price_positive(self, db_session, user_factory):
        """Testa que o preço deve ser positivo"""
        user = user_factory()
        item = Item(
            name="Produto",
            price=-10.0,  # preço negativo
            user_id=user.id
        )
        
        # Se temos validação no modelo
        with pytest.raises(ValueError):
            db_session.add(item)
            db_session.commit()
    
    def test_calculate_discount(self, db_session, user_factory):
        """Testa o cálculo de desconto"""
        user = user_factory()
        item = Item(
            name="Produto",
            price=100.0,
            user_id=user.id
        )
        
        # Assumindo que temos um método calculate_discount
        # discounted_price = item.calculate_discount(0.1)  # 10%
        # assert discounted_price == 90.0
    
    @pytest.mark.parametrize("price,discount,expected", [
        (100.0, 0.1, 90.0),
        (50.0, 0.2, 40.0),
        (200.0, 0.15, 170.0),
    ])
    def test_discount_calculation_parametrized(self, db_session, user_factory, price, discount, expected):
        """Testa cálculo de desconto com múltiplos valores"""
        user = user_factory()
        item = Item(name="Produto", price=price, user_id=user.id)
        
        # discounted_price = item.calculate_discount(discount)
        # assert discounted_price == expected
```

### Testes de Schemas (Pydantic)

```python
# tests/unit/test_schemas.py
import pytest
from pydantic import ValidationError
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.schemas.item import ItemCreate, ItemUpdate

class TestUserSchemas:
    def test_user_create_valid_data(self):
        """Testa criação de schema com dados válidos"""
        user_data = {
            "name": "João Silva",
            "email": "joao@example.com",
            "password": "senha123"
        }
        user = UserCreate(**user_data)
        
        assert user.name == "João Silva"
        assert user.email == "joao@example.com"
        assert user.password == "senha123"
    
    def test_user_create_invalid_email(self):
        """Testa validação de email inválido"""
        user_data = {
            "name": "João",
            "email": "email_invalido",  # email inválido
            "password": "senha123"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        
        assert "email" in str(exc_info.value)
    
    def test_user_create_weak_password(self):
        """Testa validação de senha fraca"""
        user_data = {
            "name": "João",
            "email": "joao@example.com",
            "password": "123"  # senha muito curta
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        
        assert "password" in str(exc_info.value)
    
    def test_user_update_partial(self):
        """Testa atualização parcial de usuário"""
        update_data = {"name": "Novo Nome"}
        user_update = UserUpdate(**update_data)
        
        assert user_update.name == "Novo Nome"
        assert user_update.email is None
        assert user_update.password is None
    
    def test_user_response_excludes_password(self):
        """Testa que a resposta não inclui senha"""
        user_data = {
            "id": 1,
            "name": "João",
            "email": "joao@example.com",
            "is_active": True
        }
        user_response = UserResponse(**user_data)
        
        # Verifica que não há campo password
        assert not hasattr(user_response, 'password')

class TestItemSchemas:
    def test_item_create_valid(self):
        """Testa criação de item válido"""
        item_data = {
            "name": "Produto Teste",
            "description": "Descrição",
            "price": 99.99
        }
        item = ItemCreate(**item_data)
        
        assert item.name == "Produto Teste"
        assert item.price == 99.99
    
    def test_item_create_invalid_price(self):
        """Testa validação de preço inválido"""
        item_data = {
            "name": "Produto",
            "price": -10.0  # preço negativo
        }
        
        with pytest.raises(ValidationError):
            ItemCreate(**item_data)
    
    def test_item_create_empty_name(self):
        """Testa validação de nome vazio"""
        item_data = {
            "name": "",  # nome vazio
            "price": 10.0
        }
        
        with pytest.raises(ValidationError):
            ItemCreate(**item_data)
```

### Testes de Serviços (Business Logic)

```python
# tests/unit/test_services.py
import pytest
from unittest.mock import Mock, patch
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.services.email_service import EmailService

class TestUserService:
    def test_create_user_success(self):
        """Testa criação bem-sucedida de usuário"""
        # Arrange
        mock_repo = Mock()
        mock_repo.get_by_email.return_value = None  # email não existe
        mock_repo.create.return_value = Mock(id=1, name="João", email="joao@example.com")
        
        service = UserService(mock_repo)
        user_data = {
            "name": "João",
            "email": "joao@example.com",
            "password": "senha123"
        }
        
        # Act
        result = service.create_user(user_data)
        
        # Assert
        assert result.id == 1
        assert result.name == "João"
        mock_repo.get_by_email.assert_called_once_with("joao@example.com")
        mock_repo.create.assert_called_once()
    
    def test_create_user_email_exists(self):
        """Testa criação de usuário com email existente"""
        # Arrange
        mock_repo = Mock()
        mock_repo.get_by_email.return_value = Mock(id=1)  # email já existe
        
        service = UserService(mock_repo)
        user_data = {
            "name": "João",
            "email": "joao@example.com",
            "password": "senha123"
        }
        
        # Act & Assert
        with pytest.raises(ValueError, match="Email já cadastrado"):
            service.create_user(user_data)
    
    def test_get_user_by_id(self):
        """Testa busca de usuário por ID"""
        # Arrange
        mock_repo = Mock()
        expected_user = Mock(id=1, name="João")
        mock_repo.get_by_id.return_value = expected_user
        
        service = UserService(mock_repo)
        
        # Act
        result = service.get_user_by_id(1)
        
        # Assert
        assert result == expected_user
        mock_repo.get_by_id.assert_called_once_with(1)

class TestAuthService:
    def test_authenticate_user_success(self):
        """Testa autenticação bem-sucedida"""
        # Arrange
        mock_user_service = Mock()
        mock_user = Mock(id=1, email="joao@example.com", password="hashed_password")
        mock_user_service.get_by_email.return_value = mock_user
        
        service = AuthService(mock_user_service)
        
        with patch('app.services.auth_service.verify_password') as mock_verify:
            mock_verify.return_value = True
            
            # Act
            result = service.authenticate_user("joao@example.com", "senha123")
            
            # Assert
            assert result == mock_user
            mock_verify.assert_called_once_with("senha123", "hashed_password")
    
    def test_authenticate_user_invalid_credentials(self):
        """Testa autenticação com credenciais inválidas"""
        # Arrange
        mock_user_service = Mock()
        mock_user_service.get_by_email.return_value = None
        
        service = AuthService(mock_user_service)
        
        # Act
        result = service.authenticate_user("joao@example.com", "senha123")
        
        # Assert
        assert result is None
    
    def test_create_access_token(self):
        """Testa criação de token de acesso"""
        service = AuthService(Mock())
        
        with patch('app.services.auth_service.create_jwt_token') as mock_create_token:
            mock_create_token.return_value = "fake_token"
            
            # Act
            token = service.create_access_token({"sub": "joao@example.com"})
            
            # Assert
            assert token == "fake_token"
            mock_create_token.assert_called_once()

class TestEmailService:
    def test_send_welcome_email_success(self):
        """Testa envio bem-sucedido de email de boas-vindas"""
        # Arrange
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            service = EmailService()
            
            # Act
            result = service.send_welcome_email("joao@example.com", "João")
            
            # Assert
            assert result is True
            mock_server.send_message.assert_called_once()
    
    def test_send_welcome_email_smtp_error(self):
        """Testa erro no envio de email"""
        # Arrange
        with patch('smtplib.SMTP') as mock_smtp:
            mock_smtp.side_effect = Exception("SMTP Error")
            
            service = EmailService()
            
            # Act
            result = service.send_welcome_email("joao@example.com", "João")
            
            # Assert
            assert result is False
```

### Testes de Integração

#### Testando Repositórios

```python
# tests/integration/test_repositories.py
import pytest
from app.repositories.user_repository import UserRepository
from app.repositories.item_repository import ItemRepository
from app.models.user import User
from app.models.item import Item

class TestUserRepository:
    def test_create_user(self, db_session):
        """Testa criação de usuário no banco"""
        repo = UserRepository(db_session)
        user_data = {
            "name": "João Silva",
            "email": "joao@example.com",
            "password": "hashed_password"
        }
        
        user = repo.create(user_data)
        
        assert user.id is not None
        assert user.name == "João Silva"
        assert user.email == "joao@example.com"
    
    def test_get_user_by_email(self, db_session, user_factory):
        """Testa busca de usuário por email"""
        # Arrange
        user = user_factory(email="joao@example.com")
        repo = UserRepository(db_session)
        
        # Act
        found_user = repo.get_by_email("joao@example.com")
        
        # Assert
        assert found_user is not None
        assert found_user.email == "joao@example.com"
    
    def test_update_user(self, db_session, user_factory):
        """Testa atualização de usuário"""
        # Arrange
        user = user_factory(name="Nome Original")
        repo = UserRepository(db_session)
        
        # Act
        updated_user = repo.update(user.id, {"name": "Nome Atualizado"})
        
        # Assert
        assert updated_user.name == "Nome Atualizado"
    
    def test_delete_user(self, db_session, user_factory):
        """Testa exclusão de usuário"""
        # Arrange
        user = user_factory()
        repo = UserRepository(db_session)
        
        # Act
        result = repo.delete(user.id)
        
        # Assert
        assert result is True
        deleted_user = repo.get_by_id(user.id)
        assert deleted_user is None
    
    def test_list_users_with_pagination(self, db_session, user_factory):
        """Testa listagem de usuários com paginação"""
        # Arrange
        users = [user_factory() for _ in range(5)]
        repo = UserRepository(db_session)
        
        # Act
        result = repo.list_users(skip=0, limit=3)
        
        # Assert
        assert len(result) == 3
    
    def test_count_users(self, db_session, user_factory):
        """Testa contagem de usuários"""
        # Arrange
        [user_factory() for _ in range(3)]
        repo = UserRepository(db_session)
        
        # Act
        count = repo.count()
        
        # Assert
        assert count == 3

class TestItemRepository:
    def test_create_item_with_user(self, db_session, user_factory):
        """Testa criação de item associado a usuário"""
        # Arrange
        user = user_factory()
        repo = ItemRepository(db_session)
        item_data = {
            "name": "Produto Teste",
            "description": "Descrição",
            "price": 99.99,
            "user_id": user.id
        }
        
        # Act
        item = repo.create(item_data)
        
        # Assert
        assert item.id is not None
        assert item.user_id == user.id
        assert item.user.name == user.name  # testa relacionamento
    
    def test_search_items_by_name(self, db_session, user_factory, item_factory):
        """Testa busca de itens por nome"""
        # Arrange
        user = user_factory()
        item1 = item_factory(name="Produto Python", user=user)
        item2 = item_factory(name="Curso FastAPI", user=user)
        item3 = item_factory(name="Livro Django", user=user)
        
        repo = ItemRepository(db_session)
        
        # Act
        results = repo.search_by_name("Python")
        
        # Assert
        assert len(results) == 1
        assert results[0].name == "Produto Python"
```

### Executando os Testes

#### Comandos Úteis

```bash
# Executar todos os testes
pytest

# Executar apenas testes unitários
pytest -m unit

# Executar testes com cobertura
pytest --cov=app --cov-report=html

# Executar testes específicos
pytest tests/unit/test_models.py::TestUserModel::test_create_user

# Executar testes em paralelo
pytest -n auto

# Executar testes com saída detalhada
pytest -v

# Executar apenas testes que falharam na última execução
pytest --lf

# Executar testes e parar no primeiro erro
pytest -x
```

#### Interpretando Resultados

```bash
# Exemplo de saída de cobertura
Name                     Stmts   Miss  Cover
--------------------------------------------
app/__init__.py              0      0   100%
app/models/user.py          25      2    92%
app/services/user.py        30      5    83%
app/repositories/user.py    20      1    95%
--------------------------------------------
TOTAL                       75      8    89%
```

## Próximos Passos

Com os testes implementados, você pode:

1. **Executar testes regularmente** durante o desenvolvimento
2. **Configurar CI/CD** para executar testes automaticamente
3. **Monitorar cobertura** e manter acima de 80%
4. **Implementar testes de API** para endpoints específicos
5. **Adicionar testes de performance** com pytest-benchmark

## Resumo

Neste passo, cobrimos:

- ✅ **Conceitos fundamentais** de testes automatizados
- ✅ **Configuração do ambiente** com pytest e FastAPI
- ✅ **Testes unitários** para modelos e schemas
- ✅ **Testes de serviços** com mocking
- ✅ **Testes de integração** com banco de dados
- ✅ **Fixtures e factories** para dados de teste
- ✅ **Testes parametrizados** e estratégias AAA
- ✅ **Comandos pytest** e interpretação de resultados

Os testes são fundamentais para manter a qualidade e confiabilidade da aplicação, permitindo refatorações seguras e desenvolvimento ágil.

---

**Anterior:** [Step 3: Autenticação](step_3.md) | **Próximo:** [Step 5: Cache e Otimizações](step_5.md)

# Deploy, Monitoramento e Observabilidade

Implementar deploy em produção com Docker, CI/CD, monitoramento completo, logging estruturado e observabilidade para uma aplicação FastAPI robusta e escalável.

## 🎯 O que você vai aprender

- Containerização com Docker
- Deploy em produção (AWS, GCP, Azure)
- CI/CD com GitHub Actions
- Monitoramento e métricas
- Logging estruturado
- Observabilidade e tracing
- Health checks e readiness
- Backup e disaster recovery

---

## 1. Conceitos Fundamentais de Deployment e Monitoramento

### 1.1 O que é Deployment?

Deployment é o processo de disponibilizar uma aplicação para uso em um ambiente de produção. Envolve:

- **Empacotamento**: Preparar a aplicação e suas dependências
- **Distribuição**: Mover a aplicação para o ambiente de produção
- **Configuração**: Ajustar configurações para o ambiente específico
- **Inicialização**: Colocar a aplicação em funcionamento

### 1.2 Ambientes de Deployment

```python
# Exemplo de configuração por ambiente
from enum import Enum
from pydantic import BaseSettings

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class Settings(BaseSettings):
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    database_url: str
    redis_url: str
    secret_key: str
    
    class Config:
        env_file = f".env.{environment}"
        
    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION
```

### 1.3 Estratégias de Deployment

#### Blue-Green Deployment
- Mantém duas versões idênticas do ambiente
- Permite rollback instantâneo
- Zero downtime durante atualizações

#### Rolling Deployment
- Atualiza instâncias gradualmente
- Mantém disponibilidade durante o processo
- Permite detecção precoce de problemas

#### Canary Deployment
- Direciona pequena porcentagem do tráfego para nova versão
- Permite validação com usuários reais
- Reduz riscos de problemas em larga escala

### 1.4 Os Três Pilares da Observabilidade

#### Logs
- Registros de eventos da aplicação
- Essenciais para debugging e auditoria
- Devem ser estruturados e pesquisáveis

#### Métricas
- Dados quantitativos sobre performance
- Permitem alertas automáticos
- Essenciais para capacity planning

#### Traces
- Rastreamento de requisições através de serviços
- Identificam gargalos em sistemas distribuídos
- Mostram o fluxo completo de uma operação

---

## 2. Containerização com Docker

### 2.1 Dockerfile Multi-stage Otimizado

```dockerfile
# Dockerfile
FROM python:3.11-slim as base

# Configurações base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Estágio de dependências
FROM base as dependencies

# Instalar dependências do sistema necessárias para compilação
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python
COPY requirements.txt requirements-dev.txt ./
RUN pip install --user --no-warn-script-location -r requirements.txt

# Estágio de desenvolvimento
FROM dependencies as development

# Instalar dependências de desenvolvimento
RUN pip install --user --no-warn-script-location -r requirements-dev.txt

# Copiar código
COPY . /app
WORKDIR /app

# Usuário não-root
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Estágio de produção
FROM base as production

# Instalar apenas dependências de runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependências Python do estágio anterior
COPY --from=dependencies /root/.local /root/.local

# Criar usuário não-root
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copiar aplicação
COPY --chown=appuser:appuser . /app
WORKDIR /app

# Configurar PATH para incluir pacotes do usuário
ENV PATH=/root/.local/bin:$PATH

# Usar usuário não-root
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expor porta
EXPOSE 8000

# Comando padrão
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### 2.2 Docker Compose para Desenvolvimento

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build:
      context: .
      target: development
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - /app/__pycache__
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/fastapi_db
      - REDIS_URL=redis://redis:6379/0
      - ENVIRONMENT=development
    depends_on:
      - db
      - redis
    networks:
      - app-network

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: fastapi_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - app-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - app
    networks:
      - app-network

volumes:
  postgres_data:
  redis_data:

networks:
  app-network:
    driver: bridge
```

### 2.3 Docker Compose para Produção

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  app:
    build:
      context: .
      target: production
    restart: unless-stopped
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
    depends_on:
      - db
      - redis
    networks:
      - app-network
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M

  db:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data
    networks:
      - app-network
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.prod.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - static_files:/app/static
    depends_on:
      - app
    networks:
      - app-network

volumes:
  postgres_data:
  redis_data:
  static_files:

networks:
  app-network:
    driver: overlay
```

---

## 3. Configuração Nginx

### 3.1 Nginx para Produção

```nginx
# nginx/nginx.prod.conf
events {
    worker_connections 2048;
}

http {
    # Configurações de performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

    # Upstream servers
    upstream app {
        least_conn;
        server app_1:8000 max_fails=3 fail_timeout=30s;
        server app_2:8000 max_fails=3 fail_timeout=30s;
        server app_3:8000 max_fails=3 fail_timeout=30s;
    }

    # HTTP to HTTPS redirect
    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

        # Static files
        location /static/ {
            alias /app/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # API endpoints with rate limiting
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Login endpoint with stricter rate limiting
        location /api/auth/login {
            limit_req zone=login burst=5 nodelay;
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket connections
        location /ws {
            proxy_pass http://app;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 86400;
        }

        # Health check
        location /health {
            access_log off;
            proxy_pass http://app;
            proxy_set_header Host $host;
        }
    }
}
```

---

## 4. CI/CD com GitHub Actions

### 4.1 Workflow Principal

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: \${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: \${{ runner.os }}-pip-\${{ hashFiles('**/requirements*.txt') }}
        restore-keys: |
          \${{ runner.os }}-pip-

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run linting
      run: |
        flake8 app tests
        black --check app tests
        isort --check-only app tests

    - name: Run type checking
      run: mypy app

    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
        REDIS_URL: redis://localhost:6379/0
        SECRET_KEY: test-secret-key
      run: |
        pytest tests/ -v --cov=app --cov-report=xml --cov-report=html

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Run security scan
      uses: pypa/gh-action-pip-audit@v1.0.8
      with:
        inputs: requirements.txt

    - name: Run Bandit security linter
      run: |
        pip install bandit
        bandit -r app/

  build:
    needs: [test, security]
    runs-on: ubuntu-latest
    if: github.event_name == 'push'

    steps:
    - uses: actions/checkout@v4

    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: \${{ env.REGISTRY }}
        username: \${{ github.actor }}
        password: \${{ secrets.GITHUB_TOKEN }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: \${{ env.REGISTRY }}/\${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=sha,prefix={{branch}}-

    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        target: production
        push: true
        tags: \${{ steps.meta.outputs.tags }}
        labels: \${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    environment: staging

    steps:
    - uses: actions/checkout@v4

    - name: Deploy to staging
      run: |
        echo "Deploying to staging environment"
        # Aqui você adicionaria os comandos específicos do seu provedor

  deploy-production:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production

    steps:
    - uses: actions/checkout@v4

    - name: Deploy to production
      run: |
        echo "Deploying to production environment"
        # Comandos de deployment para produção
```

---

## 5. Logging Estruturado

### 5.1 Configuração de Logging

```python
# app/core/logging.py
import json
import logging
import sys
from datetime import datetime
from typing import Any
from pythonjsonlogger import jsonlogger

class StructuredLogger:
    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Evitar duplicação de handlers
        if not self.logger.handlers:
            self._setup_handler()
    
    def _setup_handler(self):
        """Configurar handler com formato JSON"""
        handler = logging.StreamHandler(sys.stdout)
        
        # Formato JSON para produção
        formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(name)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S'
        )
        
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log(self, level: str, message: str, **kwargs):
        """Log estruturado com contexto adicional"""
        extra_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": "fastapi-app",
            **kwargs
        }
        
        log_method = getattr(self.logger, level.lower())
        log_method(message, extra=extra_data)
    
    def info(self, message: str, **kwargs):
        self.log("info", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self.log("error", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self.log("warning", message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        self.log("debug", message, **kwargs)

# Instância global
logger = StructuredLogger("fastapi-app")
```

### 5.2 Middleware de Logging

```python
# app/middleware/logging.py
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Gerar ID único para a requisição
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Capturar informações da requisição
        start_time = time.time()
        
        # Log da requisição recebida
        logger.info(
            "Request received",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            user_agent=request.headers.get("user-agent"),
            client_ip=request.client.host if request.client else None
        )
        
        try:
            # Processar requisição
            response = await call_next(request)
            
            # Calcular tempo de processamento
            process_time = time.time() - start_time
            
            # Log da resposta
            logger.info(
                "Request completed",
                request_id=request_id,
                status_code=response.status_code,
                process_time=process_time,
                response_size=response.headers.get("content-length")
            )
            
            # Adicionar headers de rastreamento
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Log de erro
            process_time = time.time() - start_time
            logger.error(
                "Request failed",
                request_id=request_id,
                error=str(e),
                error_type=type(e).__name__,
                process_time=process_time
            )
            raise
```

---

## 6. Métricas com Prometheus

### 6.1 Configuração de Métricas

```python
# app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest
from prometheus_client.core import CollectorRegistry
import psutil
import time
from typing import Any

class MetricsCollector:
    def __init__(self):
        self.registry = CollectorRegistry()
        
        # Métricas HTTP
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        self.http_request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # Métricas de sistema
        self.cpu_usage = Gauge(
            'system_cpu_usage_percent',
            'System CPU usage percentage',
            registry=self.registry
        )
        
        self.memory_usage = Gauge(
            'system_memory_usage_bytes',
            'System memory usage in bytes',
            registry=self.registry
        )
        
        self.disk_usage = Gauge(
            'system_disk_usage_percent',
            'System disk usage percentage',
            registry=self.registry
        )
        
        # Métricas de aplicação
        self.active_connections = Gauge(
            'websocket_connections_active',
            'Active WebSocket connections',
            registry=self.registry
        )
        
        self.database_connections = Gauge(
            'database_connections_active',
            'Active database connections',
            registry=self.registry
        )
        
        self.cache_hits = Counter(
            'cache_hits_total',
            'Total cache hits',
            ['cache_type'],
            registry=self.registry
        )
        
        self.cache_misses = Counter(
            'cache_misses_total',
            'Total cache misses',
            ['cache_type'],
            registry=self.registry
        )
        
        # Informações da aplicação
        self.app_info = Info(
            'app_info',
            'Application information',
            registry=self.registry
        )
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Registrar métricas de requisição HTTP"""
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code
        ).inc()
        
        self.http_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def update_system_metrics(self):
        """Atualizar métricas do sistema"""
        self.cpu_usage.set(psutil.cpu_percent())
        
        memory = psutil.virtual_memory()
        self.memory_usage.set(memory.used)
        
        disk = psutil.disk_usage('/')
        self.disk_usage.set(disk.percent)
    
    def set_active_connections(self, count: int):
        """Definir número de conexões WebSocket ativas"""
        self.active_connections.set(count)
    
    def set_database_connections(self, count: int):
        """Definir número de conexões de base de dados ativas"""
        self.database_connections.set(count)
    
    def record_cache_hit(self, cache_type: str):
        """Registrar cache hit"""
        self.cache_hits.labels(cache_type=cache_type).inc()
    
    def record_cache_miss(self, cache_type: str):
        """Registrar cache miss"""
        self.cache_misses.labels(cache_type=cache_type).inc()
    
    def set_app_info(self, version: str, environment: str):
        """Definir informações da aplicação"""
        self.app_info.info({
            'version': version,
            'environment': environment,
            'python_version': psutil.sys.version
        })
    
    def get_metrics(self) -> str:
        """Obter métricas no formato Prometheus"""
        self.update_system_metrics()
        return generate_latest(self.registry)

# Instância global
metrics = MetricsCollector()
```

### 6.2 Middleware de Métricas

```python
# app/middleware/metrics.py
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.metrics import metrics

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Extrair endpoint limpo (sem parâmetros)
        endpoint = self._clean_endpoint(request.url.path)
        
        try:
            response = await call_next(request)
            
            # Calcular duração
            duration = time.time() - start_time
            
            # Registrar métricas
            metrics.record_http_request(
                method=request.method,
                endpoint=endpoint,
                status_code=response.status_code,
                duration=duration
            )
            
            return response
            
        except Exception as e:
            # Registrar erro
            duration = time.time() - start_time
            metrics.record_http_request(
                method=request.method,
                endpoint=endpoint,
                status_code=500,
                duration=duration
            )
            raise
    
    def _clean_endpoint(self, path: str) -> str:
        """Limpar endpoint para evitar cardinalidade alta"""
        # Substituir IDs por placeholder
        import re
        
        # Padrões comuns de ID
        patterns = [
            (r'/\d+', '/{id}'),
            (r'/[a-f0-9-]{36}', '/{uuid}'),
            (r'/[a-f0-9]{24}', '/{objectid}'),
        ]
        
        for pattern, replacement in patterns:
            path = re.sub(pattern, replacement, path)
        
        return path
```

---

## 7. Health Checks Avançados

### 7.1 Sistema de Health Checks

```python
# app/core/health.py
import asyncio
import time
from typing import Any
from enum import Enum
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from app.database import get_db
from app.core.redis import get_redis

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@dataclass
class HealthCheck:
    name: str
    status: HealthStatus
    response_time: float
    details: dict[str, Any] = None
    error: str = None

class HealthMonitor:
    def __init__(self):
        self.checks = {}
        self.last_check_time = None
        self.cache_duration = 30  # segundos
    
    async def check_database(self) -> HealthCheck:
        """Verificar saúde da base de dados"""
        start_time = time.time()
        
        try:
            async with get_db() as db:
                # Executar query simples
                result = await db.execute("SELECT 1")
                await result.fetchone()
                
                response_time = time.time() - start_time
                
                return HealthCheck(
                    name="database",
                    status=HealthStatus.HEALTHY,
                    response_time=response_time,
                    details={"connection": "active"}
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheck(
                name="database",
                status=HealthStatus.UNHEALTHY,
                response_time=response_time,
                error=str(e)
            )
    
    async def check_redis(self) -> HealthCheck:
        """Verificar saúde do Redis"""
        start_time = time.time()
        
        try:
            redis = await get_redis()
            await redis.ping()
            
            response_time = time.time() - start_time
            
            # Obter informações adicionais
            info = await redis.info()
            
            return HealthCheck(
                name="redis",
                status=HealthStatus.HEALTHY,
                response_time=response_time,
                details={
                    "connected_clients": info.get("connected_clients"),
                    "used_memory": info.get("used_memory_human"),
                    "uptime": info.get("uptime_in_seconds")
                }
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheck(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                response_time=response_time,
                error=str(e)
            )
    
    async def check_disk_space(self, threshold: float = 0.9) -> HealthCheck:
        """Verificar espaço em disco"""
        import psutil
        start_time = time.time()
        
        try:
            disk_usage = psutil.disk_usage('/')
            usage_percent = disk_usage.used / disk_usage.total
            
            response_time = time.time() - start_time
            
            if usage_percent < threshold:
                status = HealthStatus.HEALTHY
            elif usage_percent < 0.95:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            return HealthCheck(
                name="disk_space",
                status=status,
                response_time=response_time,
                details={
                    "usage_percent": round(usage_percent * 100, 2),
                    "free_gb": round(disk_usage.free / (1024**3), 2),
                    "total_gb": round(disk_usage.total / (1024**3), 2)
                }
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheck(
                name="disk_space",
                status=HealthStatus.UNHEALTHY,
                response_time=response_time,
                error=str(e)
            )
    
    async def run_all_checks(self) -> dict[str, Any]:
        """Executar todos os health checks"""
        current_time = time.time()
        
        # Usar cache se disponível
        if (self.last_check_time and 
            current_time - self.last_check_time < self.cache_duration and
            self.checks):
            return self.checks
        
        # Executar checks em paralelo
        checks = await asyncio.gather(
            self.check_database(),
            self.check_redis(),
            self.check_disk_space(),
            return_exceptions=True
        )
        
        # Processar resultados
        results = {}
        overall_status = HealthStatus.HEALTHY
        
        for check in checks:
            if isinstance(check, Exception):
                continue
                
            results[check.name] = {
                "status": check.status,
                "response_time": check.response_time,
                "details": check.details,
                "error": check.error
            }
            
            # Determinar status geral
            if check.status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
            elif check.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED
        
        self.checks = {
            "status": overall_status,
            "timestamp": current_time,
            "checks": results
        }
        
        self.last_check_time = current_time
        return self.checks

# Instância global
health_monitor = HealthMonitor()
```

---

## 8. Sistema de Alertas

### 8.1 Configuração de Alertas

```python
# app/core/alerts.py
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
import aiohttp

class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Alert:
    name: str
    severity: AlertSeverity
    message: str
    details: dict[str, Any]
    timestamp: datetime
    resolved: bool = False

class AlertManager:
    def __init__(self):
        self.active_alerts: dict[str, Alert] = {}
        self.alert_history: list[Alert] = []
        self.notification_channels = []
        
        # Configurações de throttling
        self.alert_cooldown = {}
        self.cooldown_duration = timedelta(minutes=15)
    
    def add_notification_channel(self, channel):
        """Adicionar canal de notificação"""
        self.notification_channels.append(channel)
    
    async def trigger_alert(self, alert: Alert):
        """Disparar alerta"""
        alert_key = f"{alert.name}_{alert.severity}"
        
        # Verificar cooldown
        if self._is_in_cooldown(alert_key):
            return
        
        # Adicionar aos alertas ativos
        self.active_alerts[alert_key] = alert
        self.alert_history.append(alert)
        
        # Definir cooldown
        self.alert_cooldown[alert_key] = datetime.utcnow()
        
        # Enviar notificações
        await self._send_notifications(alert)
        
        logger.error(
            f"Alert triggered: {alert.name}",
            alert_name=alert.name,
            severity=alert.severity,
            message=alert.message,
            details=alert.details
        )
    
    async def resolve_alert(self, alert_name: str, severity: AlertSeverity):
        """Resolver alerta"""
        alert_key = f"{alert_name}_{severity}"
        
        if alert_key in self.active_alerts:
            alert = self.active_alerts[alert_key]
            alert.resolved = True
            del self.active_alerts[alert_key]
            
            # Notificar resolução
            await self._send_resolution_notification(alert)
            
            logger.info(
                f"Alert resolved: {alert_name}",
                alert_name=alert_name,
                severity=severity
            )
    
    def _is_in_cooldown(self, alert_key: str) -> bool:
        """Verificar se alerta está em cooldown"""
        if alert_key not in self.alert_cooldown:
            return False
        
        last_alert = self.alert_cooldown[alert_key]
        return datetime.utcnow() - last_alert < self.cooldown_duration
    
    async def _send_notifications(self, alert: Alert):
        """Enviar notificações para todos os canais"""
        tasks = []
        
        for channel in self.notification_channels:
            tasks.append(channel.send_alert(alert))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_resolution_notification(self, alert: Alert):
        """Enviar notificação de resolução"""
        tasks = []
        
        for channel in self.notification_channels:
            tasks.append(channel.send_resolution(alert))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

# Instância global
alert_manager = AlertManager()
```

---

## 9. Endpoints de Monitoramento

### 9.1 API de Monitoramento

```python
# app/api/monitoring.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, Response
from app.core.health import health_monitor, HealthStatus
from app.core.metrics import metrics
from app.core.logging import logger

monitoring_router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@monitoring_router.get("/health")
async def health_check():
    """Health check básico para load balancers"""
    try:
        health_data = await health_monitor.run_all_checks()
        
        if health_data["status"] == HealthStatus.UNHEALTHY:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "unhealthy"}
            )
        
        return {"status": "healthy"}
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "error": str(e)}
        )

@monitoring_router.get("/health/detailed")
async def detailed_health_check():
    """Health check detalhado"""
    try:
        health_data = await health_monitor.run_all_checks()
        return health_data
        
    except Exception as e:
        logger.error("Detailed health check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )

@monitoring_router.get("/metrics")
async def get_metrics():
    """Endpoint para métricas Prometheus"""
    try:
        metrics_data = metrics.get_metrics()
        return Response(content=metrics_data, media_type="text/plain")
        
    except Exception as e:
        logger.error("Failed to get metrics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get metrics"
        )

@monitoring_router.get("/info")
async def app_info():
    """Informações da aplicação"""
    import os
    import sys
    
    return {
        "name": "FastAPI Application",
        "version": os.getenv("APP_VERSION", "unknown"),
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "python_version": sys.version,
        "uptime": time.time() - start_time
    }
```

---

## 10. Configuração de Ferramentas Externas

### 10.1 Docker Compose com Stack de Monitoramento

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    networks:
      - monitoring

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    networks:
      - monitoring

  kibana:
    image: docker.elastic.co/kibana/kibana:8.8.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch
    networks:
      - monitoring

volumes:
  prometheus_data:
  grafana_data:
  elasticsearch_data:

networks:
  monitoring:
    driver: bridge
```

### 10.2 Configuração Prometheus

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'fastapi-app'
    static_configs:
      - targets: ['app:8000']
    metrics_path: '/monitoring/metrics'
    scrape_interval: 10s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
```

---

## 11. Scripts de Deployment

### 11.1 Script de Deploy para Produção

```bash
#!/bin/bash
# scripts/deploy-production.sh

set -e

# Configurações
REGISTRY="ghcr.io"
IMAGE_NAME="your-org/fastapi-app"
TAG=${1:-latest}
COMPOSE_FILE="docker-compose.prod.yml"

echo "🚀 Starting production deployment..."
echo "📦 Image: $REGISTRY/$IMAGE_NAME:$TAG"

# Verificar se todas as variáveis de ambiente estão definidas
required_vars=("DATABASE_URL" "REDIS_URL" "SECRET_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Environment variable $var is not set"
        exit 1
    fi
done

# Fazer backup da base de dados
echo "💾 Creating database backup..."
./scripts/backup-database.sh

# Fazer pull da nova imagem
echo "📥 Pulling new image..."
docker pull $REGISTRY/$IMAGE_NAME:$TAG

# Executar migrações
echo "📊 Running database migrations..."
docker run --rm \
    --network host \
    -e DATABASE_URL="$DATABASE_URL" \
    $REGISTRY/$IMAGE_NAME:$TAG \
    alembic upgrade head

# Deploy com zero downtime
echo "🔄 Performing rolling update..."
docker-compose -f $COMPOSE_FILE pull
docker-compose -f $COMPOSE_FILE up -d --no-deps app

# Aguardar nova versão ficar pronta
echo "⏳ Waiting for new version to be ready..."
sleep 30

# Verificar saúde da aplicação
echo "🏥 Checking application health..."
for i in {1..10}; do
    if curl -f https://yourdomain.com/health > /dev/null 2>&1; then
        echo "✅ Application is healthy"
        break
    fi
    
    if [ $i -eq 10 ]; then
        echo "❌ Health check failed, rolling back..."
        docker-compose -f $COMPOSE_FILE rollback
        exit 1
    fi
    
    echo "⏳ Attempt $i/10 failed, retrying..."
    sleep 10
done

# Limpeza de imagens antigas
echo "🧹 Cleaning up old images..."
docker image prune -f

echo "🎉 Production deployment completed successfully!"
```

---

## Próximos Passos

Com este step completo, você implementou:

1. **Containerização completa** com Docker multi-stage
2. **CI/CD robusto** com GitHub Actions
3. **Logging estruturado** para debugging eficiente
4. **Métricas Prometheus** para monitoramento de performance
5. **Health checks avançados** para alta disponibilidade
6. **Sistema de alertas** para resposta rápida a problemas
7. **Configuração Nginx** para load balancing e SSL
8. **Scripts de deployment** automatizados

### Exercícios Práticos

1. **Deploy Completo**: Configure um ambiente de produção completo
2. **Monitoramento Avançado**: Implemente dashboards Grafana personalizados
3. **Alertas Personalizados**: Configure alertas específicos para seu domínio
4. **Backup Automatizado**: Implemente estratégia de backup e recovery
5. **Scaling Horizontal**: Configure auto-scaling baseado em métricas

### Recursos Adicionais

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Prometheus Monitoring](https://prometheus.io/docs/guides/go-application/)
- [Grafana Dashboards](https://grafana.com/docs/grafana/latest/dashboards/)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Nginx Configuration](https://nginx.org/en/docs/)

### Deploy Script (scripts/deploy.sh)

```bash
#!/bin/bash

set -e

# Configurações
ENVIRONMENT=${1:-production}
IMAGE_TAG=${2:-latest}
REGISTRY="ghcr.io/your-username/fastapi-app"

echo "🚀 Deploying FastAPI app to $ENVIRONMENT"

# Verificar se Docker está rodando
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running"
    exit 1
fi

# Pull da imagem mais recente
echo "📥 Pulling latest image..."
docker pull $REGISTRY:$IMAGE_TAG

# Parar containers antigos
echo "🛑 Stopping old containers..."
docker-compose -f docker-compose.$ENVIRONMENT.yml down

# Backup do banco de dados
if [ "$ENVIRONMENT" = "production" ]; then
    echo "💾 Creating database backup..."
    docker exec postgres pg_dump -U postgres fastapi_db > backup_$(date +%Y%m%d_%H%M%S).sql
fi

# Iniciar novos containers
echo "🔄 Starting new containers..."
docker-compose -f docker-compose.$ENVIRONMENT.yml up -d

# Aguardar containers ficarem saudáveis
echo "⏳ Waiting for containers to be healthy..."
sleep 30

# Verificar health checks
echo "🔍 Checking health status..."
for i in {1..10}; do
    if curl -f http://localhost/health > /dev/null 2>&1; then
        echo "✅ Application is healthy"
        break
    fi
    
    if [ $i -eq 10 ]; then
        echo "❌ Application failed health check"
        exit 1
    fi
    
    echo "⏳ Waiting for application to be ready... ($i/10)"
    sleep 10
done

# Executar migrações se necessário
echo "🔄 Running database migrations..."
docker-compose -f docker-compose.$ENVIRONMENT.yml exec app alembic upgrade head

echo "🎉 Deployment completed successfully!"

# Limpar imagens antigas
echo "🧹 Cleaning up old images..."
docker image prune -f

echo "📊 Deployment summary:"
docker-compose -f docker-compose.$ENVIRONMENT.yml ps
```

---

## 📊 Monitoramento e Observabilidade

### Configuração do Prometheus (monitoring/prometheus.yml)

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'fastapi-app'
    static_configs:
      - targets: ['app:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']

  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
```

### Métricas Customizadas (core/metrics.py)

```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client.core import CollectorRegistry
from fastapi import Request, Response
from typing import Callable
import time
import psutil
import asyncio

# Registry customizado
REGISTRY = CollectorRegistry()

# Métricas HTTP
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code'],
    registry=REGISTRY
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    registry=REGISTRY
)

# Métricas de aplicação
active_connections = Gauge(
    'websocket_active_connections',
    'Number of active WebSocket connections',
    registry=REGISTRY
)

database_connections = Gauge(
    'database_connections_active',
    'Number of active database connections',
    registry=REGISTRY
)

cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type'],
    registry=REGISTRY
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type'],
    registry=REGISTRY
)

# Métricas de sistema
system_cpu_usage = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage',
    registry=REGISTRY
)

system_memory_usage = Gauge(
    'system_memory_usage_bytes',
    'System memory usage in bytes',
    registry=REGISTRY
)

system_disk_usage = Gauge(
    'system_disk_usage_bytes',
    'System disk usage in bytes',
    ['device'],
    registry=REGISTRY
)

class MetricsMiddleware:
    """Middleware para coletar métricas HTTP."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        start_time = time.time()
        
        # Wrapper para capturar response
        response_info = {"status_code": 500}
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                response_info["status_code"] = message["status"]
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            # Registrar métricas
            duration = time.time() - start_time
            method = request.method
            endpoint = self._get_endpoint(request)
            status_code = str(response_info["status_code"])
            
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
    
    def _get_endpoint(self, request: Request) -> str:
        """Extrair endpoint da request."""
        if hasattr(request, 'url') and hasattr(request.url, 'path'):
            path = request.url.path
            # Normalizar paths com IDs
            import re
            path = re.sub(r'/\d+', '/{id}', path)
            return path
        return "unknown"

async def update_system_metrics():
    """Atualizar métricas de sistema periodicamente."""
    while True:
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            system_cpu_usage.set(cpu_percent)
            
            # Memória
            memory = psutil.virtual_memory()
            system_memory_usage.set(memory.used)
            
            # Disco
            for disk in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(disk.mountpoint)
                    system_disk_usage.labels(device=disk.device).set(usage.used)
                except (PermissionError, OSError):
                    continue
            
        except Exception as e:
            print(f"Error updating system metrics: {e}")
        
        await asyncio.sleep(30)  # Atualizar a cada 30 segundos

def get_metrics() -> str:
    """Obter métricas no formato Prometheus."""
    return generate_latest(REGISTRY).decode('utf-8')

# Funções auxiliares para métricas customizadas
def increment_cache_hit(cache_type: str):
    """Incrementar contador de cache hits."""
    cache_hits_total.labels(cache_type=cache_type).inc()

def increment_cache_miss(cache_type: str):
    """Incrementar contador de cache misses."""
    cache_misses_total.labels(cache_type=cache_type).inc()

def set_active_connections(count: int):
    """Definir número de conexões ativas."""
    active_connections.set(count)

def set_database_connections(count: int):
    """Definir número de conexões de banco ativas."""
    database_connections.set(count)
```

### Health Checks (core/health.py)

```python
from fastapi import HTTPException
from sqlalchemy.orm import Session
from db.session import SessionLocal, engine
from core.redis import redis_client
from typing import Any
import asyncio
import time
import psutil

class HealthChecker:
    """Verificador de saúde da aplicação."""
    
    def __init__(self):
        self.checks = {
            "database": self._check_database,
            "redis": self._check_redis,
            "disk_space": self._check_disk_space,
            "memory": self._check_memory,
        }
    
    async def check_health(self) -> dict[str, Any]:
        """Executar todos os health checks."""
        results = {}
        overall_status = "healthy"
        
        for check_name, check_func in self.checks.items():
            try:
                start_time = time.time()
                result = await check_func()
                duration = time.time() - start_time
                
                results[check_name] = {
                    "status": "healthy" if result["healthy"] else "unhealthy",
                    "details": result.get("details", {}),
                    "duration_ms": round(duration * 1000, 2)
                }
                
                if not result["healthy"]:
                    overall_status = "unhealthy"
                    
            except Exception as e:
                results[check_name] = {
                    "status": "error",
                    "error": str(e),
                    "duration_ms": 0
                }
                overall_status = "unhealthy"
        
        return {
            "status": overall_status,
            "timestamp": time.time(),
            "checks": results
        }
    
    async def _check_database(self) -> dict[str, Any]:
        """Verificar conexão com banco de dados."""
        try:
            db = SessionLocal()
            try:
                # Executar query simples
                result = db.execute("SELECT 1").fetchone()
                
                # Verificar pool de conexões
                pool = engine.pool
                pool_status = {
                    "size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                    "invalid": pool.invalid()
                }
                
                return {
                    "healthy": result is not None,
                    "details": {
                        "connection_pool": pool_status,
                        "query_result": result[0] if result else None
                    }
                }
            finally:
                db.close()
                
        except Exception as e:
            return {
                "healthy": False,
                "details": {"error": str(e)}
            }
    
    async def _check_redis(self) -> dict[str, Any]:
        """Verificar conexão com Redis."""
        try:
            # Ping Redis
            pong = await redis_client.ping()
            
            # Obter informações do Redis
            info = await redis_client.info()
            
            return {
                "healthy": pong,
                "details": {
                    "ping": pong,
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory": info.get("used_memory", 0),
                    "uptime_in_seconds": info.get("uptime_in_seconds", 0)
                }
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "details": {"error": str(e)}
            }
    
    async def _check_disk_space(self) -> dict[str, Any]:
        """Verificar espaço em disco."""
        try:
            disk_usage = psutil.disk_usage('/')
            free_percent = (disk_usage.free / disk_usage.total) * 100
            
            return {
                "healthy": free_percent > 10,  # Pelo menos 10% livre
                "details": {
                    "total_gb": round(disk_usage.total / (1024**3), 2),
                    "used_gb": round(disk_usage.used / (1024**3), 2),
                    "free_gb": round(disk_usage.free / (1024**3), 2),
                    "free_percent": round(free_percent, 2)
                }
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "details": {"error": str(e)}
            }
    
    async def _check_memory(self) -> dict[str, Any]:
        """Verificar uso de memória."""
        try:
            memory = psutil.virtual_memory()
            available_percent = memory.available / memory.total * 100
            
            return {
                "healthy": available_percent > 10,  # Pelo menos 10% disponível
                "details": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "available_percent": round(available_percent, 2)
                }
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "details": {"error": str(e)}
            }

# Instância global
health_checker = HealthChecker()
```

### Logging Estruturado (core/logging.py)

```python
import logging
import json
import sys
from datetime import datetime
from typing import Any
from pythonjsonlogger import jsonlogger
from core.config import settings

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Formatter JSON customizado."""
    
    def add_fields(self, log_record: dict[str, Any], record: logging.LogRecord, message_dict: dict[str, Any]):
        super().add_fields(log_record, record, message_dict)
        
        # Adicionar timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Adicionar informações da aplicação
        log_record['service'] = 'fastapi-app'
        log_record['version'] = getattr(settings, 'VERSION', '1.0.0')
        log_record['environment'] = settings.ENVIRONMENT
        
        # Adicionar nível do log
        log_record['level'] = record.levelname
        
        # Adicionar informações do módulo
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno

def setup_logging():
    """Configurar logging estruturado."""
    
    # Configurar formatter
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(service)s %(module)s %(funcName)s %(message)s'
    )
    
    # Configurar handler para stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    # Configurar logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    root_logger.addHandler(handler)
    
    # Configurar loggers específicos
    loggers = [
        'uvicorn',
        'uvicorn.access',
        'sqlalchemy.engine',
        'alembic',
        'fastapi'
    ]
    
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
        logger.propagate = True

class StructuredLogger:
    """Logger estruturado para a aplicação."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def info(self, message: str, **kwargs):
        """Log info com contexto adicional."""
        extra = self._prepare_extra(**kwargs)
        self.logger.info(message, extra=extra)
    
    def warning(self, message: str, **kwargs):
        """Log warning com contexto adicional."""
        extra = self._prepare_extra(**kwargs)
        self.logger.warning(message, extra=extra)
    
    def error(self, message: str, **kwargs):
        """Log error com contexto adicional."""
        extra = self._prepare_extra(**kwargs)
        self.logger.error(message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """Log debug com contexto adicional."""
        extra = self._prepare_extra(**kwargs)
        self.logger.debug(message, extra=extra)
    
    def _prepare_extra(self, **kwargs) -> dict[str, Any]:
        """Preparar dados extras para o log."""
        extra = {}
        
        for key, value in kwargs.items():
            # Serializar objetos complexos
            if isinstance(value, (dict, list)):
                extra[key] = json.dumps(value, default=str)
            else:
                extra[key] = str(value)
        
        return extra

# Configurar logging na inicialização
setup_logging()

# Logger padrão da aplicação
logger = StructuredLogger(__name__)
```

---

## 📈 Dashboard de Monitoramento

### Grafana Dashboard (monitoring/grafana-dashboard.json)

```json
{
  "dashboard": {
    "id": null,
    "title": "FastAPI Application Dashboard",
    "tags": ["fastapi", "python"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "HTTP Requests Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ],
        "yAxes": [
          {
            "label": "Requests/sec"
          }
        ]
      },
      {
        "id": 2,
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ]
      },
      {
        "id": 3,
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status_code=~\"4..|5..\"}[5m])",
            "legendFormat": "Error rate"
          }
        ]
      },
      {
        "id": 4,
        "title": "Active WebSocket Connections",
        "type": "singlestat",
        "targets": [
          {
            "expr": "websocket_active_connections",
            "legendFormat": "Connections"
          }
        ]
      },
      {
        "id": 5,
        "title": "Database Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "database_connections_active",
            "legendFormat": "Active connections"
          }
        ]
      },
      {
        "id": 6,
        "title": "Cache Hit Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))",
            "legendFormat": "{{cache_type}} hit rate"
          }
        ]
      },
      {
        "id": 7,
        "title": "System Resources",
        "type": "graph",
        "targets": [
          {
            "expr": "system_cpu_usage_percent",
            "legendFormat": "CPU %"
          },
          {
            "expr": "system_memory_usage_bytes / 1024 / 1024 / 1024",
            "legendFormat": "Memory GB"
          }
        ]
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "5s"
  }
}
```

---

## 🚨 Alertas e Notificações

### Regras de Alerta (monitoring/alert_rules.yml)

```yaml
groups:
  - name: fastapi_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status_code=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }} seconds"

      - alert: DatabaseConnectionsHigh
        expr: database_connections_active > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High number of database connections"
          description: "{{ $value }} active database connections"

      - alert: LowDiskSpace
        expr: (node_filesystem_free_bytes / node_filesystem_size_bytes) * 100 < 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Low disk space"
          description: "Disk space is {{ $value }}% full"

      - alert: HighMemoryUsage
        expr: (system_memory_usage_bytes / node_memory_MemTotal_bytes) * 100 > 90
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value }}%"

      - alert: ApplicationDown
        expr: up{job="fastapi-app"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "FastAPI application is down"
          description: "The FastAPI application has been down for more than 1 minute"
```

---

## 🎯 Próximos Passos

Com deploy e monitoramento implementados, você tem:

1. **Aplicação completa em produção**
2. **Monitoramento abrangente**
3. **CI/CD automatizado**
4. **Observabilidade total**

---

## 📝 Exercícios Práticos

### Exercício 1: Multi-Cloud Deploy
Configure deploy em:
- AWS ECS/EKS
- Google Cloud Run
- Azure Container Instances

### Exercício 2: Disaster Recovery
Implemente:
- Backup automatizado
- Restore procedures
- Failover automático

### Exercício 3: Performance Optimization
Adicione:
- APM (Application Performance Monitoring)
- Distributed tracing
- Custom metrics

---

**Anterior:** [Step 6: WebSockets](step_6.md) | **Início:** [Step 0: Fundamentos](step_0.md)
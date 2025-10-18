# Cache e Otimizações

Implementar sistema de cache robusto e otimizações de performance para melhorar a velocidade e eficiência da API.

## 🎯 O que você vai aprender

- Cache em memória com Redis
- Cache de queries de banco de dados
- Cache de responses HTTP
- Otimização de queries SQL
- Compressão de responses
- Rate limiting
- Monitoramento de performance

## 📖 Conceitos Fundamentais de Cache e Performance

### O que é Cache?

Cache é uma técnica de armazenamento temporário que mantém dados frequentemente acessados em uma localização de acesso rápido, reduzindo a necessidade de buscar os mesmos dados repetidamente de fontes mais lentas.

### Por que usar Cache?

#### 1. **Performance**
- Reduz tempo de resposta
- Diminui latência
- Melhora experiência do usuário

#### 2. **Escalabilidade**
- Reduz carga no banco de dados
- Permite atender mais usuários
- Otimiza uso de recursos

#### 3. **Disponibilidade**
- Mantém dados disponíveis mesmo com falhas
- Reduz dependência de serviços externos
- Melhora resiliência

#### 4. **Economia**
- Reduz custos de infraestrutura
- Diminui uso de CPU e memória
- Otimiza largura de banda

#### 5. **Experiência do Usuário**
- Páginas carregam mais rápido
- Menos tempo de espera
- Interface mais responsiva

### Tipos de Cache

#### 1. **Cache em Memória (In-Memory)**

```python
# Exemplo simples com dicionário Python
cache = {}

def get_user_expensive(user_id: int):
    if user_id in cache:
        print("Cache HIT!")
        return cache[user_id]
    
    print("Cache MISS - buscando no banco...")
    # Simular operação custosa
    import time
    time.sleep(2)
    
    user_data = {"id": user_id, "name": f"User {user_id}"}
    cache[user_id] = user_data
    return user_data

# Uso
user = get_user_expensive(1)  # Demora 2s (MISS)
user = get_user_expensive(1)  # Instantâneo (HIT)
```

#### 2. **Cache Distribuído (Redis/Memcached)**

```python
import redis

# Conexão Redis
r = redis.Redis(host='localhost', port=6379, db=0)

def get_user_redis(user_id: int):
    cache_key = f"user:{user_id}"
    
    # Tentar buscar no cache
    cached_user = r.get(cache_key)
    if cached_user:
        print("Cache HIT!")
        return json.loads(cached_user)
    
    print("Cache MISS - buscando no banco...")
    # Buscar no banco de dados
    user_data = database.get_user(user_id)
    
    # Armazenar no cache por 1 hora
    r.setex(cache_key, 3600, json.dumps(user_data))
    
    return user_data
```

#### 3. **Cache de Banco de Dados**
- Query result cache
- Buffer pool
- Index cache

#### 4. **Cache CDN (Content Delivery Network)**
- Cache de arquivos estáticos
- Cache geográfico
- Cache de imagens

### Estratégias de Cache

#### 1. **Cache-Aside (Lazy Loading)**

```python
def get_user_cache_aside(user_id: int):
    # 1. Verificar cache primeiro
    user = cache.get(f"user:{user_id}")
    
    if user is None:
        # 2. Se não estiver no cache, buscar no banco
        user = database.get_user(user_id)
        
        # 3. Armazenar no cache
        cache.set(f"user:{user_id}", user, ttl=3600)
    
    return user

def update_user_cache_aside(user_id: int, data: dict):
    # 1. Atualizar no banco
    user = database.update_user(user_id, data)
    
    # 2. Invalidar cache
    cache.delete(f"user:{user_id}")
    
    return user
```

#### 2. **Cache-Aside com Invalidação**

```python
def update_user_with_cache_invalidation(user_id: int, data: dict):
    # 1. Atualizar no banco
    user = database.update_user(user_id, data)
    
    # 2. Invalidar caches relacionados
    cache.delete(f"user:{user_id}")
    cache.delete(f"user_profile:{user_id}")
    cache.delete("active_users")  # Lista que pode incluir este usuário
    
    return user
```

#### 3. **Write-Through**

```python
def update_user_write_through(user_id: int, data: dict):
    # 1. Atualizar no banco
    user = database.update_user(user_id, data)
    
    # 2. Atualizar no cache imediatamente
    cache.set(f"user:{user_id}", user, ttl=3600)
    
    return user
```

#### 4. **Write-Behind (Write-Back)**

```python
import asyncio
from collections import deque

class WriteBehindCache:
    def __init__(self):
        self.cache = {}
        self.write_queue = deque()
        self.dirty_keys = set()
    
    def set(self, key: str, value: any):
        # 1. Atualizar cache imediatamente
        self.cache[key] = value
        
        # 2. Marcar como "sujo" para escrita posterior
        self.dirty_keys.add(key)
        self.write_queue.append((key, value))
    
    async def flush_to_database(self):
        """Escrever dados sujos no banco de dados."""
        while self.write_queue:
            key, value = self.write_queue.popleft()
            
            if key in self.dirty_keys:
                # Escrever no banco
                await database.update(key, value)
                self.dirty_keys.remove(key)

# Executar flush periodicamente
async def periodic_flush():
    while True:
        await cache.flush_to_database()
        await asyncio.sleep(30)  # Flush a cada 30 segundos
```

#### 5. **Refresh-Ahead**

```python
import asyncio
from datetime import datetime, timedelta

class RefreshAheadCache:
    def __init__(self):
        self.cache = {}
        self.refresh_times = {}
        self.ttl = 3600  # 1 hora
        self.refresh_threshold = 0.8  # Refresh quando 80% do TTL passou
    
    async def get(self, key: str):
        # Verificar se existe no cache
        if key in self.cache:
            # Verificar se precisa de refresh
            if self._needs_refresh(key):
                # Refresh em background
                asyncio.create_task(self._refresh_key(key))
            
            return self.cache[key]
        
        # Cache miss - buscar e armazenar
        value = await self._fetch_from_source(key)
        self._store(key, value)
        return value
    
    def _needs_refresh(self, key: str) -> bool:
        if key not in self.refresh_times:
            return True
        
        elapsed = datetime.now() - self.refresh_times[key]
        return elapsed.total_seconds() > (self.ttl * self.refresh_threshold)
    
    async def _refresh_key(self, key: str):
        """Refresh key em background."""
        try:
            new_value = await self._fetch_from_source(key)
            self._store(key, new_value)
        except Exception as e:
            print(f"Erro ao fazer refresh de {key}: {e}")
    
    def _store(self, key: str, value: any):
        self.cache[key] = value
        self.refresh_times[key] = datetime.now()
```

### Invalidação de Cache

#### 1. **TTL (Time To Live)**

```python
# Cache com expiração automática
cache.set("user:123", user_data, ttl=3600)  # Expira em 1 hora

# Verificar TTL restante
remaining_ttl = cache.ttl("user:123")
print(f"Cache expira em {remaining_ttl} segundos")
```

#### 2. **Invalidação Manual**

```python
def invalidate_user_cache(user_id: int):
    """Invalidar todos os caches relacionados ao usuário."""
    patterns = [
        f"user:{user_id}",
        f"user_profile:{user_id}",
        f"user_orders:{user_id}",
        f"user_preferences:{user_id}"
    ]
    
    for pattern in patterns:
        cache.delete(pattern)
```

#### 3. **Cache Tags**

```python
class TaggedCache:
    def __init__(self):
        self.cache = {}
        self.tags = {}  # tag -> set of keys
        self.key_tags = {}  # key -> set of tags
    
    def set(self, key: str, value: any, tags: list = None):
        self.cache[key] = value
        
        if tags:
            self.key_tags[key] = set(tags)
            for tag in tags:
                if tag not in self.tags:
                    self.tags[tag] = set()
                self.tags[tag].add(key)
    
    def invalidate_tag(self, tag: str):
        """Invalidar todas as chaves com uma tag específica."""
        if tag in self.tags:
            keys_to_delete = self.tags[tag].copy()
            
            for key in keys_to_delete:
                self.delete(key)
    
    def delete(self, key: str):
        if key in self.cache:
            del self.cache[key]
        
        # Remover das tags
        if key in self.key_tags:
            for tag in self.key_tags[key]:
                self.tags[tag].discard(key)
            del self.key_tags[key]

# Uso
tagged_cache = TaggedCache()

# Armazenar com tags
tagged_cache.set("user:123", user_data, tags=["user", "profile"])
tagged_cache.set("user:456", user_data2, tags=["user", "profile"])
tagged_cache.set("post:789", post_data, tags=["post", "user:123"])

# Invalidar todos os caches de usuário
tagged_cache.invalidate_tag("user")
```

### Métricas de Cache

#### 1. **Hit Rate (Taxa de Acerto)**

```python
class CacheMetrics:
    def __init__(self):
        self.hits = 0
        self.misses = 0
    
    def record_hit(self):
        self.hits += 1
    
    def record_miss(self):
        self.misses += 1
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0
    
    @property
    def miss_rate(self) -> float:
        return 100 - self.hit_rate

# Uso
metrics = CacheMetrics()

def get_with_metrics(key: str):
    if key in cache:
        metrics.record_hit()
        return cache[key]
    else:
        metrics.record_miss()
        # Buscar dados...
        return data

print(f"Hit Rate: {metrics.hit_rate:.2f}%")
```

#### 2. **Miss Rate (Taxa de Erro)**
- Complemento do Hit Rate
- Indica eficiência do cache
- Meta: < 10% para caches críticos

#### 3. **Eviction Rate (Taxa de Remoção)**
- Frequência de remoção de itens
- Indica se cache está dimensionado corretamente

### Algoritmos de Remoção (Eviction)

#### 1. **LRU (Least Recently Used)**

```python
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = OrderedDict()
    
    def get(self, key: str):
        if key in self.cache:
            # Mover para o final (mais recente)
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    def set(self, key: str, value: any):
        if key in self.cache:
            # Atualizar e mover para o final
            self.cache.move_to_end(key)
        elif len(self.cache) >= self.capacity:
            # Remover o menos recente (primeiro)
            self.cache.popitem(last=False)
        
        self.cache[key] = value

# Uso
lru = LRUCache(capacity=3)
lru.set("a", 1)
lru.set("b", 2)
lru.set("c", 3)
lru.get("a")  # 'a' se torna o mais recente
lru.set("d", 4)  # 'b' é removido (menos recente)
```

#### 2. **LFU (Least Frequently Used)**
- Remove itens menos acessados
- Mantém contador de acessos

#### 3. **FIFO (First In, First Out)**
- Remove itens mais antigos
- Simples de implementar

#### 4. **Random**
- Remove itens aleatoriamente
- Útil quando padrão de acesso é imprevisível

### Cache Warming

```python
async def warm_cache():
    """Pré-carregar dados importantes no cache."""
    
    # 1. Usuários mais ativos
    active_users = await database.get_active_users(limit=100)
    for user in active_users:
        cache.set(f"user:{user.id}", user, ttl=3600)
    
    # 2. Produtos mais vendidos
    popular_products = await database.get_popular_products(limit=50)
    for product in popular_products:
        cache.set(f"product:{product.id}", product, ttl=7200)
    
    # 3. Configurações do sistema
    settings = await database.get_system_settings()
    cache.set("system_settings", settings, ttl=86400)  # 24 horas
    
    print("Cache warming completed!")

# Executar durante inicialização da aplicação
await warm_cache()
```

### Problemas Comuns de Cache

#### 1. **Cache Stampede**

```python
import asyncio
from typing import Dict

class StampedeProtection:
    def __init__(self):
        self.locks: Dict[str, asyncio.Lock] = {}
    
    async def get_or_compute(self, key: str, compute_func, ttl: int = 3600):
        # Verificar cache primeiro
        cached_value = cache.get(key)
        if cached_value is not None:
            return cached_value
        
        # Usar lock para evitar múltiplas computações
        if key not in self.locks:
            self.locks[key] = asyncio.Lock()
        
        async with self.locks[key]:
            # Verificar novamente após adquirir lock
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Computar valor
            value = await compute_func()
            cache.set(key, value, ttl=ttl)
            
            return value

# Uso
protection = StampedeProtection()

async def expensive_computation():
    await asyncio.sleep(5)  # Simular operação custosa
    return "computed_value"

# Múltiplas chamadas simultâneas só executarão a função uma vez
value = await protection.get_or_compute("expensive_key", expensive_computation)
```

#### 2. **Hot Keys**

```python
# Problema: Uma chave muito acessada sobrecarrega o servidor Redis

# Solução 1: Replicação local
local_cache = {}

async def get_hot_key(key: str):
    # Verificar cache local primeiro
    if key in local_cache:
        return local_cache[key]
    
    # Buscar no Redis
    value = await redis_cache.get(key)
    
    # Armazenar localmente por pouco tempo
    local_cache[key] = value
    
    # Limpar cache local periodicamente
    asyncio.create_task(clear_local_cache_later(key, delay=60))
    
    return value

# Solução 2: Sharding
def get_shard_key(key: str, shard_count: int = 10) -> str:
    import hashlib
    hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
    shard = hash_value % shard_count
    return f"{key}:shard:{shard}"

async def get_with_sharding(key: str):
    shard_key = get_shard_key(key)
    return await redis_cache.get(shard_key)
```

#### 3. **Cache Penetration**

```python
# Problema: Queries para dados inexistentes sempre vão ao banco

async def get_user_safe(user_id: int):
    cache_key = f"user:{user_id}"
    
    # Verificar cache
    cached_value = await cache.get(cache_key)
    if cached_value is not None:
        # Verificar se é um "null" cacheado
        if cached_value == "NULL":
            return None
        return cached_value
    
    # Buscar no banco
    user = await database.get_user(user_id)
    
    if user is None:
        # Cachear "null" por pouco tempo
        await cache.set(cache_key, "NULL", ttl=300)  # 5 minutos
        return None
    
    # Cachear resultado válido
    await cache.set(cache_key, user, ttl=3600)
    return user
```

### Monitoramento de Cache

```python
class CacheMonitor:
    def __init__(self):
        self.metrics = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }
    
    def record_hit(self):
        self.metrics["hits"] += 1
    
    def record_miss(self):
        self.metrics["misses"] += 1
    
    def record_set(self):
        self.metrics["sets"] += 1
    
    def record_delete(self):
        self.metrics["deletes"] += 1
    
    def record_error(self):
        self.metrics["errors"] += 1
    
    def get_stats(self) -> dict:
        total_requests = self.metrics["hits"] + self.metrics["misses"]
        
        return {
            "total_requests": total_requests,
            "hit_rate": (self.metrics["hits"] / total_requests * 100) if total_requests > 0 else 0,
            "miss_rate": (self.metrics["misses"] / total_requests * 100) if total_requests > 0 else 0,
            "operations": {
                "hits": self.metrics["hits"],
                "misses": self.metrics["misses"],
                "sets": self.metrics["sets"],
                "deletes": self.metrics["deletes"],
                "errors": self.metrics["errors"]
            }
        }

# Instância global
cache_monitor = CacheMonitor()

# Wrapper para monitoramento
async def monitored_cache_get(key: str):
    try:
        value = await cache.get(key)
        if value is not None:
            cache_monitor.record_hit()
        else:
            cache_monitor.record_miss()
        return value
    except Exception as e:
        cache_monitor.record_error()
        raise
```

---

## 🚀 Configuração Prática de Redis e Cache

### Docker Compose para Desenvolvimento

```yaml
# docker-compose.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: fastapi_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: >
      redis-server
      --appendonly yes
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
    networks:
      - app_network
    restart: unless-stopped

  app:
    build: .
    container_name: fastapi_app
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://user:password@postgres:5432/fastapi_db
    depends_on:
      - redis
      - postgres
    networks:
      - app_network
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    container_name: fastapi_postgres
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: fastapi_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - app_network
    restart: unless-stopped

volumes:
  redis_data:
  postgres_data:

networks:
  app_network:
    driver: bridge
```

### Configuração de Ambiente

```python
# app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None
    REDIS_MAX_CONNECTIONS: int = 20
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5
    
    # Cache TTL Settings (em segundos)
    CACHE_TTL_USER: int = 3600  # 1 hora
    CACHE_TTL_ITEM: int = 7200  # 2 horas
    CACHE_TTL_SEARCH: int = 1800  # 30 minutos
    CACHE_TTL_DEFAULT: int = 3600  # 1 hora
    
    # Cache Configuration
    CACHE_ENABLED: bool = True
    CACHE_KEY_PREFIX: str = "fastapi"
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/fastapi_db"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### Cliente Redis Assíncrono

```python
# app/core/cache.py
import redis.asyncio as redis
from typing import Optional, Any, Union, List
import json
import pickle
from datetime import timedelta
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    """Cliente Redis assíncrono com funcionalidades avançadas."""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self._connected = False
    
    async def connect(self):
        """Conectar ao Redis."""
        try:
            self.redis = redis.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
                decode_responses=False,  # Para suportar pickle
                retry_on_timeout=True
            )
            
            # Testar conexão
            await self.redis.ping()
            self._connected = True
            logger.info("✅ Conectado ao Redis")
            
        except Exception as e:
            logger.error(f"❌ Falha ao conectar ao Redis: {e}")
            self._connected = False
            raise
    
    async def disconnect(self):
        """Desconectar do Redis."""
        if self.redis:
            await self.redis.close()
            self._connected = False
            logger.info("Redis desconectado")
    
    async def is_connected(self) -> bool:
        """Verificar se está conectado ao Redis."""
        if not self._connected or not self.redis:
            return False
        
        try:
            await self.redis.ping()
            return True
        except:
            self._connected = False
            return False
    
    def _build_key(self, key: str) -> str:
        """Construir chave com prefixo."""
        return f"{settings.CACHE_KEY_PREFIX}:{key}"
    
    async def get(self, key: str, deserialize: str = "json") -> Optional[Any]:
        """Obter valor do Redis."""
        if not await self.is_connected():
            return None
        
        try:
            full_key = self._build_key(key)
            value = await self.redis.get(full_key)
            
            if value is None:
                return None
            
            if deserialize == "json":
                return json.loads(value)
            elif deserialize == "pickle":
                return pickle.loads(value)
            else:
                return value.decode('utf-8')
                
        except Exception as e:
            logger.error(f"Erro ao obter chave {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None,
        serialize: str = "json"
    ) -> bool:
        """Definir valor no Redis."""
        if not await self.is_connected():
            return False
        
        try:
            full_key = self._build_key(key)
            
            # Serializar valor
            if serialize == "json":
                serialized_value = json.dumps(value, default=str)
            elif serialize == "pickle":
                serialized_value = pickle.dumps(value)
            else:
                serialized_value = str(value)
            
            # Definir TTL
            if ttl is None:
                ttl = settings.CACHE_TTL_DEFAULT
            
            return await self.redis.setex(full_key, ttl, serialized_value)
            
        except Exception as e:
            logger.error(f"Erro ao definir chave {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Deletar chave do Redis."""
        if not await self.is_connected():
            return False
        
        try:
            full_key = self._build_key(key)
            result = await self.redis.delete(full_key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Erro ao deletar chave {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Deletar chaves que correspondem ao padrão."""
        if not await self.is_connected():
            return 0
        
        try:
            full_pattern = self._build_key(pattern)
            keys = await self.redis.keys(full_pattern)
            
            if keys:
                return await self.redis.delete(*keys)
            return 0
            
        except Exception as e:
            logger.error(f"Erro ao deletar padrão {pattern}: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Verificar se chave existe."""
        if not await self.is_connected():
            return False
        
        try:
            full_key = self._build_key(key)
            return await self.redis.exists(full_key) > 0
            
        except Exception as e:
            logger.error(f"Erro ao verificar chave {key}: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """Obter TTL da chave."""
        if not await self.is_connected():
            return -1
        
        try:
            full_key = self._build_key(key)
            return await self.redis.ttl(full_key)
            
        except Exception as e:
            logger.error(f"Erro ao obter TTL da chave {key}: {e}")
            return -1
    
    async def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """Incrementar valor numérico."""
        if not await self.is_connected():
            return None
        
        try:
            full_key = self._build_key(key)
            return await self.redis.incrby(full_key, amount)
            
        except Exception as e:
            logger.error(f"Erro ao incrementar chave {key}: {e}")
            return None
    
    async def expire(self, key: str, ttl: Union[int, timedelta]) -> bool:
        """Definir expiração para chave existente."""
        if not await self.is_connected():
            return False
        
        try:
            full_key = self._build_key(key)
            return await self.redis.expire(full_key, ttl)
            
        except Exception as e:
            logger.error(f"Erro ao definir expiração para chave {key}: {e}")
            return False

# Instância global
redis_client = RedisClient()
```

### Decorador para Cache de Resultados

```python
# app/core/decorators.py
import functools
import hashlib
import inspect
from typing import Any, Callable, Optional, Union
from datetime import timedelta
from app.core.cache import redis_client
from app.core.config import settings

def cache_result(
    ttl: Optional[Union[int, timedelta]] = None,
    key_prefix: Optional[str] = None,
    serialize: str = "json"
):
    """
    Decorador para cachear resultados de funções.
    
    Args:
        ttl: Tempo de vida do cache
        key_prefix: Prefixo personalizado para a chave
        serialize: Método de serialização ('json' ou 'pickle')
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            if not settings.CACHE_ENABLED:
                return await func(*args, **kwargs)
            
            # Construir chave do cache
            cache_key = _build_cache_key(func, args, kwargs, key_prefix)
            
            # Tentar obter do cache
            cached_result = await redis_client.get(cache_key, deserialize=serialize)
            if cached_result is not None:
                return cached_result
            
            # Executar função e cachear resultado
            result = await func(*args, **kwargs)
            
            if result is not None:
                cache_ttl = ttl or settings.CACHE_TTL_DEFAULT
                await redis_client.set(cache_key, result, ttl=cache_ttl, serialize=serialize)
            
            return result
        
        return wrapper
    return decorator

def invalidate_cache(patterns: Union[str, list]):
    """
    Decorador para invalidar cache após execução da função.
    
    Args:
        patterns: Padrão(ões) de chaves para invalidar
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            result = await func(*args, **kwargs)
            
            if settings.CACHE_ENABLED:
                # Invalidar padrões especificados
                if isinstance(patterns, str):
                    await redis_client.delete_pattern(patterns)
                else:
                    for pattern in patterns:
                        await redis_client.delete_pattern(pattern)
            
            return result
        
        return wrapper
    return decorator

def _build_cache_key(func: Callable, args: tuple, kwargs: dict, prefix: Optional[str] = None) -> str:
    """Construir chave única para cache baseada na função e argumentos."""
    
    # Nome da função
    func_name = f"{func.__module__}.{func.__qualname__}"
    
    # Processar argumentos
    sig = inspect.signature(func)
    bound_args = sig.bind(*args, **kwargs)
    bound_args.apply_defaults()
    
    # Criar string dos argumentos
    args_str = ""
    for param_name, param_value in bound_args.arguments.items():
        # Pular 'self' e 'cls'
        if param_name in ('self', 'cls'):
            continue
        
        # Converter valor para string
        if hasattr(param_value, 'id'):
            # Para objetos com ID (como modelos)
            value_str = f"{param_value.__class__.__name__}:{param_value.id}"
        else:
            value_str = str(param_value)
        
        args_str += f"{param_name}:{value_str}:"
    
    # Criar hash dos argumentos
    args_hash = hashlib.md5(args_str.encode()).hexdigest()[:8]
    
    # Construir chave final
    if prefix:
        return f"{prefix}:{func_name}:{args_hash}"
    else:
        return f"func:{func_name}:{args_hash}"
```

### Cache de Modelos Pydantic

```python
# app/core/model_cache.py
from typing import List, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from app.core.cache import redis_client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

class ModelCache:
    """Cache especializado para modelos Pydantic."""
    
    @staticmethod
    async def get_model(
        key: str,
        model_class: Type[T],
        ttl_refresh: bool = False
    ) -> Optional[T]:
        """
        Obter modelo do cache.
        
        Args:
            key: Chave do cache
            model_class: Classe do modelo Pydantic
            ttl_refresh: Se deve renovar TTL ao acessar
        """
        try:
            cached_data = await redis_client.get(key)
            
            if cached_data is None:
                return None
            
            # Renovar TTL se solicitado
            if ttl_refresh:
                await redis_client.expire(key, settings.CACHE_TTL_DEFAULT)
            
            # Validar e retornar modelo
            return model_class.model_validate(cached_data)
            
        except Exception as e:
            logger.error(f"Erro ao obter modelo do cache {key}: {e}")
            return None
    
    @staticmethod
    async def set_model(
        key: str,
        model: BaseModel,
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """
        Armazenar modelo no cache.
        
        Args:
            key: Chave do cache
            model: Instância do modelo Pydantic
            ttl: Tempo de vida do cache
        """
        try:
            # Converter modelo para dict
            model_data = model.model_dump()
            
            return await redis_client.set(key, model_data, ttl=ttl)
            
        except Exception as e:
            logger.error(f"Erro ao armazenar modelo no cache {key}: {e}")
            return False
    
    @staticmethod
    async def get_model_list(
        key: str,
        model_class: Type[T]
    ) -> Optional[List[T]]:
        """Obter lista de modelos do cache."""
        try:
            cached_data = await redis_client.get(key)
            
            if cached_data is None:
                return None
            
            # Validar cada item da lista
            models = []
            for item_data in cached_data:
                try:
                    model = model_class.model_validate(item_data)
                    models.append(model)
                except Exception as e:
                    logger.warning(f"Erro ao validar item da lista: {e}")
                    continue
            
            return models
            
        except Exception as e:
            logger.error(f"Erro ao obter lista do cache {key}: {e}")
            return None
    
    @staticmethod
    async def set_model_list(
        key: str,
        models: List[BaseModel],
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Armazenar lista de modelos no cache."""
        try:
            # Converter modelos para lista de dicts
            models_data = [model.model_dump() for model in models]
            
            return await redis_client.set(key, models_data, ttl=ttl)
            
        except Exception as e:
            logger.error(f"Erro ao armazenar lista no cache {key}: {e}")
            return False
    
    @staticmethod
    async def invalidate_model(model_id: Union[int, str], model_name: str):
        """Invalidar cache de um modelo específico."""
        patterns = [
            f"{model_name}:{model_id}",
            f"{model_name}:*:{model_id}",
            f"list:{model_name}:*"
        ]
        
        for pattern in patterns:
            await redis_client.delete_pattern(pattern)
```

### Implementação em Services

```python
# app/services/user_service.py
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.repositories.user_repository import UserRepository
from app.core.decorators import cache_result, invalidate_cache
from app.core.model_cache import ModelCache
from app.core.config import settings

class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = UserRepository(db)
    
    @cache_result(ttl=settings.CACHE_TTL_USER, key_prefix="user")
    async def get_user_by_id(self, user_id: int) -> Optional[UserResponse]:
        """Obter usuário por ID com cache."""
        user = await self.repository.get_by_id(user_id)
        
        if user:
            return UserResponse.model_validate(user)
        return None
    
    @cache_result(ttl=settings.CACHE_TTL_USER, key_prefix="user_email")
    async def get_user_by_email(self, email: str) -> Optional[UserResponse]:
        """Obter usuário por email com cache."""
        user = await self.repository.get_by_email(email)
        
        if user:
            return UserResponse.model_validate(user)
        return None
    
    @cache_result(ttl=settings.CACHE_TTL_SEARCH, key_prefix="user_search")
    async def search_users(
        self,
        query: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[UserResponse]:
        """Buscar usuários com cache."""
        users = await self.repository.search(query, limit, offset)
        
        return [UserResponse.model_validate(user) for user in users]
    
    @invalidate_cache(["user:*", "user_email:*", "user_search:*"])
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Criar usuário e invalidar cache."""
        user = await self.repository.create(user_data)
        user_response = UserResponse.model_validate(user)
        
        # Cachear o novo usuário
        await ModelCache.set_model(
            f"user:{user.id}",
            user_response,
            ttl=settings.CACHE_TTL_USER
        )
        
        return user_response
    
    @invalidate_cache(["user:*", "user_email:*", "user_search:*"])
    async def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[UserResponse]:
        """Atualizar usuário e invalidar cache."""
        user = await self.repository.update(user_id, user_data)
        
        if user:
            user_response = UserResponse.model_validate(user)
            
            # Atualizar cache
            await ModelCache.set_model(
                f"user:{user.id}",
                user_response,
                ttl=settings.CACHE_TTL_USER
            )
            
            return user_response
        return None
    
    @invalidate_cache(["user:*", "user_email:*", "user_search:*"])
    async def delete_user(self, user_id: int) -> bool:
        """Deletar usuário e invalidar cache."""
        return await self.repository.delete(user_id)
```

### Cache para Queries Complexas

```python
# app/services/analytics_service.py
from typing import Dict, List, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.decorators import cache_result
from app.core.config import settings

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
    
    @cache_result(ttl=3600, key_prefix="analytics_daily")  # Cache por 1 hora
    async def get_daily_stats(self, date: datetime) -> Dict[str, Any]:
        """Estatísticas diárias com cache."""
        # Query complexa que demora para executar
        query = """
        SELECT 
            COUNT(DISTINCT u.id) as active_users,
            COUNT(o.id) as total_orders,
            SUM(o.total_amount) as total_revenue,
            AVG(o.total_amount) as avg_order_value
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id 
            AND DATE(o.created_at) = :date
        WHERE u.last_login >= :date
        """
        
        result = await self.db.execute(query, {"date": date.date()})
        row = result.first()
        
        return {
            "date": date.date(),
            "active_users": row.active_users or 0,
            "total_orders": row.total_orders or 0,
            "total_revenue": float(row.total_revenue or 0),
            "avg_order_value": float(row.avg_order_value or 0)
        }
    
    @cache_result(ttl=7200, key_prefix="analytics_popular")  # Cache por 2 horas
    async def get_popular_items(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Itens mais populares com cache."""
        query = """
        SELECT 
            i.id,
            i.name,
            i.price,
            COUNT(oi.id) as order_count,
            SUM(oi.quantity) as total_quantity
        FROM items i
        JOIN order_items oi ON i.id = oi.item_id
        JOIN orders o ON oi.order_id = o.id
        WHERE o.created_at >= NOW() - INTERVAL '30 days'
        GROUP BY i.id, i.name, i.price
        ORDER BY order_count DESC, total_quantity DESC
        LIMIT :limit
        """
        
        result = await self.db.execute(query, {"limit": limit})
        
        return [
            {
                "id": row.id,
                "name": row.name,
                "price": float(row.price),
                "order_count": row.order_count,
                "total_quantity": row.total_quantity
            }
            for row in result
        ]
    
    @cache_result(ttl=1800, key_prefix="analytics_segments")  # Cache por 30 min
    async def get_user_segments(self) -> Dict[str, int]:
        """Segmentação de usuários com cache."""
        query = """
        SELECT 
            CASE 
                WHEN total_spent >= 1000 THEN 'premium'
                WHEN total_spent >= 500 THEN 'regular'
                WHEN total_spent > 0 THEN 'occasional'
                ELSE 'inactive'
            END as segment,
            COUNT(*) as user_count
        FROM (
            SELECT 
                u.id,
                COALESCE(SUM(o.total_amount), 0) as total_spent
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id
            GROUP BY u.id
        ) user_totals
        GROUP BY segment
        """
        
        result = await self.db.execute(query)
        
        return {row.segment: row.user_count for row in result}
```

### Middleware de Cache HTTP

```python
# app/middleware/http_cache_middleware.py
import hashlib
import json
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.core.cache import redis_client
from app.core.config import settings

class HTTPCacheMiddleware(BaseHTTPMiddleware):
    """Middleware para cache de respostas HTTP."""
    
    def __init__(
        self,
        app,
        default_ttl: int = 300,  # 5 minutos
        cache_methods: list = None,
        cache_status_codes: list = None
    ):
        super().__init__(app)
        self.default_ttl = default_ttl
        self.cache_methods = cache_methods or ["GET"]
        self.cache_status_codes = cache_status_codes or [200, 201]
    
    async def dispatch(self, request: Request, call_next):
        # Verificar se deve cachear
        if not self._should_cache_request(request):
            return await call_next(request)
        
        # Gerar chave do cache
        cache_key = self._generate_cache_key(request)
        
        # Tentar obter resposta do cache
        cached_response = await self._get_cached_response(cache_key)
        if cached_response:
            return cached_response
        
        # Executar request
        response = await call_next(request)
        
        # Cachear resposta se apropriado
        if self._should_cache_response(response):
            await self._cache_response(cache_key, response)
        
        return response
    
    def _should_cache_request(self, request: Request) -> bool:
        """Verificar se deve cachear o request."""
        # Só cachear métodos específicos
        if request.method not in self.cache_methods:
            return False
        
        # Não cachear se tiver parâmetros de cache
        if "no-cache" in request.headers.get("cache-control", ""):
            return False
        
        # Não cachear requests autenticados (opcional)
        if request.headers.get("authorization"):
            return False
        
        return True
    
    def _should_cache_response(self, response: Response) -> bool:
        """Verificar se deve cachear a resposta."""
        return response.status_code in self.cache_status_codes
    
    def _generate_cache_key(self, request: Request) -> str:
        """Gerar chave única para o request."""
        # Incluir método, path e query parameters
        key_parts = [
            request.method,
            str(request.url.path),
            str(request.url.query)
        ]
        
        # Incluir headers relevantes
        relevant_headers = ["accept", "accept-language", "user-agent"]
        for header in relevant_headers:
            if header in request.headers:
                key_parts.append(f"{header}:{request.headers[header]}")
        
        # Criar hash
        key_string = "|".join(key_parts)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"http_cache:{key_hash}"
    
    async def _get_cached_response(self, cache_key: str) -> Optional[Response]:
        """Obter resposta do cache."""
        try:
            cached_data = await redis_client.get(cache_key)
            
            if cached_data is None:
                return None
            
            # Reconstruir resposta
            response_data = json.loads(cached_data)
            
            response = JSONResponse(
                content=response_data["content"],
                status_code=response_data["status_code"],
                headers=response_data["headers"]
            )
            
            # Adicionar header indicando cache hit
            response.headers["X-Cache"] = "HIT"
            
            return response
            
        except Exception as e:
            # Log erro mas não falhe
            print(f"Erro ao obter resposta do cache: {e}")
            return None
    
    async def _cache_response(self, cache_key: str, response: Response):
        """Cachear resposta."""
        try:
            # Ler conteúdo da resposta
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            # Recriar iterator
            response.body_iterator = self._create_body_iterator(body)
            
            # Preparar dados para cache
            response_data = {
                "content": json.loads(body.decode()) if body else None,
                "status_code": response.status_code,
                "headers": dict(response.headers)
            }
            
            # Cachear
            await redis_client.set(
                cache_key,
                json.dumps(response_data),
                ttl=self.default_ttl
            )
            
            # Adicionar header indicando cache miss
            response.headers["X-Cache"] = "MISS"
            
        except Exception as e:
            # Log erro mas não falhe
            print(f"Erro ao cachear resposta: {e}")
    
    def _create_body_iterator(self, body: bytes):
        """Criar iterator para o corpo da resposta."""
        yield body
```

### Configuração no FastAPI

```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.cache import redis_client
from app.middleware.http_cache_middleware import HTTPCacheMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await redis_client.connect()
    yield
    # Shutdown
    await redis_client.disconnect()

app = FastAPI(lifespan=lifespan)

# Adicionar middleware de cache HTTP
app.add_middleware(
    HTTPCacheMiddleware,
    default_ttl=300,  # 5 minutos
    cache_methods=["GET"],
    cache_status_codes=[200, 201]
)
```

---

## 🚀 Otimização de Performance e Monitoramento

### Profiling de Queries de Banco de Dados

```python
# app/middleware/database_profiling_middleware.py
import time
import logging
from typing import Dict, List, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import event
from sqlalchemy.engine import Engine
from collections import defaultdict
import re

logger = logging.getLogger(__name__)

class DatabaseProfilingMiddleware(BaseHTTPMiddleware):
    """Middleware para monitorar performance de queries do banco."""
    
    def __init__(self, app, slow_query_threshold: float = 0.1):
        super().__init__(app)
        self.slow_query_threshold = slow_query_threshold
        self.query_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'avg_time': 0.0,
            'min_time': float('inf'),
            'max_time': 0.0,
            'times': []
        })
        
        # Registrar eventos do SQLAlchemy
        self._setup_sqlalchemy_events()
    
    def _setup_sqlalchemy_events(self):
        """Configurar eventos do SQLAlchemy para capturar queries."""
        
        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
        
        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total_time = time.time() - context._query_start_time
            
            # Normalizar query (remover valores específicos)
            normalized_query = self._normalize_query(statement)
            
            # Atualizar estatísticas
            stats = self.query_stats[normalized_query]
            stats['count'] += 1
            stats['total_time'] += total_time
            stats['times'].append(total_time)
            stats['min_time'] = min(stats['min_time'], total_time)
            stats['max_time'] = max(stats['max_time'], total_time)
            stats['avg_time'] = stats['total_time'] / stats['count']
            
            # Calcular mediana
            sorted_times = sorted(stats['times'])
            n = len(sorted_times)
            if n % 2 == 0:
                stats['median_time'] = (sorted_times[n//2-1] + sorted_times[n//2]) / 2
            else:
                stats['median_time'] = sorted_times[n//2]
            
            # Log queries lentas
            if total_time > self.slow_query_threshold:
                logger.warning(
                    f"Slow query detected: {total_time:.3f}s\n"
                    f"Query: {statement[:200]}..."
                )
    
    def _normalize_query(self, query: str) -> str:
        """Normalizar query removendo valores específicos."""
        # Remover valores literais
        normalized = re.sub(r"'[^']*'", "'?'", query)
        normalized = re.sub(r'\b\d+\b', '?', normalized)
        
        # Remover espaços extras e quebras de linha
        normalized = re.sub(r'\s+', ' ', normalized.strip())
        
        return normalized
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        total_time = time.time() - start_time
        
        # Adicionar headers de performance
        response.headers["X-Response-Time"] = f"{total_time:.3f}s"
        
        return response
    
    def get_query_stats(self) -> Dict[str, Any]:
        """Obter estatísticas das queries."""
        return dict(self.query_stats)
    
    def reset_stats(self):
        """Resetar estatísticas."""
        self.query_stats.clear()
```

### Otimização de Queries com Índices

```python
# app/models/optimized_models.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Index, Text
from sqlalchemy.orm import relationship
from app.models.base import Base

class OptimizedUser(Base):
    """Modelo User otimizado com índices."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100), index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, index=True)
    last_login = Column(DateTime, index=True)
    
    # Relacionamentos
    orders = relationship("OptimizedOrder", back_populates="user")
    
    # Índices compostos para queries comuns
    __table_args__ = (
        # Índice para buscar usuários ativos criados recentemente
        Index('idx_users_active_created', 'is_active', 'created_at'),
        
        # Índice para buscar por nome completo e email
        Index('idx_users_search', 'full_name', 'email'),
        
        # Índice para ordenação por último login
        Index('idx_users_last_login', 'last_login', 'is_active'),
    )

class OptimizedOrder(Base):
    """Modelo Order otimizado com índices."""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    status = Column(String(20), index=True)
    total_amount = Column(Integer)  # Em centavos
    created_at = Column(DateTime, index=True)
    updated_at = Column(DateTime, index=True)
    
    # Relacionamentos
    user = relationship("OptimizedUser", back_populates="orders")
    
    # Índices compostos
    __table_args__ = (
        # Índice para buscar pedidos por usuário e data
        Index('idx_orders_user_date', 'user_id', 'created_at'),
        
        # Índice para relatórios de status
        Index('idx_orders_status_date', 'status', 'created_at'),
        
        # Índice para análise de receita
        Index('idx_orders_amount_date', 'total_amount', 'created_at'),
    )
```

### Repository Otimizado

```python
# app/repositories/optimized_user_repository.py
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import func, and_, or_, desc
from app.models.optimized_models import OptimizedUser, OptimizedOrder
from app.schemas.user import UserCreate, UserUpdate

class OptimizedUserRepository:
    """Repository otimizado para operações de usuário."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_active_users_with_orders(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[OptimizedUser]:
        """
        Buscar usuários ativos com seus pedidos.
        Usa selectinload para evitar problema N+1.
        """
        return (
            self.db.query(OptimizedUser)
            .options(selectinload(OptimizedUser.orders))
            .filter(OptimizedUser.is_active == True)
            .order_by(desc(OptimizedUser.last_login))
            .offset(offset)
            .limit(limit)
            .all()
        )
    
    async def search_users_optimized(
        self,
        query: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[OptimizedUser]:
        """
        Busca otimizada de usuários usando índices.
        Aproveita o índice idx_users_search.
        """
        search_filter = or_(
            OptimizedUser.full_name.ilike(f"%{query}%"),
            OptimizedUser.email.ilike(f"%{query}%"),
            OptimizedUser.username.ilike(f"%{query}%")
        )
        
        return (
            self.db.query(OptimizedUser)
            .filter(
                and_(
                    OptimizedUser.is_active == True,
                    search_filter
                )
            )
            .order_by(OptimizedUser.full_name)
            .offset(offset)
            .limit(limit)
            .all()
        )
    
    async def get_user_statistics(self) -> Dict[str, Any]:
        """
        Obter estatísticas agregadas de usuários.
        Usa queries otimizadas com agregação.
        """
        # Query única para múltiplas estatísticas
        stats = (
            self.db.query(
                func.count(OptimizedUser.id).label('total_users'),
                func.count(
                    func.nullif(OptimizedUser.is_active, False)
                ).label('active_users'),
                func.count(
                    func.nullif(OptimizedUser.last_login, None)
                ).label('users_with_login'),
                func.avg(
                    func.extract('epoch', 
                        func.now() - OptimizedUser.created_at
                    ) / 86400
                ).label('avg_days_since_creation')
            )
            .first()
        )
        
        return {
            'total_users': stats.total_users,
            'active_users': stats.active_users,
            'inactive_users': stats.total_users - stats.active_users,
            'users_with_login': stats.users_with_login,
            'avg_days_since_creation': float(stats.avg_days_since_creation or 0)
        }

class OptimizedOrderRepository:
    """Repository otimizado para operações de pedidos."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_orders_with_pagination(
        self,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[OptimizedOrder]:
        """
        Buscar pedidos com paginação otimizada.
        Usa joinedload para carregar usuário em uma query.
        """
        query = (
            self.db.query(OptimizedOrder)
            .options(joinedload(OptimizedOrder.user))
        )
        
        # Aplicar filtros usando índices
        if user_id:
            query = query.filter(OptimizedOrder.user_id == user_id)
        
        if status:
            query = query.filter(OptimizedOrder.status == status)
        
        return (
            query
            .order_by(desc(OptimizedOrder.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )
    
    async def get_revenue_report_by_period(
        self,
        start_date: datetime,
        end_date: datetime,
        group_by: str = "day"  # day, week, month
    ) -> List[Dict[str, Any]]:
        """
        Relatório de receita por período com agregação otimizada.
        Aproveita o índice idx_orders_amount_date.
        """
        # Definir formato de agrupamento
        date_formats = {
            "day": func.date(OptimizedOrder.created_at),
            "week": func.date_trunc('week', OptimizedOrder.created_at),
            "month": func.date_trunc('month', OptimizedOrder.created_at)
        }
        
        date_group = date_formats.get(group_by, date_formats["day"])
        
        results = (
            self.db.query(
                date_group.label('period'),
                func.count(OptimizedOrder.id).label('order_count'),
                func.sum(OptimizedOrder.total_amount).label('total_revenue'),
                func.avg(OptimizedOrder.total_amount).label('avg_order_value'),
                func.count(func.distinct(OptimizedOrder.user_id)).label('unique_customers')
            )
            .filter(
                and_(
                    OptimizedOrder.created_at >= start_date,
                    OptimizedOrder.created_at <= end_date
                )
            )
            .group_by(date_group)
            .order_by(date_group)
            .all()
        )
        
        return [
            {
                'period': result.period,
                'order_count': result.order_count,
                'total_revenue': float(result.total_revenue or 0) / 100,  # Converter de centavos
                'avg_order_value': float(result.avg_order_value or 0) / 100,
                'unique_customers': result.unique_customers
            }
            for result in results
        ]
```

### Middleware de Compressão

```python
# app/middleware/compression_middleware.py
import gzip
import brotli
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

class CompressionMiddleware(BaseHTTPMiddleware):
    """Middleware para compressão de respostas HTTP."""
    
    def __init__(
        self,
        app,
        minimum_size: int = 500,  # Tamanho mínimo para compressão
        compressible_types: list = None
    ):
        super().__init__(app)
        self.minimum_size = minimum_size
        self.compressible_types = compressible_types or [
            "application/json",
            "application/javascript",
            "text/css",
            "text/html",
            "text/plain",
            "text/xml",
            "application/xml"
        ]
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Verificar se deve comprimir
        if not self._should_compress(request, response):
            return response
        
        # Obter método de compressão preferido
        compression_method = self._get_compression_method(request)
        
        if not compression_method:
            return response
        
        # Comprimir resposta
        compressed_response = await self._compress_response(response, compression_method)
        
        return compressed_response
    
    def _should_compress(self, request: Request, response: Response) -> bool:
        """Verificar se deve comprimir a resposta."""
        
        # Verificar se já está comprimida
        if response.headers.get("content-encoding"):
            return False
        
        # Verificar tipo de conteúdo
        content_type = response.headers.get("content-type", "").split(";")[0]
        if content_type not in self.compressible_types:
            return False
        
        # Verificar tamanho mínimo
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) < self.minimum_size:
            return False
        
        return True
    
    def _get_compression_method(self, request: Request) -> Optional[str]:
        """Obter método de compressão baseado no Accept-Encoding."""
        accept_encoding = request.headers.get("accept-encoding", "")
        
        # Priorizar brotli se disponível
        if "br" in accept_encoding:
            return "br"
        elif "gzip" in accept_encoding:
            return "gzip"
        
        return None
    
    async def _compress_response(self, response: Response, method: str) -> Response:
        """Comprimir o conteúdo da resposta."""
        
        # Ler conteúdo da resposta
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        
        # Verificar tamanho mínimo
        if len(body) < self.minimum_size:
            # Recriar response original
            response.body_iterator = self._create_body_iterator(body)
            return response
        
        # Comprimir baseado no método
        if method == "gzip":
            compressed_body = gzip.compress(body)
            encoding = "gzip"
        elif method == "br":
            compressed_body = brotli.compress(body)
            encoding = "br"
        else:
            # Fallback para não comprimido
            response.body_iterator = self._create_body_iterator(body)
            return response
        
        # Verificar se compressão foi eficiente
        compression_ratio = len(compressed_body) / len(body)
        if compression_ratio > 0.9:  # Menos de 10% de economia
            response.body_iterator = self._create_body_iterator(body)
            return response
        
        # Criar nova resposta comprimida
        compressed_response = StarletteResponse(
            content=compressed_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        )
        
        # Atualizar headers
        compressed_response.headers["content-encoding"] = encoding
        compressed_response.headers["content-length"] = str(len(compressed_body))
        compressed_response.headers["vary"] = "Accept-Encoding"
        
        return compressed_response
    
    def _create_body_iterator(self, body: bytes):
        """Criar iterator para o corpo da resposta."""
        yield body
```

### Rate Limiting

```python
# app/middleware/rate_limit_middleware.py
import time
import json
from typing import Dict, Optional, Tuple
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.cache import redis_client
import hashlib

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware para rate limiting usando sliding window."""
    
    def __init__(
        self,
        app,
        default_requests: int = 100,
        default_window: int = 3600,  # 1 hora
        per_endpoint_limits: Dict[str, Tuple[int, int]] = None
    ):
        super().__init__(app)
        self.default_requests = default_requests
        self.default_window = default_window
        self.per_endpoint_limits = per_endpoint_limits or {}
    
    async def dispatch(self, request: Request, call_next):
        # Obter identificador do cliente
        client_id = await self._get_client_id(request)
        
        # Obter limites para o endpoint
        endpoint = f"{request.method}:{request.url.path}"
        requests_limit, window_size = self.per_endpoint_limits.get(
            endpoint, 
            (self.default_requests, self.default_window)
        )
        
        # Verificar rate limit
        allowed, remaining, reset_time = await self._check_rate_limit(
            client_id, endpoint, requests_limit, window_size
        )
        
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(requests_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                    "Retry-After": str(int(reset_time - time.time()))
                }
            )
        
        # Processar request
        response = await call_next(request)
        
        # Adicionar headers de rate limit
        response.headers["X-RateLimit-Limit"] = str(requests_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response
    
    async def _get_client_id(self, request: Request) -> str:
        """Obter identificador único do cliente."""
        
        # Tentar obter user ID do JWT
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                # Aqui você decodificaria o JWT para obter o user_id
                # Por simplicidade, vamos usar um hash do token
                token = auth_header.split(" ")[1]
                user_hash = hashlib.md5(token.encode()).hexdigest()[:8]
                return f"user:{user_hash}"
            except:
                pass
        
        # Fallback para IP
        client_ip = request.client.host
        return f"ip:{client_ip}"
    
    async def _check_rate_limit(
        self,
        client_id: str,
        endpoint: str,
        requests_limit: int,
        window_size: int
    ) -> Tuple[bool, int, int]:
        """
        Verificar rate limit usando sliding window.
        
        Returns:
            (allowed, remaining_requests, reset_timestamp)
        """
        current_time = int(time.time())
        window_start = current_time - window_size
        
        # Chave do Redis
        key = f"rate_limit:{client_id}:{endpoint}"
        
        try:
            # Obter requests no window atual
            requests_data = await redis_client.get(key)
            
            if requests_data is None:
                requests = []
            else:
                requests = json.loads(requests_data)
            
            # Filtrar requests dentro do window
            recent_requests = [
                req_time for req_time in requests 
                if req_time > window_start
            ]
            
            # Verificar se excedeu o limite
            if len(recent_requests) >= requests_limit:
                # Calcular quando o rate limit será resetado
                oldest_request = min(recent_requests)
                reset_time = oldest_request + window_size
                return False, 0, reset_time
            
            # Adicionar request atual
            recent_requests.append(current_time)
            
            # Salvar no Redis
            await redis_client.set(
                key,
                json.dumps(recent_requests),
                ttl=window_size
            )
            
            remaining = requests_limit - len(recent_requests)
            reset_time = current_time + window_size
            
            return True, remaining, reset_time
            
        except Exception as e:
            # Em caso de erro, permitir o request
            print(f"Rate limit error: {e}")
            return True, requests_limit, current_time + window_size

# Decorador para rate limiting específico por endpoint
def endpoint_rate_limit(requests: int, window: int):
    """
    Decorador para aplicar rate limiting específico a um endpoint.
    
    Args:
        requests: Número de requests permitidos
        window: Janela de tempo em segundos
    """
    def decorator(func):
        func._rate_limit = (requests, window)
        return func
    return decorator
```

### Sistema de Métricas e Monitoramento

```python
# app/monitoring/metrics.py
import time
import psutil
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from app.core.cache import redis_client
import asyncio

@dataclass
class PerformanceMetrics:
    """Estrutura para métricas de performance."""
    timestamp: float
    
    # Métricas do sistema
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    
    # Métricas da aplicação
    active_requests: int
    requests_per_second: float
    avg_response_time: float
    error_rate: float
    uptime_seconds: float
    
    # Métricas do cache
    cache_hit_rate: float
    cache_memory_usage: int
    cache_connected_clients: int
    
    # Métricas do banco de dados
    db_connections: int
    db_slow_queries: int
    db_avg_query_time: float

class MetricsCollector:
    """Coletor de métricas do sistema e aplicação."""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.response_times = []
        self.last_network_stats = psutil.net_io_counters()
    
    async def collect_metrics(self) -> PerformanceMetrics:
        """Coletar todas as métricas."""
        
        # Métricas do sistema
        system_metrics = await self._collect_system_metrics()
        
        # Métricas da aplicação
        app_metrics = await self._collect_app_metrics()
        
        # Métricas do cache
        cache_metrics = await self._collect_cache_metrics()
        
        # Métricas do banco (simuladas - implementar conforme seu setup)
        db_metrics = await self._collect_db_metrics()
        
        return PerformanceMetrics(
            timestamp=time.time(),
            **system_metrics,
            **app_metrics,
            **cache_metrics,
            **db_metrics
        )
    
    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Coletar métricas do sistema."""
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memória
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Disco
        disk = psutil.disk_usage('/')
        disk_usage_percent = (disk.used / disk.total) * 100
        
        # Rede
        network_stats = psutil.net_io_counters()
        network_bytes_sent = network_stats.bytes_sent - self.last_network_stats.bytes_sent
        network_bytes_recv = network_stats.bytes_recv - self.last_network_stats.bytes_recv
        self.last_network_stats = network_stats
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'disk_usage_percent': disk_usage_percent,
            'network_bytes_sent': network_bytes_sent,
            'network_bytes_recv': network_bytes_recv
        }
    
    async def _collect_app_metrics(self) -> Dict[str, Any]:
        """Coletar métricas da aplicação."""
        
        current_time = time.time()
        uptime = current_time - self.start_time
        
        # Calcular RPS (requests por segundo)
        rps = self.request_count / max(uptime, 1)
        
        # Calcular tempo médio de resposta
        avg_response_time = (
            sum(self.response_times) / len(self.response_times)
            if self.response_times else 0
        )
        
        # Calcular taxa de erro
        error_rate = (
            (self.error_count / self.request_count) * 100
            if self.request_count > 0 else 0
        )
        
        return {
            'active_requests': 0,  # Implementar contador de requests ativos
            'requests_per_second': rps,
            'avg_response_time': avg_response_time,
            'error_rate': error_rate,
            'uptime_seconds': uptime
        }
    
    async def _collect_cache_metrics(self) -> Dict[str, Any]:
        """Coletar métricas do cache Redis."""
        
        try:
            if await redis_client.is_connected():
                # Obter informações do Redis
                info = await redis_client.redis.info()
                
                # Calcular hit rate
                hits = info.get('keyspace_hits', 0)
                misses = info.get('keyspace_misses', 0)
                total_requests = hits + misses
                hit_rate = (hits / total_requests * 100) if total_requests > 0 else 0
                
                return {
                    'cache_hit_rate': hit_rate,
                    'cache_memory_usage': info.get('used_memory', 0),
                    'cache_connected_clients': info.get('connected_clients', 0)
                }
            else:
                return {
                    'cache_hit_rate': 0,
                    'cache_memory_usage': 0,
                    'cache_connected_clients': 0
                }
        except Exception as e:
            print(f"Error collecting cache metrics: {e}")
            return {
                'cache_hit_rate': 0,
                'cache_memory_usage': 0,
                'cache_connected_clients': 0
            }
    
    async def _collect_db_metrics(self) -> Dict[str, Any]:
        """Coletar métricas do banco de dados."""
        
        # Implementar baseado no seu setup de banco
        # Por enquanto, retornar valores simulados
        return {
            'db_connections': 5,
            'db_slow_queries': 0,
            'db_avg_query_time': 0.05
        }
    
    def record_request(self, response_time: float, is_error: bool = False):
        """Registrar uma requisição."""
        self.request_count += 1
        self.response_times.append(response_time)
        
        if is_error:
            self.error_count += 1
        
        # Manter apenas os últimos 1000 tempos de resposta
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]

# Instância global
metrics_collector = MetricsCollector()
```

### Middleware de Métricas

```python
# app/middleware/metrics_middleware.py
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.monitoring.metrics import metrics_collector

class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware para coletar métricas de requests."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Calcular tempo de resposta
            response_time = time.time() - start_time
            
            # Verificar se é erro
            is_error = response.status_code >= 400
            
            # Registrar métricas
            metrics_collector.record_request(response_time, is_error)
            
            return response
            
        except Exception as e:
            # Registrar como erro
            response_time = time.time() - start_time
            metrics_collector.record_request(response_time, is_error=True)
            raise
```

### API de Monitoramento

```python
# app/api/monitoring.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.monitoring.metrics import metrics_collector, PerformanceMetrics
import asyncio

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Obter métricas atuais do sistema."""
    
    try:
        metrics = await metrics_collector.collect_metrics()
        return asdict(metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error collecting metrics: {e}")

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Verificação detalhada de saúde do sistema."""
    
    metrics = await metrics_collector.collect_metrics()
    
    # Determinar status baseado nas métricas
    status = "healthy"
    issues = []
    
    # Verificar CPU
    if metrics.cpu_percent > 80:
        status = "warning"
        issues.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")
    
    # Verificar memória
    if metrics.memory_percent > 85:
        status = "critical" if metrics.memory_percent > 95 else "warning"
        issues.append(f"High memory usage: {metrics.memory_percent:.1f}%")
    
    # Verificar taxa de erro
    if metrics.error_rate > 5:
        status = "critical" if metrics.error_rate > 10 else "warning"
        issues.append(f"High error rate: {metrics.error_rate:.1f}%")
    
    # Verificar tempo de resposta
    if metrics.avg_response_time > 1.0:
        status = "warning"
        issues.append(f"Slow response time: {metrics.avg_response_time:.3f}s")
    
    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": metrics.uptime_seconds,
        "issues": issues,
        "metrics": asdict(metrics)
    }

@router.get("/alerts")
async def get_alerts() -> List[Dict[str, Any]]:
    """Obter alertas baseados nas métricas."""
    
    metrics = await metrics_collector.collect_metrics()
    alerts = []
    
    # Alertas críticos
    if metrics.cpu_percent > 90:
        alerts.append({
            "level": "critical",
            "message": f"CPU usage is critically high: {metrics.cpu_percent:.1f}%",
            "metric": "cpu_percent",
            "value": metrics.cpu_percent,
            "threshold": 90
        })
    
    if metrics.memory_percent > 95:
        alerts.append({
            "level": "critical",
            "message": f"Memory usage is critically high: {metrics.memory_percent:.1f}%",
            "metric": "memory_percent",
            "value": metrics.memory_percent,
            "threshold": 95
        })
    
    if metrics.error_rate > 10:
        alerts.append({
            "level": "critical",
            "message": f"Error rate is critically high: {metrics.error_rate:.1f}%",
            "metric": "error_rate",
            "value": metrics.error_rate,
            "threshold": 10
        })
    
    # Alertas de warning
    if 80 <= metrics.cpu_percent <= 90:
        alerts.append({
            "level": "warning",
            "message": f"CPU usage is high: {metrics.cpu_percent:.1f}%",
            "metric": "cpu_percent",
            "value": metrics.cpu_percent,
            "threshold": 80
        })
    
    if 85 <= metrics.memory_percent <= 95:
        alerts.append({
            "level": "warning",
            "message": f"Memory usage is high: {metrics.memory_percent:.1f}%",
            "metric": "memory_percent",
            "value": metrics.memory_percent,
            "threshold": 85
        })
    
    if metrics.avg_response_time > 1.0:
        alerts.append({
            "level": "warning",
            "message": f"Average response time is slow: {metrics.avg_response_time:.3f}s",
            "metric": "avg_response_time",
            "value": metrics.avg_response_time,
            "threshold": 1.0
        })
    
    return alerts
```

---

## 📊 Resumo do Step 5

Neste step, implementamos um sistema completo de **Cache e Otimização de Performance**:

### ✅ O que foi coberto:

1. **Conceitos Fundamentais de Cache**
   - Tipos de cache (in-memory, distribuído, database, CDN)
   - Estratégias de cache (Cache-Aside, Write-Through, Write-Behind, Refresh-Ahead)
   - Padrões de invalidação (TTL, manual, cache tags)
   - Algoritmos de eviction (LRU, LFU, FIFO, Random)
   - Problemas comuns (Cache Stampede, Hot Keys, Cache Penetration)

2. **Implementação Prática com Redis**
   - Configuração completa do Redis com Docker
   - Cliente Redis assíncrono com funcionalidades avançadas
   - Decoradores para cache automático de funções
   - Cache especializado para modelos Pydantic
   - Middleware de cache HTTP

3. **Otimização de Performance**
   - Profiling de queries de banco de dados
   - Índices compostos para otimização de queries
   - Compressão de respostas HTTP (gzip/brotli)
   - Rate limiting com sliding window
   - Sistema de métricas e monitoramento

4. **Monitoramento e Observabilidade**
   - Coleta de métricas do sistema, aplicação e cache
   - Dashboard de saúde da aplicação
   - Sistema de alertas baseado em thresholds
   - APIs para monitoramento em tempo real

### 🎯 Próximos passos:

No **Step 6**, vamos implementar **WebSockets e Comunicação em Tempo Real** para criar funcionalidades interativas e colaborativas.

---
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment a key's value."""
        try:
            return await self.redis.incr(key, amount)
        except Exception as e:
            print(f"Redis INCR error: {e}")
            return 0
    
    async def get_pattern(self, pattern: str) -> list:
        """Get all keys matching a pattern."""
        try:
            keys = await self.redis.keys(pattern)
            return [key.decode('utf-8') if isinstance(key, bytes) else key for key in keys]
        except Exception as e:
            print(f"Redis KEYS error: {e}")
            return []
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        try:
            keys = await self.get_pattern(pattern)
            if keys:
                return await self.delete(*keys)
            return 0
        except Exception as e:
            print(f"Redis DELETE_PATTERN error: {e}")
            return 0

# Instância global
redis_client = RedisClient()

# Dependency para FastAPI
async def get_redis() -> RedisClient:
    return redis_client
```

### Configuração no Settings (core/config.py)

```python
class Settings(BaseSettings):
    # ... outras configurações ...
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600  # 1 hora
    REDIS_SESSION_TTL: int = 86400  # 24 horas
    
    # Cache
    ENABLE_CACHE: bool = True
    CACHE_DEFAULT_TTL: int = 300  # 5 minutos
    CACHE_MAX_SIZE: int = 1000
```

---

## 🎯 Sistema de Cache

### Cache Manager (core/cache.py)

```python
from typing import Optional, Any, Callable, Union
from datetime import timedelta
import hashlib
import inspect
from functools import wraps
from core.redis import redis_client
from core.config import settings

class CacheManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.default_ttl = settings.CACHE_DEFAULT_TTL
    
    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a unique cache key."""
        # Criar string única baseada nos argumentos
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        # Hash para evitar keys muito longas
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"cache:{prefix}:{key_hash}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not settings.ENABLE_CACHE:
            return None
        return await self.redis.get(key)
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache."""
        if not settings.ENABLE_CACHE:
            return False
        
        expire_time = ttl or self.default_ttl
        return await self.redis.set(key, value, expire=expire_time)
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        return bool(await self.redis.delete(key))
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all cache keys matching pattern."""
        return await self.redis.delete_pattern(f"cache:{pattern}*")
    
    def cache_result(
        self, 
        prefix: str, 
        ttl: Optional[int] = None,
        key_builder: Optional[Callable] = None
    ):
        """Decorator to cache function results."""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Gerar chave do cache
                if key_builder:
                    cache_key = key_builder(*args, **kwargs)
                else:
                    cache_key = self._generate_cache_key(prefix, *args, **kwargs)
                
                # Tentar obter do cache
                cached_result = await self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Executar função e cachear resultado
                result = await func(*args, **kwargs)
                await self.set(cache_key, result, ttl)
                return result
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Para funções síncronas, usar versão assíncrona internamente
                import asyncio
                return asyncio.run(async_wrapper(*args, **kwargs))
            
            # Retornar wrapper apropriado baseado no tipo da função
            if inspect.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator

# Instância global
cache_manager = CacheManager(redis_client)
```

### Cache de Repository (db/repository/cached_repository.py)

```python
from typing import Optional, List, Any, Dict
from sqlalchemy.orm import Session
from core.cache import cache_manager
from db.repository.base import BaseRepository

class CachedRepository(BaseRepository):
    """Repository base with caching capabilities."""
    
    def __init__(self, db: Session, model, cache_prefix: str):
        super().__init__(db, model)
        self.cache_prefix = cache_prefix
        self.cache_ttl = 300  # 5 minutos
    
    async def get_cached(self, id: Any) -> Optional[Any]:
        """Get object by ID with caching."""
        cache_key = f"{self.cache_prefix}:get:{id}"
        
        # Tentar cache primeiro
        cached_obj = await cache_manager.get(cache_key)
        if cached_obj:
            return cached_obj
        
        # Buscar no banco
        obj = self.get(id)
        if obj:
            # Cachear resultado
            await cache_manager.set(cache_key, obj, self.cache_ttl)
        
        return obj
    
    async def get_multi_cached(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict] = None
    ) -> tuple[List[Any], int]:
        """Get multiple objects with caching."""
        # Gerar chave baseada nos parâmetros
        filter_str = str(sorted(filters.items())) if filters else "none"
        cache_key = f"{self.cache_prefix}:list:{skip}:{limit}:{filter_str}"
        
        # Tentar cache
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        # Buscar no banco
        objects, total = self.get_multi(skip=skip, limit=limit, filters=filters)
        
        # Cachear resultado
        result = (objects, total)
        await cache_manager.set(cache_key, result, self.cache_ttl)
        
        return result
    
    async def invalidate_cache(self, id: Optional[Any] = None):
        """Invalidate cache for this repository."""
        if id:
            # Invalidar cache específico
            cache_key = f"{self.cache_prefix}:get:{id}"
            await cache_manager.delete(cache_key)
        
        # Invalidar cache de listagens
        await cache_manager.clear_pattern(f"{self.cache_prefix}:list")
    
    def create(self, obj_in) -> Any:
        """Create object and invalidate cache."""
        obj = super().create(obj_in)
        # Invalidar cache de listagens
        asyncio.create_task(self.invalidate_cache())
        return obj
    
    def update(self, db_obj, obj_in) -> Any:
        """Update object and invalidate cache."""
        obj = super().update(db_obj, obj_in)
        # Invalidar cache específico e listagens
        asyncio.create_task(self.invalidate_cache(obj.id))
        return obj
    
    def remove(self, id: Any) -> Any:
        """Remove object and invalidate cache."""
        obj = super().remove(id)
        # Invalidar cache específico e listagens
        asyncio.create_task(self.invalidate_cache(id))
        return obj
```

### Item Repository com Cache (db/repository/item_repository.py)

```python
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from db.repository.cached_repository import CachedRepository
from db.models.item import Item
from schemas.item import ItemCreate, ItemUpdate
from core.cache import cache_manager

class ItemRepository(CachedRepository):
    def __init__(self, db: Session):
        super().__init__(db, Item, "item")
    
    @cache_manager.cache_result("item_by_name", ttl=600)
    async def get_by_name_cached(self, name: str) -> Optional[Item]:
        """Get item by name with caching."""
        return self.db.query(Item).filter(Item.name == name).first()
    
    @cache_manager.cache_result("items_by_category", ttl=300)
    async def get_by_category_cached(self, category_id: int) -> List[Item]:
        """Get items by category with caching."""
        return self.db.query(Item).filter(
            Item.category_id == category_id,
            Item.is_available == True
        ).all()
    
    @cache_manager.cache_result("items_search", ttl=180)
    async def search_items_cached(
        self, 
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Item], int]:
        """Search items with caching."""
        query = self.db.query(Item).filter(
            or_(
                Item.name.ilike(f"%{search_term}%"),
                Item.description.ilike(f"%{search_term}%")
            ),
            Item.is_available == True
        )
        
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        
        return items, total
    
    @cache_manager.cache_result("popular_items", ttl=1800)  # 30 minutos
    async def get_popular_items_cached(self, limit: int = 10) -> List[Item]:
        """Get popular items with caching."""
        # Assumindo que temos um campo de popularidade ou vendas
        return self.db.query(Item).filter(
            Item.is_available == True
        ).order_by(Item.view_count.desc()).limit(limit).all()
    
    async def increment_view_count(self, item_id: int):
        """Increment item view count and update cache."""
        item = self.get(item_id)
        if item:
            item.view_count = (item.view_count or 0) + 1
            self.db.commit()
            
            # Invalidar caches relacionados
            await self.invalidate_cache(item_id)
            await cache_manager.clear_pattern("popular_items")
```

---

## 🌐 Cache de Response HTTP

### Response Cache Middleware (middleware/cache_middleware.py)

```python
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import hashlib
import json
from core.cache import cache_manager
from core.config import settings

class ResponseCacheMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, cache_ttl: int = 300):
        super().__init__(app)
        self.cache_ttl = cache_ttl
        self.cacheable_methods = {"GET"}
        self.cacheable_status_codes = {200, 201}
    
    def _should_cache(self, request: Request, response: Response) -> bool:
        """Determine if response should be cached."""
        # Não cachear se cache está desabilitado
        if not settings.ENABLE_CACHE:
            return False
        
        # Só cachear métodos específicos
        if request.method not in self.cacheable_methods:
            return False
        
        # Só cachear status codes de sucesso
        if response.status_code not in self.cacheable_status_codes:
            return False
        
        # Não cachear se há autenticação
        if "authorization" in request.headers:
            return False
        
        # Não cachear endpoints específicos
        excluded_paths = ["/api/v1/auth/", "/api/v1/admin/"]
        if any(request.url.path.startswith(path) for path in excluded_paths):
            return False
        
        return True
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key for request."""
        # Incluir método, path e query parameters
        key_data = {
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params),
            "headers": {
                k: v for k, v in request.headers.items() 
                if k.lower() in ["accept", "accept-language", "content-type"]
            }
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"response:{key_hash}"
    
    async def dispatch(self, request: Request, call_next):
        # Gerar chave do cache
        cache_key = self._generate_cache_key(request)
        
        # Tentar obter response do cache
        if request.method in self.cacheable_methods:
            cached_response = await cache_manager.get(cache_key)
            if cached_response:
                return StarletteResponse(
                    content=cached_response["content"],
                    status_code=cached_response["status_code"],
                    headers=cached_response["headers"],
                    media_type=cached_response.get("media_type")
                )
        
        # Processar request
        response = await call_next(request)
        
        # Cachear response se apropriado
        if self._should_cache(request, response):
            # Ler conteúdo da response
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            # Preparar dados para cache
            cache_data = {
                "content": response_body.decode(),
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "media_type": response.media_type
            }
            
            # Cachear response
            await cache_manager.set(cache_key, cache_data, self.cache_ttl)
            
            # Recriar response com o conteúdo lido
            response = StarletteResponse(
                content=response_body,
                status_code=response.status_code,
                headers=response.headers,
                media_type=response.media_type
            )
        
        return response
```

### Cache Headers Middleware (middleware/cache_headers.py)

```python
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta

class CacheHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.cache_rules = {
            "/api/v1/items": {"max_age": 300, "public": True},  # 5 minutos
            "/api/v1/categories": {"max_age": 1800, "public": True},  # 30 minutos
            "/static": {"max_age": 86400, "public": True},  # 24 horas
        }
    
    def _get_cache_rule(self, path: str) -> dict:
        """Get cache rule for path."""
        for pattern, rule in self.cache_rules.items():
            if path.startswith(pattern):
                return rule
        return {}
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Aplicar headers de cache baseado no path
        cache_rule = self._get_cache_rule(request.url.path)
        
        if cache_rule and response.status_code == 200:
            max_age = cache_rule.get("max_age", 0)
            is_public = cache_rule.get("public", False)
            
            if max_age > 0:
                # Cache-Control header
                cache_control = f"max-age={max_age}"
                if is_public:
                    cache_control += ", public"
                else:
                    cache_control += ", private"
                
                response.headers["Cache-Control"] = cache_control
                
                # Expires header
                expires = datetime.utcnow() + timedelta(seconds=max_age)
                response.headers["Expires"] = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")
                
                # ETag header (simples baseado no conteúdo)
                if hasattr(response, 'body'):
                    import hashlib
                    etag = hashlib.md5(str(response.body).encode()).hexdigest()
                    response.headers["ETag"] = f'"{etag}"'
        
        return response
```

---

## ⚡ Otimizações de Performance

### Query Optimization (db/optimizations.py)

```python
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, joinedload, selectinload
from typing import List, Optional
import time
import logging

# Configurar logging para queries lentas
logging.basicConfig()
logger = logging.getLogger("sqlalchemy.engine")
logger.setLevel(logging.INFO)

# Event listener para monitorar queries lentas
@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - context._query_start_time
    if total > 0.1:  # Log queries que demoram mais de 100ms
        logger.warning(f"Slow query: {total:.4f}s - {statement[:100]}...")

class QueryOptimizer:
    """Utility class for query optimizations."""
    
    @staticmethod
    def optimize_item_queries(db: Session):
        """Apply optimizations for item queries."""
        # Eager loading para evitar N+1 queries
        return db.query(Item).options(
            joinedload(Item.category),
            selectinload(Item.reviews)
        )
    
    @staticmethod
    def optimize_user_queries(db: Session):
        """Apply optimizations for user queries."""
        return db.query(User).options(
            joinedload(User.role),
            selectinload(User.permissions)
        )
    
    @staticmethod
    def create_indexes(db: Session):
        """Create database indexes for better performance."""
        indexes = [
            # Items
            "CREATE INDEX IF NOT EXISTS idx_items_category_id ON items(category_id)",
            "CREATE INDEX IF NOT EXISTS idx_items_is_available ON items(is_available)",
            "CREATE INDEX IF NOT EXISTS idx_items_name_search ON items USING gin(to_tsvector('portuguese', name))",
            "CREATE INDEX IF NOT EXISTS idx_items_price ON items(price)",
            
            # Users
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active)",
            
            # Categories
            "CREATE INDEX IF NOT EXISTS idx_categories_is_active ON categories(is_active)",
            
            # Composite indexes
            "CREATE INDEX IF NOT EXISTS idx_items_category_available ON items(category_id, is_available)",
        ]
        
        for index_sql in indexes:
            try:
                db.execute(text(index_sql))
                db.commit()
                print(f"✅ Created index: {index_sql.split()[-1]}")
            except Exception as e:
                print(f"❌ Failed to create index: {e}")
                db.rollback()

# Optimized repository methods
class OptimizedItemRepository(ItemRepository):
    def get_with_relations(self, id: int) -> Optional[Item]:
        """Get item with all relations loaded."""
        return self.db.query(Item).options(
            joinedload(Item.category),
            selectinload(Item.reviews).joinedload(Review.user)
        ).filter(Item.id == id).first()
    
    def get_popular_with_stats(self, limit: int = 10) -> List[Item]:
        """Get popular items with aggregated stats."""
        return self.db.query(Item).options(
            joinedload(Item.category)
        ).filter(
            Item.is_available == True
        ).order_by(
            Item.view_count.desc(),
            Item.created_at.desc()
        ).limit(limit).all()
    
    def search_optimized(
        self, 
        search_term: str,
        category_id: Optional[int] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Item], int]:
        """Optimized search with filters."""
        query = self.db.query(Item).options(
            joinedload(Item.category)
        ).filter(Item.is_available == True)
        
        # Text search usando PostgreSQL full-text search
        if search_term:
            query = query.filter(
                text("to_tsvector('portuguese', name || ' ' || description) @@ plainto_tsquery('portuguese', :search)")
            ).params(search=search_term)
        
        # Filtros adicionais
        if category_id:
            query = query.filter(Item.category_id == category_id)
        
        if min_price:
            query = query.filter(Item.price >= min_price)
        
        if max_price:
            query = query.filter(Item.price <= max_price)
        
        # Count otimizado
        total = query.count()
        
        # Resultados paginados
        items = query.offset(skip).limit(limit).all()
        
        return items, total
```

### Connection Pooling (db/session.py)

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from core.config import settings

# Engine otimizado com connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,  # Número de conexões permanentes
    max_overflow=30,  # Conexões extras quando necessário
    pool_pre_ping=True,  # Verificar conexões antes de usar
    pool_recycle=3600,  # Reciclar conexões a cada hora
    echo=settings.DEBUG,  # Log SQL queries em desenvolvimento
    echo_pool=settings.DEBUG,  # Log pool events
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Dependency otimizada
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## 🛡️ Rate Limiting

### Rate Limiter (middleware/rate_limit.py)

```python
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from core.redis import redis_client
from core.config import settings
import time
from typing import Dict, Optional

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self, 
        app,
        calls: int = 100,
        period: int = 60,
        per_ip: bool = True
    ):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.per_ip = per_ip
        
        # Rate limits específicos por endpoint
        self.endpoint_limits = {
            "/api/v1/auth/login": {"calls": 5, "period": 300},  # 5 tentativas por 5 min
            "/api/v1/auth/register": {"calls": 3, "period": 3600},  # 3 registros por hora
            "/api/v1/items/": {"calls": 1000, "period": 60},  # 1000 requests por minuto
        }
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        if self.per_ip:
            # Usar IP real considerando proxies
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                return forwarded_for.split(",")[0].strip()
            return request.client.host
        else:
            # Usar user ID se autenticado
            user_id = getattr(request.state, "user_id", None)
            return str(user_id) if user_id else request.client.host
    
    def _get_rate_limit(self, path: str) -> Dict[str, int]:
        """Get rate limit for specific endpoint."""
        for endpoint, limits in self.endpoint_limits.items():
            if path.startswith(endpoint):
                return limits
        return {"calls": self.calls, "period": self.period}
    
    async def _is_rate_limited(
        self, 
        client_id: str, 
        endpoint: str,
        calls: int,
        period: int
    ) -> tuple[bool, Dict[str, int]]:
        """Check if client is rate limited."""
        key = f"rate_limit:{endpoint}:{client_id}"
        
        # Usar sliding window com Redis
        current_time = int(time.time())
        window_start = current_time - period
        
        # Remover entradas antigas
        await redis_client.redis.zremrangebyscore(key, 0, window_start)
        
        # Contar requests na janela atual
        current_requests = await redis_client.redis.zcard(key)
        
        # Informações para headers
        info = {
            "limit": calls,
            "remaining": max(0, calls - current_requests),
            "reset": current_time + period,
            "retry_after": period if current_requests >= calls else 0
        }
        
        if current_requests >= calls:
            return True, info
        
        # Adicionar request atual
        await redis_client.redis.zadd(key, {str(current_time): current_time})
        await redis_client.redis.expire(key, period)
        
        # Atualizar remaining
        info["remaining"] = max(0, calls - current_requests - 1)
        
        return False, info
    
    async def dispatch(self, request: Request, call_next):
        # Pular rate limiting para alguns paths
        skip_paths = ["/health", "/metrics", "/docs", "/openapi.json"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)
        
        client_id = self._get_client_id(request)
        endpoint = request.url.path
        rate_limit = self._get_rate_limit(endpoint)
        
        # Verificar rate limit
        is_limited, info = await self._is_rate_limited(
            client_id, 
            endpoint,
            rate_limit["calls"],
            rate_limit["period"]
        )
        
        if is_limited:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Try again in {info['retry_after']} seconds.",
                    "retry_after": info["retry_after"]
                },
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": str(info["remaining"]),
                    "X-RateLimit-Reset": str(info["reset"]),
                    "Retry-After": str(info["retry_after"])
                }
            )
        
        # Processar request
        response = await call_next(request)
        
        # Adicionar headers de rate limit
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(info["reset"])
        
        return response

# Decorator para rate limiting específico
def rate_limit(calls: int, period: int):
    """Decorator for endpoint-specific rate limiting."""
    def decorator(func):
        func._rate_limit = {"calls": calls, "period": period}
        return func
    return decorator
```

---

## 📊 Monitoramento de Performance

### Performance Monitor (core/monitoring.py)

```python
import time
import psutil
from typing import Dict, Any
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from core.redis import redis_client
import json
from datetime import datetime, timedelta

class PerformanceMonitor:
    def __init__(self):
        self.metrics_key = "performance_metrics"
    
    async def record_request(
        self, 
        method: str,
        path: str,
        status_code: int,
        duration: float,
        memory_usage: float,
        cpu_usage: float
    ):
        """Record request metrics."""
        timestamp = int(time.time())
        
        metric = {
            "timestamp": timestamp,
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration": duration,
            "memory_usage": memory_usage,
            "cpu_usage": cpu_usage
        }
        
        # Armazenar métrica no Redis (com TTL de 24 horas)
        key = f"{self.metrics_key}:{timestamp}"
        await redis_client.set(key, metric, expire=86400)
    
    async def get_metrics_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get performance metrics summary."""
        end_time = int(time.time())
        start_time = end_time - (hours * 3600)
        
        # Buscar métricas no período
        pattern = f"{self.metrics_key}:*"
        keys = await redis_client.get_pattern(pattern)
        
        metrics = []
        for key in keys:
            timestamp = int(key.split(":")[-1])
            if start_time <= timestamp <= end_time:
                metric = await redis_client.get(key)
                if metric:
                    metrics.append(metric)
        
        if not metrics:
            return {"message": "No metrics found"}
        
        # Calcular estatísticas
        total_requests = len(metrics)
        avg_duration = sum(m["duration"] for m in metrics) / total_requests
        max_duration = max(m["duration"] for m in metrics)
        min_duration = min(m["duration"] for m in metrics)
        
        # Agrupar por status code
        status_codes = {}
        for metric in metrics:
            code = metric["status_code"]
            status_codes[code] = status_codes.get(code, 0) + 1
        
        # Endpoints mais lentos
        endpoint_stats = {}
        for metric in metrics:
            path = metric["path"]
            if path not in endpoint_stats:
                endpoint_stats[path] = {"count": 0, "total_duration": 0}
            endpoint_stats[path]["count"] += 1
            endpoint_stats[path]["total_duration"] += metric["duration"]
        
        slowest_endpoints = sorted(
            [
                {
                    "path": path,
                    "avg_duration": stats["total_duration"] / stats["count"],
                    "count": stats["count"]
                }
                for path, stats in endpoint_stats.items()
            ],
            key=lambda x: x["avg_duration"],
            reverse=True
        )[:10]
        
        return {
            "period_hours": hours,
            "total_requests": total_requests,
            "avg_response_time": round(avg_duration, 4),
            "max_response_time": round(max_duration, 4),
            "min_response_time": round(min_duration, 4),
            "status_codes": status_codes,
            "slowest_endpoints": slowest_endpoints,
            "requests_per_hour": round(total_requests / hours, 2)
        }

# Instância global
performance_monitor = PerformanceMonitor()

class PerformanceMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.process = psutil.Process()
    
    async def dispatch(self, request: Request, call_next):
        # Métricas iniciais
        start_time = time.time()
        start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        start_cpu = self.process.cpu_percent()
        
        # Processar request
        response = await call_next(request)
        
        # Métricas finais
        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        end_cpu = self.process.cpu_percent()
        
        # Calcular métricas
        duration = end_time - start_time
        memory_usage = end_memory - start_memory
        cpu_usage = end_cpu - start_cpu
        
        # Registrar métricas
        await performance_monitor.record_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration=duration,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage
        )
        
        # Adicionar headers de performance
        response.headers["X-Response-Time"] = f"{duration:.4f}s"
        
        return response
```

### Health Check Endpoint (api/v1/health.py)

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.redis import redis_client
from db.session import get_db
from core.monitoring import performance_monitor
import psutil
import time

router = APIRouter()

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check."""
    health_status = {
        "status": "healthy",
        "timestamp": int(time.time()),
        "checks": {}
    }
    
    # Database check
    try:
        db.execute("SELECT 1")
        health_status["checks"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    # Redis check
    try:
        await redis_client.redis.ping()
        health_status["checks"]["redis"] = {"status": "healthy"}
    except Exception as e:
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    # System metrics
    health_status["system"] = {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent
    }
    
    return health_status

@router.get("/metrics")
async def get_metrics(hours: int = 1):
    """Get performance metrics."""
    return await performance_monitor.get_metrics_summary(hours)
```

---

## 🚀 Configuração Final

### Main Application (main.py)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager

from core.config import settings
from core.redis import redis_client
from middleware.cache_middleware import ResponseCacheMiddleware
from middleware.cache_headers import CacheHeadersMiddleware
from middleware.rate_limit import RateLimitMiddleware
from middleware.performance import PerformanceMiddleware
from api.v1.api import api_router
from api.v1.health import router as health_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await redis_client.connect()
    yield
    # Shutdown
    await redis_client.disconnect()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# Middlewares (ordem importa!)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(PerformanceMiddleware)
app.add_middleware(RateLimitMiddleware, calls=1000, period=60)
app.add_middleware(ResponseCacheMiddleware, cache_ttl=300)
app.add_middleware(CacheHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(api_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1", tags=["health"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        workers=4 if not settings.DEBUG else 1
    )
```

---

## 🎯 Próximos Passos

Com cache e otimizações implementados, você pode:

1. **Step 6:** Implementar WebSockets e comunicação em tempo real
2. **Step 7:** Deploy, monitoramento e observabilidade

---

## 📝 Exercícios Práticos

### Exercício 1: Cache Personalizado
Implemente cache personalizado para:
- Resultados de busca complexa
- Dados de usuário frequentemente acessados
- Estatísticas do sistema

### Exercício 2: Otimização de Queries
Otimize queries para:
- Relatórios complexos
- Agregações pesadas
- Buscas full-text

### Exercício 3: Monitoramento Avançado
Implemente:
- Alertas para performance degradada
- Métricas customizadas
- Dashboard de monitoramento

---

**Anterior:** [Step 4: Testes](step_4.md) | **Próximo:** [Step 6: WebSockets](step_6.md)
# WebSockets e Comunicação em Tempo Real

Implementar comunicação bidirecional em tempo real usando WebSockets com FastAPI, incluindo autenticação, gerenciamento de conexões, chat, notificações push e integração com Redis para aplicações distribuídas.

## 🎯 O que você vai aprender

- Fundamentos de WebSockets e comunicação em tempo real
- Implementação de WebSockets com FastAPI
- Autenticação e autorização em WebSockets
- Sistema de chat em tempo real
- Notificações push
- Gerenciamento de conexões distribuídas com Redis
- Padrões de arquitetura para aplicações real-time
- Monitoramento e debugging de WebSockets

---

## 🌐 Conceitos Fundamentais de WebSockets

### O que são WebSockets?

WebSockets são um protocolo de comunicação que permite conexão bidirecional e full-duplex entre cliente e servidor sobre uma única conexão TCP. Diferente do HTTP tradicional, que segue o modelo request-response, WebSockets mantêm uma conexão persistente que permite comunicação em tempo real.

#### Características dos WebSockets

1. **Conexão Persistente**: Uma vez estabelecida, a conexão permanece aberta
2. **Bidirecional**: Cliente e servidor podem enviar dados a qualquer momento
3. **Full-Duplex**: Dados podem fluir simultaneamente em ambas as direções
4. **Baixa Latência**: Sem overhead de headers HTTP em cada mensagem
5. **Eficiência**: Menos recursos de rede comparado a polling

### HTTP vs WebSockets

#### HTTP Tradicional (Request-Response)
```
Cliente                    Servidor
   |                          |
   |-------- Request -------->|
   |                          |
   |<------- Response --------|
   |                          |
   |-------- Request -------->|
   |                          |
   |<------- Response --------|
```

**Características:**
- Stateless (sem estado)
- Unidirecional (cliente inicia)
- Overhead de headers em cada request
- Ideal para operações CRUD

#### WebSockets
```
Cliente                    Servidor
   |                          |
   |------ Handshake -------->|
   |<----- Handshake ---------|
   |                          |
   |<====== Mensagens ======>|
   |<====== Bidirecionais ===>|
   |<====== Full-Duplex =====>|
```

**Características:**
- Stateful (mantém estado)
- Bidirecional (ambos podem iniciar)
- Baixo overhead após handshake
- Ideal para tempo real

### Casos de Uso para WebSockets

#### 1. Chat e Mensagens Instantâneas
- Aplicações de mensagens em tempo real
- Salas de chat com múltiplos usuários
- Indicadores de "usuário digitando"
- Histórico de mensagens sincronizado

#### 2. Notificações em Tempo Real
- Alertas do sistema
- Notificações de atividade do usuário
- Atualizações de status
- Lembretes e avisos

#### 3. Dashboards e Monitoramento
- Métricas em tempo real
- Gráficos dinâmicos
- Status de sistemas
- Alertas operacionais

#### 4. Colaboração em Tempo Real
- Editores colaborativos
- Quadros compartilhados
- Comentários em tempo real
- Sincronização de cursores

#### 5. Jogos e Aplicações Interativas
- Jogos multiplayer
- Aplicações de desenho colaborativo
- Votações em tempo real
- Leilões online

---

## 🚀 Implementação com FastAPI

### Configuração Básica

```python
# main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json
import logging

app = FastAPI(title="WebSocket Chat API")
logger = logging.getLogger(__name__)

# Gerenciador de conexões simples
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Nova conexão WebSocket. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Conexão WebSocket removida. Total: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Erro ao enviar mensagem: {e}")

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Mensagem recebida: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

### Estruturas de Dados para Mensagens

```python
# schemas/websocket.py
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class MessageType(str, Enum):
    CHAT = "chat"
    NOTIFICATION = "notification"
    SYSTEM = "system"
    TYPING = "typing"
    USER_JOIN = "user_join"
    USER_LEAVE = "user_leave"

class WebSocketMessage(BaseModel):
    type: MessageType
    data: Dict[str, Any]
    timestamp: datetime = datetime.now()
    user_id: Optional[str] = None
    room_id: Optional[str] = None

class ChatMessage(BaseModel):
    message: str
    user_id: str
    username: str
    room_id: str
    timestamp: datetime = datetime.now()

class NotificationMessage(BaseModel):
    title: str
    content: str
    severity: str = "info"  # info, warning, error, success
    action_url: Optional[str] = None

class TypingIndicator(BaseModel):
    user_id: str
    username: str
    room_id: str
    is_typing: bool
```

---

## 🔐 Autenticação WebSocket

### Middleware de Autenticação

```python
# core/websocket_auth.py
from fastapi import WebSocket, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Optional
from core.auth import decode_access_token
from db.models.user import User
from db.session import SessionLocal
import logging

logger = logging.getLogger(__name__)

async def authenticate_websocket(websocket: WebSocket) -> User | None:
    """Authenticate WebSocket connection using token from query params or headers."""
    token = None
    
    # Tentar obter token dos query parameters
    token = websocket.query_params.get("token")
    
    # Se não encontrou, tentar dos headers
    if not token:
        auth_header = websocket.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        logger.warning("WebSocket connection without authentication token")
        return None
    
    try:
        # Decodificar token
        payload = decode_access_token(token)
        if not payload:
            logger.warning("Invalid WebSocket authentication token")
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Token without user ID")
            return None
        
        # Buscar usuário no banco
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == int(user_id)).first()
            if not user or not user.is_active:
                logger.warning(f"User {user_id} not found or inactive")
                return None
            
            return user
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        return None

async def require_websocket_auth(websocket: WebSocket) -> User:
    """Require authentication for WebSocket connection."""
    user = await authenticate_websocket(websocket)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication required")
        raise HTTPException(status_code=401, detail="Authentication required")
    return user
```

### Gerenciador de Conexões Autenticadas

```python
# core/websocket_manager.py
from typing import Dict, Set, Optional, List
from fastapi import WebSocket
from db.models.user import User
from schemas.websocket import WebSocketMessage, MessageType
import json
import logging

logger = logging.getLogger(__name__)

class AuthenticatedConnectionManager:
    def __init__(self):
        # user_id -> websocket
        self.user_connections: Dict[str, WebSocket] = {}
        # room_id -> set of user_ids
        self.room_members: Dict[str, Set[str]] = {}
        # user_id -> set of room_ids
        self.user_rooms: Dict[str, Set[str]] = {}
    
    async def connect_user(self, websocket: WebSocket, user: User):
        """Connect authenticated user."""
        user_id = str(user.id)
        
        # Desconectar conexão anterior se existir
        if user_id in self.user_connections:
            try:
                await self.user_connections[user_id].close()
            except:
                pass
        
        self.user_connections[user_id] = websocket
        
        # Inicializar rooms do usuário se não existir
        if user_id not in self.user_rooms:
            self.user_rooms[user_id] = set()
        
        logger.info(f"User {user.username} ({user_id}) connected via WebSocket")
        
        # Enviar mensagem de boas-vindas
        await self.send_to_user(user_id, WebSocketMessage(
            type=MessageType.SYSTEM,
            data={"message": f"Bem-vindo, {user.username}!"}
        ))
    
    def disconnect_user(self, user_id: str):
        """Disconnect user and clean up."""
        if user_id in self.user_connections:
            del self.user_connections[user_id]
        
        # Remover usuário de todas as salas
        if user_id in self.user_rooms:
            for room_id in self.user_rooms[user_id].copy():
                self.leave_room(user_id, room_id)
            del self.user_rooms[user_id]
        
        logger.info(f"User {user_id} disconnected")
    
    async def join_room(self, user_id: str, room_id: str):
        """Add user to room."""
        if room_id not in self.room_members:
            self.room_members[room_id] = set()
        
        self.room_members[room_id].add(user_id)
        self.user_rooms[user_id].add(room_id)
        
        # Notificar outros membros da sala
        await self.broadcast_to_room(room_id, WebSocketMessage(
            type=MessageType.USER_JOIN,
            data={"user_id": user_id, "room_id": room_id},
            user_id=user_id
        ), exclude_user=user_id)
        
        logger.info(f"User {user_id} joined room {room_id}")
    
    def leave_room(self, user_id: str, room_id: str):
        """Remove user from room."""
        if room_id in self.room_members:
            self.room_members[room_id].discard(user_id)
            
            # Remover sala se vazia
            if not self.room_members[room_id]:
                del self.room_members[room_id]
        
        if user_id in self.user_rooms:
            self.user_rooms[user_id].discard(room_id)
        
        logger.info(f"User {user_id} left room {room_id}")
    
    async def send_to_user(self, user_id: str, message: WebSocketMessage):
        """Send message to specific user."""
        if user_id in self.user_connections:
            try:
                websocket = self.user_connections[user_id]
                await websocket.send_text(message.model_dump_json())
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                self.disconnect_user(user_id)
    
    async def broadcast_to_room(self, room_id: str, message: WebSocketMessage, exclude_user: Optional[str] = None):
        """Broadcast message to all users in room."""
        if room_id not in self.room_members:
            return
        
        for user_id in self.room_members[room_id]:
            if exclude_user and user_id == exclude_user:
                continue
            await self.send_to_user(user_id, message)
    
    async def broadcast_to_all(self, message: WebSocketMessage):
        """Broadcast message to all connected users."""
        for user_id in self.user_connections:
            await self.send_to_user(user_id, message)
    
    def get_room_members(self, room_id: str) -> List[str]:
        """Get list of user IDs in room."""
        return list(self.room_members.get(room_id, set()))
    
    def get_user_rooms(self, user_id: str) -> List[str]:
        """Get list of room IDs user is in."""
        return list(self.user_rooms.get(user_id, set()))
    
    def is_user_online(self, user_id: str) -> bool:
        """Check if user is currently connected."""
        return user_id in self.user_connections

# Instância global
connection_manager = AuthenticatedConnectionManager()
```

---

## 💬 Sistema de Chat em Tempo Real

### Modelos de Dados

```python
# db/models/chat.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.base import Base

class ChatRoom(Base):
    __tablename__ = "chat_rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_private = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    creator = relationship("User", back_populates="created_rooms")
    messages = relationship("ChatMessage", back_populates="room", cascade="all, delete-orphan")
    members = relationship("ChatRoomMember", back_populates="room", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    room_id = Column(Integer, ForeignKey("chat_rooms.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    edited_at = Column(DateTime(timezone=True))
    is_deleted = Column(Boolean, default=False)
    
    # Relacionamentos
    room = relationship("ChatRoom", back_populates="messages")
    user = relationship("User", back_populates="chat_messages")

class ChatRoomMember(Base):
    __tablename__ = "chat_room_members"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("chat_rooms.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    is_admin = Column(Boolean, default=False)
    
    # Relacionamentos
    room = relationship("ChatRoom", back_populates="members")
    user = relationship("User", back_populates="chat_memberships")
```

### Endpoints WebSocket para Chat

```python
# api/websocket/chat.py
from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from core.websocket_auth import require_websocket_auth
from core.websocket_manager import connection_manager
from schemas.websocket import WebSocketMessage, MessageType, ChatMessage
from services.chat_service import ChatService
import json
import logging

logger = logging.getLogger(__name__)

async def handle_chat_websocket(websocket: WebSocket, db: Session = Depends(get_db)):
    """Handle chat WebSocket connections."""
    try:
        # Autenticar usuário
        user = await require_websocket_auth(websocket)
        
        # Conectar usuário
        await connection_manager.connect_user(websocket, user)
        
        chat_service = ChatService(db)
        
        while True:
            # Receber mensagem
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            message_type = message_data.get("type")
            payload = message_data.get("data", {})
            
            if message_type == "join_room":
                await handle_join_room(user.id, payload, chat_service)
            
            elif message_type == "leave_room":
                await handle_leave_room(user.id, payload)
            
            elif message_type == "send_message":
                await handle_send_message(user, payload, chat_service)
            
            elif message_type == "typing":
                await handle_typing_indicator(user, payload)
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
    
    except WebSocketDisconnect:
        connection_manager.disconnect_user(str(user.id))
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect_user(str(user.id))

async def handle_join_room(user_id: int, payload: dict, chat_service: ChatService):
    """Handle user joining a chat room."""
    room_id = payload.get("room_id")
    if not room_id:
        return
    
    # Verificar se usuário pode entrar na sala
    if await chat_service.can_user_join_room(user_id, room_id):
        await connection_manager.join_room(str(user_id), str(room_id))
        
        # Enviar histórico de mensagens
        messages = await chat_service.get_room_messages(room_id, limit=50)
        await connection_manager.send_to_user(str(user_id), WebSocketMessage(
            type=MessageType.SYSTEM,
            data={"messages": [msg.dict() for msg in messages]}
        ))

async def handle_leave_room(user_id: int, payload: dict):
    """Handle user leaving a chat room."""
    room_id = payload.get("room_id")
    if room_id:
        connection_manager.leave_room(str(user_id), str(room_id))

async def handle_send_message(user, payload: dict, chat_service: ChatService):
    """Handle sending a chat message."""
    room_id = payload.get("room_id")
    content = payload.get("message")
    
    if not room_id or not content:
        return
    
    # Salvar mensagem no banco
    message = await chat_service.create_message(
        user_id=user.id,
        room_id=room_id,
        content=content
    )
    
    # Broadcast para a sala
    chat_message = ChatMessage(
        message=content,
        user_id=str(user.id),
        username=user.username,
        room_id=str(room_id)
    )
    
    await connection_manager.broadcast_to_room(str(room_id), WebSocketMessage(
        type=MessageType.CHAT,
        data=chat_message.dict(),
        user_id=str(user.id)
    ))

async def handle_typing_indicator(user, payload: dict):
    """Handle typing indicator."""
    room_id = payload.get("room_id")
    is_typing = payload.get("is_typing", False)
    
    if room_id:
        await connection_manager.broadcast_to_room(str(room_id), WebSocketMessage(
            type=MessageType.TYPING,
            data={
                "user_id": str(user.id),
                "username": user.username,
                "is_typing": is_typing
            },
            user_id=str(user.id)
        ), exclude_user=str(user.id))
```

---

## 🔔 Sistema de Notificações Push

### Gerenciador de Notificações

```python
# core/notification_manager.py
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from core.websocket_manager import connection_manager
from schemas.websocket import WebSocketMessage, MessageType, NotificationMessage

class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class Notification:
    id: str
    title: str
    content: str
    priority: NotificationPriority
    user_id: str | None = None
    action_url: str | None = None
    created_at: datetime = datetime.now()
    read: bool = False

class NotificationManager:
    def __init__(self):
        # user_id -> list of notifications
        self.user_notifications: dict[str, list[Notification]] = {}
    
    async def send_notification(
        self,
        user_id: str,
        title: str,
        content: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        action_url: str | None = None
    ):
        """Send notification to specific user."""
        notification = Notification(
            id=f"notif_{datetime.now().timestamp()}",
            title=title,
            content=content,
            priority=priority,
            user_id=user_id,
            action_url=action_url
        )
        
        # Armazenar notificação
        if user_id not in self.user_notifications:
            self.user_notifications[user_id] = []
        self.user_notifications[user_id].append(notification)
        
        # Enviar via WebSocket se usuário estiver online
        if connection_manager.is_user_online(user_id):
            await connection_manager.send_to_user(user_id, WebSocketMessage(
                type=MessageType.NOTIFICATION,
                data=NotificationMessage(
                    title=title,
                    content=content,
                    severity=priority.value,
                    action_url=action_url
                ).dict()
            ))
    
    async def broadcast_notification(
        self,
        title: str,
        content: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        action_url: Optional[str] = None
    ):
        """Broadcast notification to all online users."""
        await connection_manager.broadcast_to_all(WebSocketMessage(
            type=MessageType.NOTIFICATION,
            data=NotificationMessage(
                title=title,
                content=content,
                severity=priority.value,
                action_url=action_url
            ).dict()
        ))
    
    def get_user_notifications(self, user_id: str, unread_only: bool = False) -> List[Notification]:
        """Get notifications for user."""
        notifications = self.user_notifications.get(user_id, [])
        if unread_only:
            notifications = [n for n in notifications if not n.read]
        return notifications
    
    def mark_as_read(self, user_id: str, notification_id: str):
        """Mark notification as read."""
        notifications = self.user_notifications.get(user_id, [])
        for notification in notifications:
            if notification.id == notification_id:
                notification.read = True
                break

# Instância global
notification_manager = NotificationManager()
```

### Integração com Redis para Distribuição

```python
# core/redis_websocket.py
import redis.asyncio as redis
import json
import logging
from typing import Optional
from core.websocket_manager import connection_manager
from schemas.websocket import WebSocketMessage

logger = logging.getLogger(__name__)

class RedisWebSocketManager:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: redis.Redis | None = None
        self.pubsub: redis.client.PubSub | None = None
    
    async def connect(self):
        """Connect to Redis."""
        self.redis_client = redis.from_url(self.redis_url)
        self.pubsub = self.redis_client.pubsub()
        
        # Subscribe to WebSocket channels
        await self.pubsub.subscribe("websocket:broadcast", "websocket:user", "websocket:room")
        
        logger.info("Connected to Redis for WebSocket distribution")
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
        if self.redis_client:
            await self.redis_client.close()
    
    async def listen_for_messages(self):
        """Listen for Redis messages and distribute to local connections."""
        if not self.pubsub:
            return
        
        async for message in self.pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    channel = message["channel"].decode()
                    
                    if channel == "websocket:broadcast":
                        await self._handle_broadcast(data)
                    elif channel == "websocket:user":
                        await self._handle_user_message(data)
                    elif channel == "websocket:room":
                        await self._handle_room_message(data)
                
                except Exception as e:
                    logger.error(f"Error processing Redis message: {e}")
    
    async def _handle_broadcast(self, data: dict):
        """Handle broadcast message."""
        message = WebSocketMessage(**data["message"])
        await connection_manager.broadcast_to_all(message)
    
    async def _handle_user_message(self, data: dict):
        """Handle user-specific message."""
        user_id = data["user_id"]
        message = WebSocketMessage(**data["message"])
        await connection_manager.send_to_user(user_id, message)
    
    async def _handle_room_message(self, data: dict):
        """Handle room message."""
        room_id = data["room_id"]
        message = WebSocketMessage(**data["message"])
        exclude_user = data.get("exclude_user")
        await connection_manager.broadcast_to_room(room_id, message, exclude_user)
    
    async def publish_broadcast(self, message: WebSocketMessage):
        """Publish broadcast message to Redis."""
        if self.redis_client:
            await self.redis_client.publish("websocket:broadcast", json.dumps({
                "message": message.dict()
            }))
    
    async def publish_user_message(self, user_id: str, message: WebSocketMessage):
        """Publish user message to Redis."""
        if self.redis_client:
            await self.redis_client.publish("websocket:user", json.dumps({
                "user_id": user_id,
                "message": message.dict()
            }))
    
    async def publish_room_message(self, room_id: str, message: WebSocketMessage, exclude_user: Optional[str] = None):
        """Publish room message to Redis."""
        if self.redis_client:
            await self.redis_client.publish("websocket:room", json.dumps({
                "room_id": room_id,
                "message": message.dict(),
                "exclude_user": exclude_user
            }))

# Instância global
redis_websocket_manager = RedisWebSocketManager()
```

---

## 📊 Monitoramento e Métricas

### Métricas WebSocket

```python
# core/websocket_metrics.py
from prometheus_client import Counter, Gauge, Histogram
import time
from functools import wraps

# Métricas Prometheus
websocket_connections_total = Counter(
    'websocket_connections_total',
    'Total number of WebSocket connections',
    ['status']  # connected, disconnected, failed
)

websocket_active_connections = Gauge(
    'websocket_active_connections',
    'Number of active WebSocket connections'
)

websocket_messages_total = Counter(
    'websocket_messages_total',
    'Total number of WebSocket messages',
    ['type', 'direction']  # type: chat, notification, etc; direction: sent, received
)

websocket_message_duration = Histogram(
    'websocket_message_duration_seconds',
    'Time spent processing WebSocket messages',
    ['type']
)

def track_websocket_connection(func):
    """Decorator to track WebSocket connections."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        websocket_connections_total.labels(status='connected').inc()
        websocket_active_connections.inc()
        
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            websocket_connections_total.labels(status='failed').inc()
            raise
        finally:
            websocket_connections_total.labels(status='disconnected').inc()
            websocket_active_connections.dec()
    
    return wrapper

def track_message_processing(message_type: str):
    """Decorator to track message processing time."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                websocket_messages_total.labels(type=message_type, direction='processed').inc()
                return result
            finally:
                duration = time.time() - start_time
                websocket_message_duration.labels(type=message_type).observe(duration)
        
        return wrapper
    return decorator
```

### Health Checks para WebSocket

```python
# core/websocket_health.py
from fastapi import APIRouter, HTTPException
from core.websocket_manager import connection_manager
from core.redis_websocket import redis_websocket_manager

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/websocket")
async def websocket_health():
    """Health check for WebSocket services."""
    try:
        # Verificar conexões ativas
        active_connections = len(connection_manager.user_connections)
        
        # Verificar Redis (se configurado)
        redis_status = "not_configured"
        if redis_websocket_manager.redis_client:
            try:
                await redis_websocket_manager.redis_client.ping()
                redis_status = "healthy"
            except Exception:
                redis_status = "unhealthy"
        
        return {
            "status": "healthy",
            "active_connections": active_connections,
            "redis_status": redis_status,
            "rooms": len(connection_manager.room_members)
        }
    
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"WebSocket service unhealthy: {str(e)}")
```

---

## 🧪 Testes para WebSockets

### Testes de Conexão

```python
# tests/test_websocket.py
import pytest
from fastapi.testclient import TestClient
from main import app
import json

@pytest.fixture
def client():
    return TestClient(app)

def test_websocket_connection(client):
    """Test basic WebSocket connection."""
    with client.websocket_connect("/ws") as websocket:
        # Enviar mensagem de teste
        websocket.send_text("Hello WebSocket")
        
        # Receber resposta
        data = websocket.receive_text()
        assert "Hello WebSocket" in data

def test_websocket_authentication():
    """Test WebSocket authentication."""
    # Teste sem token
    with pytest.raises(Exception):
        with TestClient(app).websocket_connect("/ws/chat"):
            pass
    
    # Teste com token válido
    token = "valid_jwt_token"
    with TestClient(app).websocket_connect(f"/ws/chat?token={token}") as websocket:
        data = websocket.receive_text()
        message = json.loads(data)
        assert message["type"] == "system"

def test_chat_message_flow():
    """Test chat message flow."""
    token = "valid_jwt_token"
    
    with TestClient(app).websocket_connect(f"/ws/chat?token={token}") as websocket:
        # Entrar em uma sala
        websocket.send_text(json.dumps({
            "type": "join_room",
            "data": {"room_id": "1"}
        }))
        
        # Enviar mensagem
        websocket.send_text(json.dumps({
            "type": "send_message",
            "data": {
                "room_id": "1",
                "message": "Hello, room!"
            }
        }))
        
        # Verificar se mensagem foi processada
        data = websocket.receive_text()
        message = json.loads(data)
        assert message["type"] == "chat"
        assert message["data"]["message"] == "Hello, room!"
```

---

## 📝 Resumo

Neste step, implementamos um sistema completo de WebSockets e comunicação em tempo real com:

### ✅ Funcionalidades Implementadas

1. **Fundamentos WebSocket**
   - Conceitos e diferenças com HTTP
   - Casos de uso e padrões de comunicação
   - Protocolo e estados de conexão

2. **Implementação FastAPI**
   - Configuração básica de WebSockets
   - Gerenciador de conexões autenticadas
   - Estruturas de dados para mensagens

3. **Autenticação e Segurança**
   - Middleware de autenticação WebSocket
   - Validação de tokens JWT
   - Gerenciamento seguro de conexões

4. **Sistema de Chat**
   - Salas de chat com membros
   - Mensagens em tempo real
   - Indicadores de digitação
   - Histórico de mensagens

5. **Notificações Push**
   - Sistema de notificações em tempo real
   - Diferentes níveis de prioridade
   - Broadcast e mensagens direcionadas

6. **Integração Redis**
   - Distribuição de mensagens entre instâncias
   - Pub/Sub para escalabilidade
   - Gerenciamento distribuído de conexões

7. **Monitoramento**
   - Métricas Prometheus
   - Health checks específicos
   - Tracking de performance

8. **Testes e Cliente**
   - Testes automatizados para WebSockets
   - Cliente JavaScript completo
   - Exemplos de integração

### 🎯 Próximos Passos

No próximo step, vamos abordar **Deploy, Monitoramento e Observabilidade**, incluindo:
- Containerização com Docker
- CI/CD com GitHub Actions
- Monitoramento em produção
- Logging estruturado
- Observabilidade e tracing
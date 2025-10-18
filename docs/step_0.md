# Fundamentos e Conceitos Essenciais

Este é o ponto de partida para aprender FastAPI. Aqui você encontrará os conceitos fundamentais que precisa dominar antes de começar a desenvolver APIs.

## 📚 Conceitos Essenciais de APIs

### O que é uma API?

Uma API (Interface de Programação de Aplicações) é um conjunto de regras e protocolos que permite que diferentes sistemas se comuniquem. É como um "contrato" entre aplicações.

**Analogia do Restaurante:**

- **Cliente (Você):** Quer uma refeição
- **API (Garçom):** Interface que recebe seu pedido e traz a resposta
- **Servidor (Cozinha):** Processa o pedido e prepara a resposta

### O que é REST?

REST (Representational State Transfer) é um estilo arquitetural para APIs que define como os recursos devem ser organizados e acessados.

**Princípios REST:**

1. **Stateless:** Cada requisição é independente
2. **Recursos:** Tudo é tratado como recurso (usuários, produtos, etc.)
3. **Verbos HTTP:** GET, POST, PUT, DELETE para diferentes operações
4. **Representações:** Dados em formato JSON, XML, etc.

### Verbos HTTP Principais

| Verbo | Propósito | Exemplo | Descrição Detalhada |
|-------|-----------|---------|---------------------|
| GET | Buscar dados | `GET /users/123` | Recupera informações sem modificar |
| POST | Criar novo recurso | `POST /users` | Cria um novo recurso no servidor |
| PUT | Atualizar recurso completo | `PUT /users/123` | Substitui completamente o recurso |
| PATCH | Atualizar parcialmente | `PATCH /users/123` | Modifica apenas campos específicos |
| DELETE | Remover recurso | `DELETE /users/123` | Remove o recurso do servidor |

### (Alguns) Códigos de Status HTTP

| Código | Significado | Quando usar | Exemplo de Uso |
|--------|-------------|-------------|----------------|
| 200 | OK | Operação bem-sucedida | GET retorna dados |
| 201 | Created | Recurso criado com sucesso | POST cria usuário |
| 400 | Bad Request | Dados inválidos na requisição | JSON malformado |
| 401 | Unauthorized | Não autenticado | Token ausente |
| 403 | Forbidden | Não autorizado | Sem permissão |
| 404 | Not Found | Recurso não encontrado | ID inexistente |
| 422 | Unprocessable Entity | Dados válidos mas regra de negócio falha | Email já existe |
| 500 | Internal Server Error | Erro no servidor | Exceção não tratada |

### Exemplo Prático de API REST

```python
# Exemplo de endpoints RESTful para gerenciar usuários
GET    /api/v1/users          # Lista todos os usuários
GET    /api/v1/users/123      # Busca usuário específico
POST   /api/v1/users          # Cria novo usuário
PUT    /api/v1/users/123      # Atualiza usuário completo
PATCH  /api/v1/users/123      # Atualiza campos específicos
DELETE /api/v1/users/123      # Remove usuário

# Estrutura de resposta consistente
{
    "success": true,
    "data": {
        "id": 123,
        "name": "João Silva",
        "email": "joao@email.com"
    },
    "message": "Usuário criado com sucesso"
}
```

---

## 🚀 Introdução ao FastAPI

### O que é FastAPI?

FastAPI é um framework web moderno e de alta performance para construir APIs em Python. Foi criado por Sebastian Ramirez e se tornou uma das escolhas mais populares para desenvolvimento de APIs.

### Principais Vantagens

1. **Performance:** Uma das mais rápidas disponíveis (comparável ao NodeJS e Go)
2. **Fácil de usar:** Sintaxe intuitiva e documentação excelente
3. **Type Hints:** Usa tipagem Python para validação automática
4. **Documentação automática:** Gera Swagger UI e ReDoc automaticamente
5. **Async nativo:** Suporte completo a programação assíncrona
6. **Validação automática:** Valida dados de entrada automaticamente
7. **Padrões modernos:** Baseado em OpenAPI e JSON Schema

---

## ⚡ Programação Assíncrona no FastAPI

### Conceitos Fundamentais

**Programação Síncrona (Tradicional):**

```python
# Síncrono - bloqueia até completar
def buscar_dados():
    time.sleep(2)  # Simula operação lenta
    return "dados"

# Assíncrono - não bloqueia
async def buscar_dados_async():
    await asyncio.sleep(2)  # Simula operação lenta
    return "dados"
```

**Programação Síncrona** é o modelo tradicional onde o código executa **linha por linha**, **esperando** cada operação terminar antes de passar para a próxima.

```python
import time

def exemplo_sincrono():
    print("1. Iniciando operação...")
    
    # Operação 1: Buscar dados do usuário (simula 2 segundos)
    time.sleep(2)
    usuario = {"nome": "João", "id": 123}
    print("2. Usuário encontrado!")
    
    # Operação 2: Buscar pedidos do usuário (simula 1 segundo)
    time.sleep(1)
    pedidos = [{"id": 1, "valor": 100}, {"id": 2, "valor": 200}]
    print("3. Pedidos encontrados!")
    
    # Operação 3: Calcular total (instantâneo)
    total = sum(pedido["valor"] for pedido in pedidos)
    print(f"4. Total calculado: R$ {total}")
    
    return {"usuario": usuario, "pedidos": pedidos, "total": total}

# Execução: 3 segundos total (2 + 1 + 0)
# O programa "trava" em cada sleep(), não faz nada mais
```

**Problemas da Programação Síncrona:**

- ⏳ **Tempo perdido**: Enquanto espera uma operação, não faz nada
- 🚫 **Bloqueio**: Uma operação lenta trava todo o programa
- 📉 **Baixa performance**: Não aproveita o tempo de espera
- 😴 **Recursos ociosos**: CPU fica "dormindo" desnecessariamente

### Por que Usar Async/Await?

**Exemplo Prático - Diferença de Performance:**

```python
import asyncio
import httpx
import time

# ❌ Versão Síncrona (Lenta)
def buscar_dados_sync():
    # Simula 3 requisições que demoram 1 segundo cada
    dados = []
    for i in range(3):
        time.sleep(1)  # Bloqueia por 1 segundo
        dados.append(f"dados_{i}")
    return dados
    # Total: 3 segundos! 😴

# ✅ Versão Assíncrona (Rápida)
async def buscar_dados_async():
    async def buscar_item(i):
        await asyncio.sleep(1)  # Não bloqueia
        return f"dados_{i}"
    
    # Executa as 3 requisições em paralelo
    tasks = [buscar_item(i) for i in range(3)]
    dados = await asyncio.gather(*tasks)
    return dados
    # Total: 1 segundo! 🚀 (3x mais rápido)
```

### 🚀 Async/Await - Explicação Detalhada

**Programação Assíncrona** permite que o programa **não trave** enquanto espera operações lentas. Em vez de ficar parado, ele pode fazer outras coisas!

```python
import asyncio

async def exemplo_assincrono():
    print("1. Iniciando operações...")
    
    # Define as operações que podem rodar em paralelo
    async def buscar_usuario():
        print("   🔍 Buscando usuário...")
        await asyncio.sleep(2)  # Simula operação lenta
        print("   ✅ Usuário encontrado!")
        return {"nome": "João", "id": 123}
    
    async def buscar_pedidos():
        print("   🔍 Buscando pedidos...")
        await asyncio.sleep(1)  # Simula operação lenta
        print("   ✅ Pedidos encontrados!")
        return [{"id": 1, "valor": 100}, {"id": 2, "valor": 200}]
    
    async def buscar_configuracoes():
        print("   🔍 Buscando configurações...")
        await asyncio.sleep(1.5)  # Simula operação lenta
        print("   ✅ Configurações encontradas!")
        return {"tema": "escuro", "idioma": "pt-br"}
    
    # 🚀 EXECUTA TUDO EM PARALELO!
    usuario, pedidos, config = await asyncio.gather(
        buscar_usuario(),
        buscar_pedidos(),
        buscar_configuracoes()
    )
    
    # Operação final (instantânea)
    total = sum(pedido["valor"] for pedido in pedidos)
    print(f"2. Total calculado: R$ {total}")
    
    return {
        "usuario": usuario, 
        "pedidos": pedidos, 
        "config": config,
        "total": total
    }

# Execução: ~2 segundos total (tempo da operação mais lenta)
# Em vez de 4.5 segundos (2 + 1 + 1.5) se fosse síncrono!
```

**Vantagens do Async/Await:**

- ⚡ **Muito mais rápido**: Operações em paralelo
- 🔄 **Não bloqueia**: Programa continua responsivo
- 💪 **Melhor uso de recursos**: CPU não fica ociosa
- 🌐 **Ideal para I/O**: Perfeito para APIs, banco de dados, arquivos

**Como funciona na prática:**

```python
# Quando você faz await, o Python diz:
# "Ok, vou esperar isso aqui, mas enquanto isso, 
#  vou fazer outras coisas que estão prontas!"

async def exemplo_real():
    # Inicia 3 operações ao mesmo tempo
    task1 = asyncio.create_task(consultar_api_externa())
    task2 = asyncio.create_task(consultar_banco_dados())
    task3 = asyncio.create_task(processar_arquivo())
    
    # Espera todas terminarem
    resultado1, resultado2, resultado3 = await asyncio.gather(
        task1, task2, task3
    )
    
    return combinar_resultados(resultado1, resultado2, resultado3)
```

### Quando Usar Async/Await

**✅ Use async/await quando:**

- Fazendo requisições HTTP para outras APIs
- Consultando banco de dados
- Lendo/escrevendo arquivos
- Operações de rede em geral
- Qualquer operação que "espera"

```python
# ✅ Bom uso de async
@app.get("/dados-externos")
async def buscar_dados_externos():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.externa.com/dados")
        return response.json()

# ✅ Bom uso de async com banco
@app.get("/usuarios")
async def listar_usuarios():
    usuarios = await database.fetch_all("SELECT * FROM usuarios")
    return usuarios
```

**❌ NÃO use async/await quando:**

- Fazendo cálculos simples
- Manipulando strings/listas
- Operações que não "esperam"

```python
# ❌ Uso desnecessário de async
@app.get("/calcular")
async def calcular(a: int, b: int):
    resultado = a + b  # Operação instantânea, não precisa de async
    return {"resultado": resultado}

# ✅ Versão correta
@app.get("/calcular")
def calcular(a: int, b: int):
    resultado = a + b
    return {"resultado": resultado}
```

---

## 📝 Validação de Dados com Pydantic

### O que é Pydantic?

Pydantic é uma biblioteca que **valida dados automaticamente** usando **type hints** do Python. É o coração da validação no FastAPI.

### Exemplo Básico de Validação

```python
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime

class Usuario(BaseModel):
    nome: str
    email: EmailStr
    idade: int
    ativo: bool = True
    data_criacao: datetime | None = None

    @field_validator('nome')
    @classmethod
    def nome_deve_ter_pelo_menos_2_caracteres(cls, v):
        if len(v) < 2:
            raise ValueError('Nome deve ter pelo menos 2 caracteres')
        return v.title()  # Capitaliza o nome

    @field_validator('idade')
    @classmethod
    def idade_deve_ser_valida(cls, v):
        if v < 0:
            raise ValueError('Idade não pode ser negativa')
        if v > 120:
            raise ValueError('Idade não pode ser maior que 120')
        return v

# ✅ Dados válidos
usuario_valido = Usuario(
    nome="joão silva",
    email="joao@email.com",
    idade=25
)
print(usuario_valido.nome)  # "João Silva" (capitalizado automaticamente)

# ❌ Dados inválidos
try:
    usuario_invalido = Usuario(
        nome="J",  # Muito curto
        email="email-inválido",  # Email inválido
        idade=-5  # Idade negativa
    )
except ValueError as e:
    print(f"Erro de validação: {e}")
```

### Modelos Aninhados e Complexos

```python
class Endereco(BaseModel):
    rua: str
    numero: int
    cidade: str
    cep: str
    estado: str

class ItemPedido(BaseModel):
    produto_id: int
    nome_produto: str
    quantidade: int
    preco_unitario: float
    
    @property
    def subtotal(self) -> float:
        return self.quantidade * self.preco_unitario

class Pedido(BaseModel):
    id: int | None = None
    cliente_nome: str
    cliente_email: EmailStr
    endereco_entrega: Endereco
    itens: list[ItemPedido]
    data_pedido: datetime = datetime.now()
    status: str = "pendente"
    
    @property
    def total(self) -> float:
        return sum(item.subtotal for item in self.itens)
    
    @validator('itens')
    def deve_ter_pelo_menos_um_item(cls, v):
        if not v:
            raise ValueError('Pedido deve ter pelo menos um item')
        return v

# Exemplo de uso
pedido = Pedido(
    cliente_nome="Maria Silva",
    cliente_email="maria@email.com",
    endereco_entrega=Endereco(
        rua="Rua das Flores",
        numero=123,
        cidade="São Paulo",
        cep="01234-567",
        estado="SP"
    ),
    itens=[
        ItemPedido(
            produto_id=1,
            nome_produto="Notebook",
            quantidade=1,
            preco_unitario=2500.00
        ),
        ItemPedido(
            produto_id=2,
            nome_produto="Mouse",
            quantidade=2,
            preco_unitario=50.00
        )
    ]
)

print(f"Total do pedido: R$ {pedido.total}")  # R$ 2600.0
```

---

## 🛠️ Configuração do Ambiente de Desenvolvimento

### Instalação com UV (Recomendado)

UV, uma única ferramenta para substituir pip, pip-tools, pipx, poetry, pyenv, twine, virtualenv, e mais.

```bash
# Criar ambiente virtual
uv venv

# Ativar ambiente (Windows)
.venv\Scripts\activate

# Ativar ambiente (Linux/Mac)
source .venv/bin/activate

# Instalar FastAPI e Uvicorn
uv add fastapi uvicorn[standard]
```

### Sua Primeira API

Crie um arquivo `main.py`:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="Minha Primeira API",
    description="Uma API de exemplo para aprender FastAPI",
    version="1.0.0"
)

class Mensagem(BaseModel):
    texto: str
    autor: str = "Anônimo"

@app.get("/")
async def root():
    return {"message": "Olá, FastAPI!"}

@app.get("/saudacao/{nome}")
async def saudar(nome: str):
    return {"message": f"Olá, {nome}!"}

@app.post("/mensagem")
async def criar_mensagem(mensagem: Mensagem):
    return {
        "message": "Mensagem recebida!",
        "dados": mensagem
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Executar a API

```bash
# Método 1: Usando uvicorn diretamente
uvicorn main:app --reload

# Método 2: Executando o arquivo Python
python main.py
```

### Acessar a Documentação

Após iniciar o servidor, acesse:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI JSON:** `http://localhost:8000/openapi.json`

---

## 🎯 Próximos Passos

Agora que você domina os fundamentos, está pronto para:

1. Criar sua primeira API completa com estrutura profissional
2. Integrar banco de dados e persistência
3. Implementar autenticação e autorização
4. Criar testes automatizados
5. Otimizar performance com cache
6. Implementar WebSockets
7. Deploy e monitoramento em produção

**Dica:** Pratique os conceitos deste step criando pequenas APIs antes de avançar. A base sólida é fundamental para o sucesso nos próximos passos! 🚀

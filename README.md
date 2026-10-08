# Orquestrador Assíncrono de Pedidos

Projeto de portfólio que demonstra uma arquitetura orientada a eventos para
receber e processar pedidos de forma assíncrona. A API aceita o pedido e o
publica no RabbitMQ; um worker independente consulta o ViaCEP e persiste o
resultado no PostgreSQL.

## Arquitetura

```text
Cliente HTTP
    |
    | POST /orders
    v
API FastAPI --- publica OrderRequestDTO ---> RabbitMQ (order_queue)
                                                |
                                                | entrega mensagem
                                                v
                                      Worker de pedidos
                                       |             |
                                       |             +--> ViaCEP
                                       v
                                  PostgreSQL
                                       ^
                                       |
                         GET /orders/{order_id}
```

### Fluxo de processamento

1. O cliente envia um pedido para `POST /orders`.
2. O FastAPI valida o JSON como `OrderRequestDTO`, incluindo cliente e
   informações de entrega aninhadas.
3. `OrderService` delega a publicação ao `RabbitMQOrderPublisher`. A API
   responde `202 Accepted` quando a publicação termina.
4. O worker consome a mensagem e valida novamente o JSON recebido da fila.
5. `OrderProcessor` consulta o ViaCEP por meio de `ViaCepClient`, calcula o
   frete configurado e delega a gravação ao `OrderRepository`.
6. O repositório faz upsert do cliente e do pedido. O endereço permanece em
   campos separados no PostgreSQL.
7. O cliente consulta o resultado em `GET /orders/{order_id}`. A API retorna
   os dados de entrega como um objeto `shipping`.

Como o processamento é assíncrono, `202 Accepted` significa que o pedido foi
aceito para processamento, não que já foi concluído. O pedido só é gravado
depois que o worker consulta o ViaCEP; portanto, uma consulta GET feita antes
desse momento retorna `404`.

## Tecnologias

- Python 3.11
- FastAPI e Pydantic
- RabbitMQ e Pika
- PostgreSQL 15 e SQLAlchemy
- ViaCEP
- Docker Compose

## Organização do código

```text
api/
  infrastructure/       Adaptador que publica pedidos no RabbitMQ
  routes/               Endpoints HTTP e conversão de erros em respostas
  services/             Casos de uso da API
  main.py               Criação da aplicação FastAPI e inicialização
  schemas.py            DTOs das respostas HTTP
worker/
  infrastructure/       Cliente HTTP tipado para o ViaCEP
  services/             Orquestração do processamento do pedido
  main.py               Consumo e confirmação das mensagens RabbitMQ
shared/
  repositories/         Consultas e gravações no PostgreSQL
  config.py             Configurações carregadas do ambiente
  database.py           Engine, sessões e criação das tabelas
  dtos.py               Contratos tipados compartilhados
  models.py             Modelos SQLAlchemy
docker-compose.yml      API, worker, RabbitMQ e PostgreSQL
```

As rotas não implementam consultas SQL ou chamadas ao RabbitMQ diretamente.
Os serviços coordenam os casos de uso, enquanto os adaptadores e o repositório
encapsulam o acesso a sistemas externos.

## Pré-requisitos

- Docker Desktop instalado e em execução.
- Docker Compose v2 (`docker compose`).

Não é necessário instalar Python ou as dependências localmente para executar a
versão com Docker.

## Qualidade de código e testes

O projeto usa Ruff para lint e formatação, e pytest para testes automatizados.
Essas ferramentas ficam em `requirements-dev.txt`, separadas das dependências
necessárias para executar os serviços.

Para instalar as dependências de desenvolvimento em um ambiente virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

Executar o linter:

```powershell
ruff check .
```

Verificar a formatação:

```powershell
ruff format --check .
```

Aplicar a formatação automaticamente:

```powershell
ruff format .
```

Executar os testes:

```powershell
pytest
```

`.gitignore` exclui ambientes virtuais, caches, arquivos locais de ambiente e
artefatos de teste do controle de versão. `.dockerignore` reduz o contexto de
build e evita enviar caches, testes e arquivos de ambiente para as imagens.

## Executar

Na raiz do projeto:

```powershell
docker compose up --build
```

Para iniciar em segundo plano:

```powershell
docker compose up --build -d
```

Para acompanhar os logs:

```powershell
docker compose logs -f api worker
```

Para parar os serviços sem remover os dados persistidos:

```powershell
docker compose down
```

O PostgreSQL usa o volume `postgres_data`; por isso os registros permanecem
quando os contêineres são parados e iniciados novamente. Para apagar também
esse volume e todos os dados locais, use `docker compose down --volumes`.
**Esse comando é destrutivo e não pode ser desfeito.**

### Endereços locais

| Serviço | Endereço | Uso |
| --- | --- | --- |
| API | `http://localhost:8000` | Endpoints de pedidos |
| Swagger UI | `http://localhost:8000/docs` | Explorar e executar requisições |
| RabbitMQ Management | `http://localhost:15672` | Painel da fila |
| PostgreSQL | `localhost:5432` | Banco `orderdb` |

No ambiente local do Compose, o painel RabbitMQ usa as credenciais padrão
`guest` / `guest`. As credenciais do PostgreSQL também são as de
desenvolvimento definidas no Compose: usuário `postgres`, senha `postgres` e
banco `orderdb`. **Não use essas credenciais padrão em produção.**

## Utilizar a API

### Criar um pedido

`POST /orders` aceita o seguinte JSON:

```json
{
  "order_id": "pedido-001",
  "items_total": 120.5,
  "customer": {
    "customer_id": "cliente-001",
    "name": "Maria Silva",
    "email": "maria@example.com"
  },
  "shipping": {
    "cep": "01001-000"
  }
}
```

O CEP pode ser enviado com ou sem hífen. Campos ausentes ou inválidos são
recusados pela validação do DTO.

Exemplo no PowerShell:

```powershell
$payload = @{
  order_id = "pedido-001"
  items_total = 120.5
  customer = @{
    customer_id = "cliente-001"
    name = "Maria Silva"
    email = "maria@example.com"
  }
  shipping = @{
    cep = "01001-000"
  }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/orders" `
  -ContentType "application/json" `
  -Body $payload
```

Resposta esperada, com status HTTP `202 Accepted`:

```json
{
  "order_id": "pedido-001",
  "status": "ACCEPTED"
}
```

### Consultar o pedido

```powershell
Invoke-RestMethod -Method Get `
  -Uri "http://localhost:8000/orders/pedido-001"
```

Após o worker concluir o processamento, a resposta `200 OK` tem este formato:

```json
{
  "order_id": "pedido-001",
  "customer_id": "cliente-001",
  "shipping": {
    "cep": "01001-000",
    "logradouro": "Praça da Sé",
    "complemento": "lado ímpar",
    "bairro": "Sé",
    "cidade": "São Paulo",
    "estado": "SP"
  },
  "items_total": 120.5,
  "shipping_cost": 15.0,
  "total": 135.5,
  "status": "COMPLETED"
}
```

Os campos opcionais do ViaCEP, como `logradouro`, `complemento` e `bairro`,
podem ser `null`. A cidade, o estado e o CEP são guardados separadamente; não
há concatenação do endereço em uma string para a resposta da API.

### Respostas de erro relevantes

| HTTP | Situação |
| --- | --- |
| `202` | Pedido publicado para processamento |
| `404` | Pedido ainda não foi gravado ou não existe |
| `422` | JSON recebido não passou na validação |
| `503` | RabbitMQ indisponível após as tentativas de publicação ou banco indisponível na consulta |

## Configuração

O projeto carrega configurações por variáveis de ambiente em
`shared/config.py`. O Compose define as URLs internas do banco e do RabbitMQ.
As demais opções e seus valores padrão são:

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+psycopg2://postgres:postgres@localhost:5432/orderdb` | Conexão SQLAlchemy |
| `RABBITMQ_URL` | `amqp://guest:guest@localhost:5672/%2F` | Conexão AMQP |
| `ORDER_QUEUE` | `order_queue` | Nome da fila |
| `VIACEP_BASE_URL` | `https://viacep.com.br/ws` | URL base do ViaCEP |
| `SHIPPING_COST` | `15.00` | Frete fixo por pedido |
| `LOG_LEVEL` | `INFO` | Nível dos logs |

Dentro do Docker Compose, use os nomes dos serviços (`postgres` e `rabbitmq`)
nas URLs, como já está configurado no `docker-compose.yml`. `localhost` dentro
de um contêiner apontaria para o próprio contêiner, não para os demais.

## Comportamento de mensagens

- A fila é declarada como durável e as mensagens são publicadas como
  persistentes.
- O worker processa uma mensagem por vez por instância (`prefetch_count=1`).
- Mensagens processadas com sucesso recebem confirmação (`ack`).
- Mensagens inválidas ou com CEP não encontrado não são reenfileiradas.
- Falhas inesperadas durante o processamento são reenfileiradas.
- Cliente existente não é duplicado; pedido com o mesmo `order_id` é
  atualizado pelo upsert.

## Escopo e limitações

Este projeto tem foco demonstrativo e não pretende ser uma configuração pronta
para produção. Entre as simplificações atuais:

- O frete é fixo e os valores monetários usam `float`.
- A API responde após publicar a mensagem, mas o publisher ainda não aguarda
  publisher confirms explícitos do RabbitMQ.

- As tabelas são criadas automaticamente com SQLAlchemy; não há migrações
  versionadas com Alquemy.
- O Compose usa credenciais locais padrão e não configura autenticação própria
  para o painel RabbitMQ.

Esses pontos são oportunidades de evolução: publisher confirms, política
limitada de retries com dead-letter queue, migrações, valores monetários com
`Decimal`/`NUMERIC`, gestão segura de segredos e testes automatizados de
integração.

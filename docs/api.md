# API

## Visão Geral

A API é implementada em Flask e retorna JSON. Os endpoints são consumidos por `app/static/js/script.js`.

Base local:

```text
http://127.0.0.1:5000
```

## Convenções

- Sucesso: `200 OK`, `201 Created`.
- Erro de validação: `400 Bad Request`.
- Erro de autenticação: `401 Unauthorized`.
- Registro não encontrado: `404 Not Found`.
- Erro de banco ou aplicação: `500` ou `503`.

Resposta de erro:

```json
{
  "erro": "Mensagem do erro"
}
```

## Endpoints de Interface

### `GET /`

Renderiza `base.html`.

## Endpoints de Filtros

### `GET /filiais`

Retorna lista de filiais.

```json
["Filial Campinas", "Filial Sao Paulo Centro"]
```

### `GET /categorias`

Retorna lista de categorias.

### `GET /produtos?categoria=Perifericos`

Retorna nomes de produtos, opcionalmente filtrados por categoria.

### `GET /produtos_detalhados?categoria=Hardware`

Retorna catálogo detalhado.

```json
[
  {
    "produto": "Fonte 650W",
    "categoria": "Hardware",
    "marca": "PowerMax",
    "preco": 399.9,
    "status": "ATIVO",
    "vendidos": 1497,
    "receita": 567170.44
  }
]
```

### `GET /clientes`

Retorna clientes.

```json
[
  {
    "nome": "Cliente 1",
    "tipo": "B2C",
    "cidade": "Belo Horizonte",
    "uf": "MG",
    "cadastro": "2025-07-19"
  }
]
```

## Endpoints de Usuários

### `GET /usuarios`

Lista usuários da aplicação.

```json
[
  {
    "id": "u-1",
    "dbId": 1,
    "name": "Marina Costa",
    "email": "admin@aurora.local",
    "roleId": "administrador",
    "status": "Ativo"
  }
]
```

### `POST /auth/login`

Autentica usuário.

Request:

```json
{
  "id": "u-1",
  "password": "admin123"
}
```

Response:

```json
{
  "id": "u-1",
  "dbId": 1,
  "name": "Marina Costa",
  "email": "admin@aurora.local",
  "roleId": "administrador",
  "status": "Ativo"
}
```

### `POST /usuarios`

Cria usuário.

Request:

```json
{
  "name": "Novo Usuario",
  "email": "novo@aurora.local",
  "password": "senha123",
  "roleId": "analista",
  "status": "Ativo"
}
```

Validações:

- nome mínimo de 3 caracteres;
- email válido;
- email único;
- senha mínima de 6 caracteres;
- perfil válido;
- status válido.

### `PATCH /usuarios/<id>/status`

Atualiza status.

```json
{
  "status": "Inativo"
}
```

Regra: não é permitido inativar o último administrador ativo.

### `DELETE /usuarios/<id>`

Remove usuário.

Regra: não é permitido remover o último administrador ativo.

## Endpoints de Venda

### `POST /vendas`

Cadastra venda.

Request:

```json
{
  "cliente": "Cliente 1",
  "produto": "Mouse Gamer RGB",
  "quantidade": 2,
  "desconto": 10,
  "filial": "Filial Campinas",
  "data": "2026-05-20"
}
```

Response:

```json
{
  "id_venda": 10001,
  "numero_pedido": "PED-APP-20260520190000000000",
  "valor_bruto": 259.8,
  "desconto": 10.0,
  "valor_liquido": 249.8
}
```

## Endpoints de KPIs

Todos aceitam os parâmetros:

| Parâmetro | Descrição |
|---|---|
| `filial` | Nome da filial. |
| `produto` | Nome do produto. |
| `categoria` | Nome da categoria. |
| `inicio` | Data inicial. |
| `fim` | Data final. |

### `GET /faturamento`

Retorna faturamento bruto formatado.

### `GET /receita_liquida`

Retorna receita líquida.

### `GET /custo_total`

Retorna custo total.

### `GET /margem_bruta`

Retorna margem bruta.

### `GET /margem_bruta_percentual`

Retorna margem percentual média.

## Endpoints Analíticos

### `GET /pergunta_faturamento`

Retorna série mensal com receita bruta, descontos, receita líquida, quantidade vendida e vendas.

### `GET /pergunta_receita_liquida`

Retorna indicadores por filial.

### `GET /pergunta_receita_liquida_categoria`

Retorna indicadores por categoria.

### `GET /pergunta_produtos_vendidos`

Retorna produtos vendidos e receita.

### `GET /pergunta_margem_bruta`

Retorna margem por período, filial e categoria.

## Endpoints de Gráficos Legados

- `/grafico_receita_bruta`
- `/grafico_receita_liquida`
- `/grafico_margem_bruta_percentual`

São mantidos para compatibilidade com versões anteriores da interface.

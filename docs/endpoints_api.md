# Endpoints REST

Todos os endpoints `/api` retornam JSON padronizado.

Sucesso:

```json
{
  "success": true,
  "message": "Operacao realizada com sucesso.",
  "data": {}
}
```

Erro:

```json
{
  "success": false,
  "message": "Erro ao realizar operacao.",
  "error": "Detalhe tecnico do erro."
}
```

## Usuarios

| Metodo | Endpoint | Uso |
|---|---|---|
| GET | `/api/usuarios` | Lista usuarios. |
| POST | `/api/usuarios` | Cria usuario. |
| GET | `/api/usuarios/<id>` | Busca usuario. |
| PUT | `/api/usuarios/<id>` | Atualiza usuario. |
| DELETE | `/api/usuarios/<id>` | Remove usuario. |

## Produtos

| Metodo | Endpoint | Uso |
|---|---|---|
| GET | `/api/produtos` | Lista produtos. |
| POST | `/api/produtos` | Cria produto. |
| PUT | `/api/produtos/<id>` | Atualiza produto. |
| DELETE | `/api/produtos/<id>` | Remove produto sem vendas vinculadas. |

## Filiais E Categorias

| Metodo | Endpoint | Uso |
|---|---|---|
| GET | `/api/filiais` | Lista filiais. |
| POST | `/api/filiais` | Cria filial. |
| GET | `/api/clientes` | Lista clientes para venda. |
| GET | `/api/categorias` | Lista categorias. |
| POST | `/api/categorias` | Cria categoria. |
| GET | `/api/canais` | Lista canais ativos para venda. |

## Vendas

| Metodo | Endpoint | Uso |
|---|---|---|
| GET | `/api/vendas` | Lista vendas recentes. |
| POST | `/api/vendas` | Registra venda. |

## Dashboard

| Metodo | Endpoint | Uso |
|---|---|---|
| GET | `/api/dashboard/resumo` | KPIs resumidos. |
| GET | `/api/dashboard/vendas-mes` | Serie mensal. |
| GET | `/api/dashboard/produtos-ranking` | Ranking de produtos. |
| GET | `/api/dashboard/filiais` | Indicadores por filial. |

## Rotinas SQL

| Metodo | Endpoint | Uso |
|---|---|---|
| GET | `/api/banco/rotinas` | Lista triggers, procedures e functions existentes no schema `comercial`. |
| POST | `/api/banco/rotinas/executar-demo` | Executa `pr_refresh_kpis` e functions de demonstracao para comprovar o uso das rotinas. |

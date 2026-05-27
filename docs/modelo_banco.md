# Modelo Do Banco

O schema `comercial` usa PostgreSQL e modelagem dimensional para dashboards comerciais.

## Tabelas Principais

| Tabela | Objetivo |
|---|---|
| `dim_calendario` | Datas analiticas. |
| `dim_filial` | Cadastro de filiais. |
| `dim_categoria` | Categorias de produtos. |
| `dim_fornecedor` | Fornecedores comerciais. |
| `dim_produto` | Produtos, precos, custos e status. |
| `dim_cliente` | Clientes B2B/B2C. |
| `dim_canal_venda` | Canais de venda ativos/inativos. |
| `app_usuario` | Usuarios usados pelo login atual da aplicacao. |
| `usuarios` | Tabela academica de usuarios com `senha_hash`, `ativo` e timestamps. |
| `log_operacao` | Auditoria de operacoes. |
| `fato_vendas` | Cabecalho da venda. |
| `fato_itens_venda` | Itens vendidos. |
| `movimentacao_estoque` | Entradas, saidas e ajustes de estoque. |

## Relacionamentos

- `dim_categoria` 1:N `dim_produto`.
- `dim_fornecedor` 1:N `dim_produto`.
- `dim_calendario` 1:N `fato_vendas`.
- `dim_filial` 1:N `fato_vendas`.
- `dim_cliente` 1:N `fato_vendas`.
- `dim_canal_venda` 1:N `fato_vendas`.
- `app_usuario` 1:N `fato_vendas`.
- `fato_vendas` 1:N `fato_itens_venda`.
- `dim_produto` 1:N `fato_itens_venda`.
- `fato_itens_venda` gera `movimentacao_estoque`.

## Integridade

O banco usa chaves primarias, chaves estrangeiras, `UNIQUE`, `CHECK`, `NOT NULL`, `NUMERIC` para valores monetarios e `TIMESTAMP` para auditoria.


# Triggers, Procedures e Functions

## Triggers

| Trigger | Tabela | Momento | Evento | Objetivo |
|---|---|---|---|---|
| `trg_calcular_totais_item` | `fato_itens_venda` | BEFORE | INSERT, UPDATE | Impede quantidade invalida e calcula `valor_total` e `custo_total`. |
| `trg_validar_venda` | `fato_vendas` | BEFORE | INSERT, UPDATE | Valida desconto e recalcula `valor_liquido`. |
| `trg_auditar_usuario` | `app_usuario` | AFTER | INSERT, UPDATE, DELETE | Registra operacoes de usuarios em `log_operacao`. |
| `trg_auditar_venda` | `fato_vendas` | AFTER | INSERT, UPDATE, DELETE | Registra operacoes de vendas em `log_operacao`. |
| `trg_usuarios_updated_at` | `usuarios` | BEFORE | UPDATE | Atualiza `atualizado_em` automaticamente. |
| `trg_movimentar_estoque_venda` | `fato_itens_venda` | AFTER | INSERT | Cria movimentacao de estoque de saida apos item de venda. |

Exemplo:

```sql
INSERT INTO comercial.fato_itens_venda (
    id_venda, id_produto, quantidade, valor_unitario, custo_unitario, valor_total, custo_total
)
VALUES (1, 1, 2, 129.90, 70.00, 0, 0);
```

O banco calcula os totais automaticamente e registra movimentacao de estoque.

## Procedures e Functions

| Rotina | Tipo | Objetivo |
|---|---|---|
| `pr_cadastrar_usuario` | Procedure | Insere usuario validando nome, email e senha. |
| `pr_cadastrar_produto` | Procedure | Insere produto a partir do nome da categoria. |
| `pr_refresh_kpis` | Procedure | Atualiza a materialized view de KPIs. |
| `fn_calcular_receita_liquida` | Function | Calcula bruto menos desconto com validacao. |
| `fn_obter_ou_criar_data` | Function | Reusa ou cria data na dimensao calendario. |
| `fn_resumo_comercial_subqueries` | Function | Retorna indicadores calculados com subqueries. |
| `fn_faturamento_periodo` | Function | Calcula faturamento por periodo. |
| `fn_ranking_produtos` | Function | Retorna ranking de produtos vendidos. |

Exemplos:

```sql
CALL comercial.pr_cadastrar_usuario(
    'Novo Usuario',
    'novo@aurora.local',
    'senha123',
    'leitura_comercial',
    TRUE
);
```

```sql
SELECT comercial.fn_faturamento_periodo('2026-01-01', '2026-12-31');
```

```sql
SELECT * FROM comercial.fn_ranking_produtos(10);
```


# Dashboards

## Visão Geral

Os dashboards transformam dados da view `comercial.vm_kpis_comercial_mensal` em cards, tabelas e gráficos. O frontend usa filtros globais e consulta endpoints Flask que executam queries SQL agregadas.

## Filtros Globais

| Filtro | Campo enviado | Uso no SQL |
|---|---|---|
| Início | `inicio` | `periodo BETWEEN :inicio AND :fim` |
| Fim | `fim` | `periodo BETWEEN :inicio AND :fim` |
| Filial | `filial` | `nome_filial = :filial` |
| Categoria | `categoria` | `nome_categoria = :categoria` |
| Produto | `produto` | `nome_produto = :produto` |

## KPIs

| KPI | Origem | Interpretação |
|---|---|---|
| Receita total | `SUM(receita_liquida)` | Valor vendido após descontos. |
| Quantidade de vendas | `SUM(quantidade_de_vendas)` | Total de pedidos concluídos. |
| Ticket médio | Receita líquida / vendas | Receita média por pedido. |
| Produtos vendidos | `SUM(quantidade_vendida)` | Volume de unidades vendidas. |
| Melhor filial | Ranking por `receita_liquida` | Filial com maior desempenho. |
| Melhor categoria | Ranking por `receita_liquida` | Categoria com maior contribuição. |
| Total de clientes | `/clientes` | Quantidade de clientes carregados na interface. |
| Margem bruta | `SUM(margem_bruta)` | Ganho após custo dos produtos. |

## Dashboard Geral

Objetivo: visão executiva do desempenho comercial.

Componentes:

- cards de receita, vendas, ticket, produtos, melhor filial, melhor categoria, clientes e margem;
- gráfico de evolução da receita;
- gráfico de receita por filial;
- gráfico de receita por categoria;
- gráfico de produtos mais vendidos.

Consultas utilizadas:

- `/faturamento`
- `/receita_liquida`
- `/custo_total`
- `/margem_bruta`
- `/margem_bruta_percentual`
- `/pergunta_faturamento`
- `/pergunta_receita_liquida`
- `/pergunta_receita_liquida_categoria`
- `/pergunta_produtos_vendidos`

## Dashboard de Vendas

Objetivo: acompanhar evolução mensal de vendas.

Indicadores:

- receita bruta;
- descontos;
- receita líquida;
- quantidade de vendas;
- produtos vendidos.

Gráficos:

- barras por quantidade de vendas no mês;
- linha de evolução da receita líquida.

Tabela:

| Coluna | Descrição |
|---|---|
| Período | Mês de referência. |
| Receita bruta | Total bruto vendido. |
| Descontos | Desconto total aplicado. |
| Receita líquida | Bruto menos desconto. |
| Vendas | Total de pedidos. |

## Dashboard por Filial

Objetivo: comparar performance entre filiais.

Origem:

```sql
SELECT nome_filial, SUM(receita_liquida), AVG(margem_bruta_percentual)
FROM comercial.vm_kpis_comercial_mensal
GROUP BY nome_filial;
```

Gráficos:

- barras de receita líquida por filial.

Tabela:

- filial;
- receita líquida;
- margem média.

## Dashboard por Categoria

Objetivo: identificar categorias com melhor desempenho.

Origem:

```sql
SELECT nome_categoria, SUM(quantidade_vendida), SUM(receita_liquida), AVG(margem_bruta_percentual)
FROM comercial.vm_kpis_comercial_mensal
GROUP BY nome_categoria;
```

Visualizações:

- gráfico doughnut de participação;
- tabela de categoria, quantidade vendida, receita líquida e margem.

## Relatórios

Objetivo: visão resumida para análise gerencial.

Componentes:

- cards de receita, margem, filial e categoria;
- gráfico de receita por filial;
- gráfico de receita por categoria.

## Produtos

Origem:

- `comercial.dim_produto`;
- `comercial.dim_categoria`;
- `comercial.vm_kpis_comercial_mensal`.

Mostra:

- produto;
- categoria;
- marca;
- preço;
- status;
- receita.

## Clientes

Origem:

- `comercial.dim_cliente`.

Mostra:

- nome;
- tipo;
- cidade;
- UF;
- data de cadastro.

## Interpretação dos Indicadores

| Indicador | Como interpretar |
|---|---|
| Receita líquida alta | Bom volume comercial após descontos. |
| Margem percentual baixa | Pode indicar custo alto ou desconto excessivo. |
| Ticket médio alto | Clientes compram mais por pedido. |
| Quantidade vendida alta | Forte saída operacional do produto/categoria. |
| Desconto alto | Avaliar política comercial e impacto na margem. |

## Fallback

Quando o banco falha, a interface exibe o alerta superior de indisponibilidade e mostra a mensagem de erro na área principal. O fluxo atual não usa dados demonstrativos locais como fallback.

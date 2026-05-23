# Regras de Negócio

## Domínio

O sistema representa uma operação comercial com:

- filiais;
- categorias;
- produtos;
- clientes;
- vendas;
- itens de venda;
- usuários da aplicação;
- dashboards gerenciais.

## Regras de Produto

- Produto deve pertencer a uma categoria.
- Produto possui preço de venda e custo.
- Produto pode estar ativo ou inativo.
- O dashboard considera produtos na view de KPIs e no catálogo.

## Regras de Cliente

- Cliente possui nome e tipo.
- Tipos usados: `B2B` e `B2C`.
- Cliente pode estar associado a vendas.

## Regras de Venda

- Venda deve possuir data, filial, cliente, produto, quantidade e desconto.
- Quantidade deve ser maior que zero.
- Desconto não pode ser negativo.
- Desconto não pode ultrapassar valor bruto.
- Venda cadastrada pela interface assume `forma_pagamento = PIX`.
- Venda cadastrada pela interface assume `status_venda = CONCLUIDA`.
- Após venda, a materialized view de KPIs é atualizada.

## Cálculos Financeiros

| Campo | Fórmula |
|---|---|
| Valor bruto | `preco_venda * quantidade` |
| Desconto | Valor informado, limitado ao bruto |
| Valor líquido | `valor_bruto - desconto` |
| Custo total | `custo_produto * quantidade` |
| Margem bruta | `receita_liquida - custo_total` |
| Margem percentual | `margem_bruta / receita_liquida * 100` |

## Regras de Usuário

- Nome deve ter pelo menos 3 caracteres.
- Email deve ter formato válido.
- Email deve ser único.
- Senha deve ter pelo menos 6 caracteres.
- Perfil deve ser um dos valores permitidos:
  - `admin_comercial`
  - `gerente_comercial`
  - `operador_comercial`
  - `leitura_comercial`
- Status deve ser:
  - `Ativo`
  - `Inativo`
- Usuário inativo não pode autenticar.
- O último `admin_comercial` ativo não pode ser inativado.
- O último `admin_comercial` ativo não pode ser removido.

## Regras de Permissão

- Admin Comercial possui acesso completo.
- Gerente Comercial visualiza dashboards, consultas e relatórios.
- Operador Comercial cadastra vendas e consulta telas operacionais.
- Leitura Comercial apenas consulta dashboards e relatórios.
- A navegação é controlada visualmente no frontend.
- Rotas backend sensíveis validam sessão e permissão por perfil.

## Regras de Dashboard

- KPIs consideram vendas concluídas.
- Filtros de data só são aplicados quando início e fim são informados.
- Filtros vazios retornam visão geral.
- A interface exibe aviso quando o banco falha e não substitui a API por dados locais.

## Regras Técnicas

- Toda sessão de banco deve ser fechada.
- Escritas devem usar `commit`.
- Falhas em escrita devem usar `rollback`.
- Queries devem usar parâmetros SQLAlchemy, não concatenação de valores do usuário.

## Melhorias Futuras

- Centralização da matriz de permissões.
- Hash de senha.
- Auditoria de operações.
- Controle real de operador por venda.
- Campo de forma de pagamento no formulário.
- Suporte a múltiplos itens por venda.

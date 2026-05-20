# Backend

## Visão Geral

O backend é implementado em Flask e atua como API JSON para a interface web. Ele também renderiza a página inicial por meio de `base.html`.

## Arquivos Principais

| Arquivo | Descrição |
|---|---|
| `run.py` | Ponto de entrada local da aplicação. |
| `app/__init__.py` | Factory `create_app()`, registro de rotas e tratamento global de `OperationalError`. |
| `app/config.py` | Carrega variáveis de ambiente com `python-dotenv`. |
| `app/db.py` | Configura SQLAlchemy engine e `SessionLocal`. |
| `app/routes.py` | Define endpoints HTTP. |
| `app/services/bi_queries.py` | Implementa consultas SQL e regras de negócio. |

## Inicialização

```python
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
```

## Configuração

O backend usa `.env`:

```env
DB_HOST=localhost
DB_PORT=5782
DB_NAME=bi_comercial_db
DB_USER=bi_user
DB_PASSWORD=bi_pass
```

## Conexão com Banco

`app/db.py` monta a URL:

```text
postgresql+psycopg://bi_user:bi_pass@localhost:5782/bi_comercial_db
```

As rotas chamam:

```python
session = get_session()
try:
    ...
finally:
    session.close()
```

## Uso de SQLAlchemy

O projeto não usa models declarativos. O SQLAlchemy é usado para:

- criação da engine;
- gerenciamento de pool;
- criação de sessões;
- execução de SQL textual com `text()`;
- passagem segura de parâmetros.

Exemplo:

```python
query, params = bi_queries.get_faturamento(filial, produto, categoria, inicio, fim)
result = session.execute(query, params).fetchone()
```

## Rotas Principais

| Rota | Método | Função |
|---|---|---|
| `/` | GET | Renderiza a interface e testa banco. |
| `/filiais` | GET | Lista filiais. |
| `/categorias` | GET | Lista categorias. |
| `/produtos` | GET | Lista nomes de produtos. |
| `/produtos_detalhados` | GET | Lista catálogo detalhado. |
| `/clientes` | GET | Lista clientes. |
| `/usuarios` | GET | Lista usuários da aplicação. |
| `/auth/login` | POST | Autentica usuário por id e senha. |
| `/usuarios` | POST | Cria usuário. |
| `/usuarios/<id>/status` | PATCH | Atualiza status do usuário. |
| `/usuarios/<id>` | DELETE | Remove usuário. |
| `/vendas` | POST | Registra nova venda. |
| `/faturamento` | GET | Retorna faturamento bruto. |
| `/receita_liquida` | GET | Retorna receita líquida. |
| `/custo_total` | GET | Retorna custo total. |
| `/margem_bruta` | GET | Retorna margem bruta. |
| `/margem_bruta_percentual` | GET | Retorna percentual médio de margem. |

## Services

`bi_queries.py` tem três grupos principais:

| Grupo | Funções |
|---|---|
| Filtros e cadastros | `get_filiais`, `get_produtos`, `get_categorias`, `get_clientes`. |
| KPIs e perguntas | `get_faturamento`, `get_receitaLiquida`, `pergunta_faturamento`, etc. |
| Escrita e validação | `criar_venda`, `criar_usuario`, `autenticar_usuario`, `remover_usuario`. |

## Tratamento de Erros

O backend usa blocos `try/except/finally` por rota:

- `ValueError`: retorna erro de validação com status 400, 401 ou 404 conforme contexto.
- `Exception`: retorna status 500.
- `OperationalError`: handler global em `app/__init__.py` retorna 503.

## Autenticação

O endpoint `/auth/login` recebe:

```json
{
  "id": "u-1",
  "password": "admin123"
}
```

Retorna:

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

Limitação atual: não há token, cookie de sessão ou middleware de autorização backend.

## Cadastro de Venda

Fluxo da função `criar_venda`:

1. Busca produto, filial e cliente.
2. Valida existência.
3. Calcula bruto, desconto, líquido e custo.
4. Garante data em `dim_calendario`.
5. Insere em `fato_vendas`.
6. Insere em `fato_itens_venda`.
7. Executa `REFRESH MATERIALIZED VIEW`.

## Logs

O projeto não possui logs estruturados próprios. Em desenvolvimento, erros aparecem no console Flask. Para produção, recomenda-se:

- configurar logging do Gunicorn;
- registrar exceções com contexto;
- criar logs de auditoria para criação de usuários e vendas.

## Recomendações

- Mover senhas para hash.
- Adicionar `Flask-Login` ou JWT.
- Criar decorators de permissão nas rotas sensíveis.
- Adicionar testes com `pytest`.
- Criar migrations.

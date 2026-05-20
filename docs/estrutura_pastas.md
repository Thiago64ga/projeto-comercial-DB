# Estrutura de Pastas

## Árvore Geral

```text
projeto-comercial-DB/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── db.py
│   ├── routes.py
│   ├── services/
│   │   └── bi_queries.py
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── script.js
│   └── templates/
│       └── base.html
├── db/
│   ├── init/
│   │   └── cria_banco.sql
│   └── docs/
│       └── modelo_banco.md
├── docs/
├── infra/
│   └── docker/
│       ├── docker-compose.yml
│       ├── README.md
│       └── criar_database.txt
├── requirements.txt
├── run.py
└── README.md
```

## `app/`

Contém a aplicação Flask.

| Arquivo | Responsabilidade |
|---|---|
| `__init__.py` | Factory da aplicação e handler global de erro. |
| `config.py` | Leitura de variáveis de ambiente. |
| `db.py` | Conexão SQLAlchemy. |
| `routes.py` | Rotas Flask e controllers. |

## `app/services/`

Camada de serviços e SQL.

| Arquivo | Responsabilidade |
|---|---|
| `bi_queries.py` | Consultas de dashboard, usuários, clientes, produtos e vendas. |

## `app/static/`

Arquivos servidos diretamente ao navegador.

| Pasta | Conteúdo |
|---|---|
| `css` | Estilos visuais. |
| `js` | Lógica da interface. |

## `app/templates/`

Templates Flask/Jinja.

| Arquivo | Função |
|---|---|
| `base.html` | Estrutura base da aplicação. |

## `db/`

Scripts e documentação de banco.

| Caminho | Função |
|---|---|
| `db/init/cria_banco.sql` | Criação do schema, tabelas, dados, índices e views. |
| `db/docs/modelo_banco.md` | Documentação histórica do modelo. |

## `docs/`

Documentação técnica do projeto.

| Documento | Tema |
|---|---|
| `arquitetura.md` | Arquitetura geral. |
| `backend.md` | Backend Flask. |
| `frontend.md` | Interface web. |
| `database.md` | Banco de dados. |
| `permissoes.md` | Perfis e acesso. |
| `dashboard.md` | Dashboards e KPIs. |
| `api.md` | Endpoints. |
| `instalacao.md` | Configuração local. |
| `deploy.md` | Publicação. |
| `manutencao.md` | Evolução do projeto. |

## `infra/`

Infraestrutura local.

| Arquivo | Função |
|---|---|
| `docker-compose.yml` | Container PostgreSQL. |
| `README.md` | Orientações locais de Docker. |
| `criar_database.txt` | Notas auxiliares. |

## Arquivos de Raiz

| Arquivo | Função |
|---|---|
| `README.md` | Entrada principal da documentação. |
| `requirements.txt` | Dependências Python. |
| `run.py` | Execução local Flask. |
| `.env` | Variáveis de ambiente. |

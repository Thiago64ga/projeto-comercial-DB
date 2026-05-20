# Arquitetura do Sistema

## Visão Geral

O Rede Comercial Aurora BI é uma aplicação web monolítica em Flask, com frontend renderizado por template HTML e comportamento dinâmico em JavaScript. O backend expõe endpoints JSON que consultam e gravam dados em PostgreSQL. A camada de serviços centraliza as queries SQL em `app/services/bi_queries.py`.

## Componentes

| Componente | Arquivo/Pasta | Responsabilidade |
|---|---|---|
| Entrada Flask | `run.py` | Inicializa a aplicação criada por `create_app()`. |
| Factory Flask | `app/__init__.py` | Cria a aplicação, registra rotas e handler global de erro de banco. |
| Configuração | `app/config.py` | Carrega variáveis do `.env`. |
| Banco | `app/db.py` | Cria engine SQLAlchemy e sessões. |
| Rotas | `app/routes.py` | Controllers HTTP e serialização JSON. |
| Services | `app/services/bi_queries.py` | Queries SQL, regras de validação e operações de escrita. |
| Template | `app/templates/base.html` | Estrutura HTML da interface. |
| Frontend | `app/static/js/script.js` | Estado da interface, chamadas API, permissões e gráficos. |
| Estilos | `app/static/css/style.css` | Layout, componentes, responsividade e aparência visual. |
| Banco SQL | `db/init/cria_banco.sql` | DDL, DML, índices, views e usuários iniciais. |
| Infra | `infra/docker/docker-compose.yml` | PostgreSQL local em container. |

## Diagrama de Componentes

```mermaid
flowchart TB
    subgraph Client["Cliente"]
        Browser["Navegador"]
        HTML["base.html"]
        CSS["style.css"]
        JS["script.js"]
        Chart["Chart.js CDN"]
    end

    subgraph Flask["Aplicação Flask"]
        App["create_app"]
        Routes["routes.py"]
        Services["bi_queries.py"]
        DBSession["db.py / SQLAlchemy Session"]
    end

    subgraph Database["PostgreSQL"]
        Dims["Dimensões"]
        Facts["Fatos"]
        Users["app_usuario"]
        View["vm_kpis_comercial_mensal"]
    end

    Browser --> HTML
    HTML --> CSS
    HTML --> JS
    JS --> Chart
    JS --> Routes
    Routes --> Services
    Services --> DBSession
    DBSession --> Database
    Facts --> View
    Dims --> View
```

## Padrão Arquitetural

O projeto se aproxima de MVC com services:

| Papel | Implementação |
|---|---|
| Model | Tabelas e views PostgreSQL, acessadas por SQL textual. |
| View | `base.html`, CSS e renderizações dinâmicas em JavaScript. |
| Controller | Rotas Flask em `routes.py`. |
| Service | `bi_queries.py`, contendo SQL, validações e regras de persistência. |

Não há ORM declarativo com classes de modelo. O SQLAlchemy é usado para engine, pool, sessões e execução de SQL parametrizado.

## Comunicação Frontend/Backend

O frontend usa `fetch()` para consultar endpoints JSON:

```mermaid
sequenceDiagram
    participant U as Usuário
    participant JS as script.js
    participant API as Flask routes.py
    participant S as bi_queries.py
    participant DB as PostgreSQL

    U->>JS: Aplica filtros
    JS->>API: GET /faturamento?filial=&categoria=&...
    API->>S: get_faturamento(...)
    S->>DB: SELECT SUM(faturamento_bruto)
    DB-->>S: Resultado
    S-->>API: Query + params
    API-->>JS: JSON
    JS-->>U: Atualiza cards/gráficos
```

## Comunicação com Banco

A conexão é configurada em `app/db.py`:

```python
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={"connect_timeout": 1}
)
```

Características:

- `pool_pre_ping=True`: detecta conexões mortas.
- `pool_recycle=300`: recicla conexões antigas.
- `connect_timeout=1`: evita travamento prolongado em caso de banco indisponível.
- sessões são abertas por rota e fechadas no `finally`.

## Fluxo de Autenticação

```mermaid
sequenceDiagram
    participant U as Usuário
    participant UI as Role Bar
    participant API as /auth/login
    participant DB as app_usuario

    U->>UI: Seleciona usuário e informa senha
    UI->>API: POST /auth/login
    API->>DB: Busca id + senha
    DB-->>API: Usuário encontrado
    API-->>UI: Dados do usuário sem senha
    UI->>UI: Atualiza perfil ativo e permissões visuais
```

Observação: a autenticação atual é funcional para o escopo do projeto, mas ainda não cria sessão server-side. O controle de telas é feito no frontend.

## Fluxo de Permissões

As permissões são declaradas em `roleProfiles` no `script.js`. Cada tela possui uma permissão exigida no array `screens`.

```mermaid
flowchart TD
    A[Usuário autenticado] --> B[roleId]
    B --> C[roleProfiles]
    C --> D[Lista de permissões]
    D --> E{Tela permitida?}
    E -->|Sim| F[Renderiza tela]
    E -->|Não| G[Renderiza acesso negado]
```

## Fluxo dos Dashboards

1. `loadDashboardData()` monta query string com filtros globais.
2. A aplicação consulta endpoints de KPIs e tabelas.
3. Dados são normalizados no frontend.
4. Cards são renderizados por `renderKpis()`.
5. Gráficos são renderizados por `renderCharts()` com Chart.js.

## Rotas

As rotas estão em `app/routes.py` e funcionam como controllers:

- recebem parâmetros HTTP;
- abrem sessão no banco;
- chamam funções em `bi_queries.py`;
- serializam resultados em JSON;
- fazem `commit`, `rollback` ou `close`.

## Services

`bi_queries.py` concentra:

- queries de KPIs;
- consultas auxiliares de filtros;
- validações de usuários;
- criação de venda;
- refresh da materialized view;
- criação automática da tabela `app_usuario` quando necessário.

## Templates e Assets

`base.html` define o shell da aplicação:

- alerta de banco indisponível;
- sidebar;
- Role Bar;
- navegação principal;
- filtros globais;
- área dinâmica `#viewRoot`.

`script.js` injeta os conteúdos de tela em `#viewRoot`.

## Integrações

| Integração | Uso |
|---|---|
| PostgreSQL | Armazenamento transacional e analítico. |
| Chart.js CDN | Renderização de gráficos. |
| Docker Compose | Banco local para desenvolvimento. |
| python-dotenv | Configuração de ambiente. |

## Pontos de Evolução Arquitetural

- Adicionar autenticação server-side com sessões.
- Criar camada repository para separar SQL de regras.
- Usar migrations com Alembic.
- Implementar testes automatizados.
- Proteger permissões também no backend.
- Remover dependência de CDN em ambientes restritos.

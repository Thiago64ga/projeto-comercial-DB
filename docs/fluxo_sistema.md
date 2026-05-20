# Fluxo do Sistema

## Fluxo de Inicialização

```mermaid
sequenceDiagram
    participant Dev as Desenvolvedor
    participant Flask as Flask
    participant DB as PostgreSQL
    participant Browser as Navegador

    Dev->>Flask: python run.py
    Flask->>Flask: create_app()
    Flask->>DB: SELECT 1
    DB-->>Flask: OK ou erro
    Browser->>Flask: GET /
    Flask-->>Browser: base.html
    Browser->>Browser: Carrega CSS e JS
```

## Fluxo de Carregamento de Dados

1. `init()` executa no frontend.
2. `loadUsers()` consulta `/usuarios`.
3. `loadSelects()` consulta `/filiais` e `/categorias`.
4. `loadProducts()` consulta `/produtos`.
5. `refreshData()` consulta endpoints de KPIs.
6. `render()` monta a tela atual.

## Fluxo de Login

```mermaid
flowchart TD
    A[Selecionar usuário] --> B[Digitar senha]
    B --> C[POST /auth/login]
    C --> D{Credenciais válidas?}
    D -->|Sim| E[Atualiza currentUserId]
    E --> F[Recalcula permissões]
    F --> G[Renderiza tela permitida]
    D -->|Não| H[Exibe erro]
```

## Fluxo de Dashboard

```mermaid
flowchart TD
    A[Usuário aplica filtros] --> B[buildParams]
    B --> C[Chamadas Promise.all]
    C --> D[Flask routes.py]
    D --> E[bi_queries.py]
    E --> F[(PostgreSQL)]
    F --> G[JSON]
    G --> H[Normalização no frontend]
    H --> I[Cards, tabelas e gráficos]
```

## Fluxo de Nova Venda

1. Usuário acessa tela "Nova Venda".
2. Seleciona cliente, produto, filial e data.
3. Informa quantidade e desconto.
4. Frontend envia `POST /vendas`.
5. Backend valida campos obrigatórios.
6. Service busca produto, filial e cliente.
7. Calcula valores monetários.
8. Insere venda em `fato_vendas`.
9. Insere item em `fato_itens_venda`.
10. Atualiza `vm_kpis_comercial_mensal`.
11. Frontend recarrega dashboards.

## Fluxo de Usuários

### Criação

```mermaid
sequenceDiagram
    participant UI as Tela de Usuários
    participant API as POST /usuarios
    participant S as bi_queries.py
    participant DB as app_usuario

    UI->>API: Dados do novo usuário
    API->>S: criar_usuario
    S->>S: Valida nome, email, senha, perfil e status
    S->>DB: INSERT
    DB-->>S: Usuário criado
    S-->>API: Dados sem senha
    API-->>UI: 201 Created
```

### Alteração de Status

Regras:

- status permitido: `Ativo`, `Inativo`;
- não inativar último administrador ativo.

### Remoção

Regra:

- não remover último administrador ativo.

## Fluxo de Fallback

Quando uma chamada opcional falha:

1. `fetchOptional()` captura erro.
2. `state.usingMock = true`.
3. A interface usa dados demonstrativos.
4. O alerta de banco indisponível é exibido.

## Fluxo de Manutenção de View

Após cadastro de venda:

```sql
REFRESH MATERIALIZED VIEW comercial.vm_kpis_comercial_mensal;
```

Isso garante que os dashboards reflitam a venda recém-inserida.

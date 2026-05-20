# Permissões e Autenticação

## Visão Geral

O sistema possui quatro perfis funcionais:

- Administrador
- Gerente
- Vendedor
- Analista

As permissões são declaradas no frontend em `roleProfiles`, dentro de `app/static/js/script.js`. Os usuários da aplicação são persistidos no banco na tabela `comercial.app_usuario`.

## Usuários Padrão

| Perfil | Email | Senha | Status |
|---|---|---|---|
| Administrador | `admin@aurora.local` | `admin123` | Ativo |
| Gerente | `gerente@aurora.local` | `gerente123` | Ativo |
| Vendedor | `vendedor@aurora.local` | `vendedor123` | Ativo |
| Analista | `analista@aurora.local` | `analista123` | Ativo |

## Perfis

### Administrador

Permissões completas:

- visualizar todos os dashboards;
- visualizar produtos, clientes, filiais, vendas e relatórios;
- cadastrar vendas;
- gerenciar usuários;
- criar usuários;
- editar status de usuários;
- remover usuários;
- visualizar matriz de permissões.

### Gerente

Permissões:

- visualizar dashboards;
- visualizar produtos, clientes, filiais e vendas;
- gerenciar usuários;
- criar usuários;
- remover usuários;
- visualizar relatórios.

Restrição:

- não possui permissão explícita para editar status no mapa atual do frontend.

### Vendedor

Permissões:

- visualizar dashboard de vendas;
- visualizar produtos;
- visualizar clientes;
- cadastrar novas vendas;
- consultar somente sua visão operacional.

Restrição atual:

- o frontend reduz visualmente a visão de vendas para um recorte, mas não há filtro backend por vendedor autenticado.

### Analista

Permissões:

- visualizar dashboards;
- visualizar produtos, clientes, filiais e vendas;
- visualizar relatórios.

Restrições:

- não cria vendas;
- não gerencia usuários;
- não altera cadastros.

## Matriz de Permissões

| Tela/Função | Administrador | Gerente | Vendedor | Analista |
|---|---:|---:|---:|---:|
| Dashboard geral | Sim | Sim | Não | Sim |
| Dashboard de vendas | Sim | Sim | Sim | Sim |
| Dashboard por filial | Sim | Sim | Não | Sim |
| Dashboard por categoria | Sim | Sim | Não | Sim |
| Nova venda | Sim | Não | Sim | Não |
| Produtos | Sim | Sim | Sim | Sim |
| Clientes | Sim | Sim | Sim | Sim |
| Gerenciar usuários | Sim | Sim | Não | Não |
| Criar usuário | Sim | Sim | Não | Não |
| Editar usuário | Sim | Não | Não | Não |
| Remover usuário | Sim | Sim | Não | Não |
| Permissões | Sim | Não | Não | Não |
| Relatórios | Sim | Sim | Não | Sim |

## Fluxo da Troca de Usuário

```mermaid
sequenceDiagram
    participant U as Usuário
    participant UI as Role Bar
    participant API as Flask
    participant DB as app_usuario

    U->>UI: Seleciona usuário
    U->>UI: Digita senha
    UI->>API: POST /auth/login
    API->>DB: Valida id + senha
    DB-->>API: Usuário ativo
    API-->>UI: Dados do usuário
    UI->>UI: Atualiza perfil e permissões
```

## Controle de Telas

Cada item de navegação possui uma permissão:

```javascript
{ id: "dashboard-geral", permission: "dashboard:geral" }
```

Antes de renderizar uma tela, o frontend executa:

```javascript
hasPermission(state.currentScreenId)
```

Se não houver acesso, a tela `renderDenied()` é exibida.

## Controle de Botões

Botões de ação são renderizados condicionalmente:

```javascript
const canCreate = can("usuarios:criar");
const canEdit = can("usuarios:editar");
const canRemove = can("usuarios:remover");
```

## Validações Backend

O backend valida:

- nome mínimo de usuário;
- email em formato válido;
- email único;
- senha mínima;
- perfil permitido;
- status permitido;
- bloqueio de inativação do último administrador ativo;
- bloqueio de remoção do último administrador ativo.

## Proteção de Rotas

Estado atual:

- as rotas existem e validam dados;
- a autorização fina por perfil ainda não é aplicada no backend;
- o controle principal de acesso é visual no frontend.

Melhoria recomendada:

- adicionar sessão Flask;
- criar decorator `@require_permission`;
- validar usuário logado antes de mutações;
- armazenar senha com hash.

## Middleware

Não há middleware customizado de autenticação. O handler global existente trata `OperationalError` de banco.

## DCL do PostgreSQL

O script de banco pode conter roles PostgreSQL como:

- `admin_comercial`;
- `gerente_comercial`;
- `operador_comercial`;
- `leitura_comercial`.

Essas roles controlam permissões no banco, enquanto `app_usuario` controla perfis da aplicação.

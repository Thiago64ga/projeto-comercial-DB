# Frontend

## Visão Geral

O frontend é uma single page interface construída com HTML, CSS e JavaScript puro. O Flask entrega `login.html` para autenticação e `base.html` para a área principal. O `script.js` controla navegação, sessão atual, chamadas API, renderização de telas, tabelas e gráficos.

## Arquivos

| Arquivo | Função |
|---|---|
| `app/templates/login.html` | Tela de login por e-mail e senha. |
| `app/templates/base.html` | Estrutura principal da página. |
| `app/static/css/style.css` | Estilos, layout, responsividade e componentes. |
| `app/static/js/script.js` | Estado, permissões, API, renderização e eventos. |

## Layout

A interface possui:

- alerta superior de banco indisponível;
- sidebar fixa;
- marca "Aurora BI";
- painel de sessão com usuário logado e logout;
- menu de navegação;
- área principal de trabalho;
- filtros globais;
- raiz dinâmica `#viewRoot`.

```mermaid
flowchart LR
    A[Sidebar] --> B[Painel de sessão]
    A --> C[Menu]
    D[Workspace] --> E[Topbar / Filtros]
    D --> F[viewRoot]
    F --> G[Cards]
    F --> H[Gráficos]
    F --> I[Tabelas]
    F --> J[Formulários]
```

## Componentes

| Componente | Implementação |
|---|---|
| Sidebar | HTML fixo em `base.html`, estilizado por `.sidebar`. |
| Login | Formulário de e-mail e senha em `login.html`. |
| Painel de sessão | Mostra usuário/perfil logado e link de saída. |
| Navbar | Gerada por `renderNav()`. |
| Filtros | Inputs de data e selects de filial, categoria e produto. |
| Cards KPI | Criados por `card()` e `renderKpis()`. |
| Gráficos | Criados por `renderCharts()` com Chart.js. |
| Tabelas | Criadas por helper `table()`. |
| Formulários | Usuário e nova venda. |

## Estado da Interface

O objeto `state` centraliza:

| Campo | Descrição |
|---|---|
| `currentUserId` | Usuário autenticado atualmente. |
| `currentScreenId` | Tela ativa. |
| `charts` | Instâncias Chart.js para destruição antes de redesenhar. |
| `data` | Dados normalizados dos dashboards. |
| `users` | Usuários carregados de `/usuarios`. |
| `currentUser` | Usuário autenticado retornado por `/auth/me`. |
| `apiFiliais` | Filiais vindas do banco. |
| `apiProducts` | Produtos detalhados. |
| `apiClients` | Clientes. |
| `dbUnavailable` | Indica falha de banco/API e exibe aviso visual. |

## Permissões Visuais

As permissões são definidas em `roleProfiles`:

```javascript
const roleProfiles = {
    admin_comercial: { permissions: ["dashboard:geral", "usuarios:gerenciar"] },
    gerente_comercial: { permissions: ["dashboard:geral", "relatorios:ver"] },
    operador_comercial: { permissions: ["dashboard:vendas", "vendas:criar"] },
    leitura_comercial: { permissions: ["dashboard:geral", "relatorios:ver"] }
};
```

Cada tela em `screens` exige uma permissão.

## Autenticação na Interface

Fluxo:

1. Usuário acessa `/login`.
2. Envia e-mail e senha para `/auth/login`.
3. O backend cria sessão Flask e redireciona para `/`.
4. `loadCurrentUser()` consulta `/auth/me`.
5. A UI recalcula permissões e renderiza a primeira tela permitida.

## Gráficos

Biblioteca: Chart.js via CDN.

Tipos utilizados:

- `line`: evolução temporal.
- `bar`: rankings e comparações.
- `doughnut`: participação por categoria.

Antes de renderizar uma nova tela, `clearCharts()` destrói instâncias antigas para evitar sobreposição.

## Tabelas

As tabelas são criadas com:

```javascript
function table(headers, rows) {
    return `
        <div class="table-wrap">
            <table>...</table>
        </div>
    `;
}
```

## Formulários

### Cadastro de Usuário

Campos:

- nome;
- email;
- senha;
- perfil;
- status.

Backend: `POST /usuarios`.

### Nova Venda

Campos:

- cliente;
- produto;
- quantidade;
- desconto;
- filial;
- data.

Backend: `POST /vendas`.

## Responsividade

O CSS define:

- grid principal com sidebar e workspace;
- cards em grid responsivo;
- filtros em grid;
- tabelas em wrapper para overflow;
- raio de borda consistente em 8px.

## Banco Indisponível

Se endpoints falham, a interface ativa `state.dbUnavailable`, exibe o alerta superior e mostra uma mensagem de banco indisponível na área principal. Os dados demonstrativos locais foram removidos do fluxo de fallback.

## Pontos de Atenção

- O controle de permissões visual complementa as validações backend das ações sensíveis.
- As senhas de teste ainda são armazenadas em texto puro no banco para ambiente didático.
- Chart.js depende de internet por CDN.
- O frontend não usa framework; manutenções devem preservar funções pequenas e renderização por tela.

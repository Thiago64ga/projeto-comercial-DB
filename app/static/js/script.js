const roleProfiles = {
    admin_comercial: {
        name: "Administrador",
        description: "Pode criar, editar e remover usuarios; visualiza todos os dados e dashboards.",
        forcedFilial: "",
        permissions: [
            "dashboard:geral", "dashboard:vendas", "dashboard:filial", "dashboard:categoria",
            "produtos:ver", "clientes:ver", "filiais:ver", "vendas:ver:todas", "vendas:criar",
            "usuarios:gerenciar", "usuarios:criar", "usuarios:editar", "usuarios:remover",
            "permissoes:ver", "relatorios:ver", "dados:todos"
        ]
    },
    gerente_comercial: {
        name: "Gerente Comercial",
        description: "Visualiza dashboards, vendas, produtos, clientes, filiais e relatorios.",
        forcedFilial: "",
        permissions: [
            "dashboard:geral", "dashboard:vendas", "dashboard:filial", "dashboard:categoria",
            "produtos:ver", "clientes:ver", "filiais:ver", "vendas:ver:todas", "relatorios:ver"
        ]
    },
    operador_comercial: {
        name: "Operador Comercial",
        description: "Pode adicionar vendas, visualizar produtos, clientes e dashboards permitidos.",
        forcedFilial: "",
        permissions: ["dashboard:vendas", "produtos:ver", "clientes:ver", "vendas:ver:proprias", "vendas:criar"]
    },
    leitura_comercial: {
        name: "Leitura Comercial",
        description: "Pode apenas visualizar indicadores e relatorios. Nao cadastra, edita ou remove dados.",
        forcedFilial: "",
        permissions: [
            "dashboard:geral", "dashboard:vendas", "dashboard:filial", "dashboard:categoria",
            "relatorios:ver"
        ]
    }
};

const screens = [
    { id: "dashboard-geral", label: "Dashboard geral", icon: "DG", permission: "dashboard:geral" },
    { id: "dashboard-vendas", label: "Dashboard de vendas", icon: "$", permission: "dashboard:vendas" },
    { id: "dashboard-filial", label: "Dashboard por filial", icon: "F", permission: "dashboard:filial" },
    { id: "dashboard-categoria", label: "Dashboard por categoria", icon: "C", permission: "dashboard:categoria" },
    { id: "nova-venda", label: "Nova Venda", icon: "+", permission: "vendas:criar" },
    { id: "produtos", label: "Produtos", icon: "P", permission: "produtos:ver" },
    { id: "clientes", label: "Clientes", icon: "CL", permission: "clientes:ver" },
    { id: "gerenciar-usuarios", label: "Gerenciar Usuarios", icon: "U", permission: "usuarios:gerenciar" },
    { id: "permissoes", label: "Permissoes", icon: "A", permission: "permissoes:ver" },
    { id: "relatorios", label: "Relatorios", icon: "R", permission: "relatorios:ver" }
];

const legacyRoleIds = {
    administrador: "admin_comercial",
    gerente: "gerente_comercial",
    vendedor: "operador_comercial",
    analista: "leitura_comercial"
};

const state = {
    currentUserId: "",
    currentScreenId: "dashboard-geral",
    charts: [],
    data: null,
    users: [],
    currentUser: null,
    apiFiliais: [],
    apiProducts: [],
    apiClients: [],
    dbUnavailable: false
};

const els = {
    roleDescription: document.getElementById("roleDescription"),
    mainNav: document.getElementById("mainNav"),
    pageTitle: document.getElementById("pageTitle"),
    viewRoot: document.getElementById("viewRoot"),
    dbAlert: document.getElementById("alerta-banco-fora"),
    filialSelect: document.getElementById("filialSelect"),
    categoriaSelect: document.getElementById("categoriaSelect"),
    produtoSelect: document.getElementById("produtosSelect"),
    dataInicio: document.getElementById("dataInicio"),
    dataFim: document.getElementById("dataFim"),
    btnAplicar: document.getElementById("btnAplicar")
};

const currency = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const integer = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });

function getUser(userId = state.currentUserId) {
    if (state.currentUser && state.currentUser.id === userId) {
        return state.currentUser;
    }
    return state.users.find((user) => user.id === userId) || state.users[0] || {
        id: "",
        name: "Sem usuario",
        roleId: "operador_comercial",
        status: "Inativo"
    };
}

function normalizeRoleId(roleId) {
    return legacyRoleIds[roleId] || roleId;
}

function getRole(user = getUser()) {
    return roleProfiles[normalizeRoleId(user.roleId)] || roleProfiles.operador_comercial;
}

function getScreen() {
    return screens.find((screen) => screen.id === state.currentScreenId) || screens[0];
}

function can(permission) {
    return getRole().permissions.includes(permission);
}

function hasPermission(screenId) {
    const screen = screens.find((item) => item.id === screenId);
    return screen ? can(screen.permission) : false;
}

function assertPermission(permission, target) {
    if (can(permission)) {
        return true;
    }
    showFormMessage(target, "Acesso negado", "error");
    return false;
}

function firstAllowedScreenId() {
    const role = getRole();
    const allowed = screens.find((screen) => role.permissions.includes(screen.permission));
    return allowed ? allowed.id : "dashboard-vendas";
}

function showFormMessage(target, text, type = "success") {
    if (!target) {
        return;
    }
    target.textContent = text;
    target.className = `form-message ${type}`;
}

function setRoleMessage(text, type = "success") {
    if (!els.roleMessage) {
        return;
    }
    els.roleMessage.textContent = text;
    els.roleMessage.className = `role-message ${type}`;
}

function buildParams() {
    const role = getRole();
    const params = new URLSearchParams();
    const filial = role.forcedFilial || els.filialSelect.value;
    params.set("filial", filial);
    params.set("categoria", els.categoriaSelect.value);
    params.set("produto", els.produtoSelect.value);
    params.set("inicio", els.dataInicio.value);
    params.set("fim", els.dataFim.value);
    return params;
}

async function fetchJson(path) {
    const response = await fetch(path);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(data.erro || `Falha em ${path}`);
    }
    return data;
}

async function fetchJsonWithOptions(path, options) {
    const response = await fetch(path, options);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(data.erro || `Falha em ${path}`);
    }
    return data;
}

async function loadUsers() {
    if (!can("usuarios:gerenciar")) {
        state.users = state.currentUser ? [state.currentUser] : [];
        return;
    }
    state.users = await fetchJson("/usuarios");

    if (!state.users.some((user) => user.id === state.currentUserId)) {
        state.currentUserId = state.users[0]?.id || "";
    }
}

async function loadCurrentUser() {
    const user = await fetchJson("/auth/me");
    state.currentUser = user;
    state.currentUserId = user.id;
    state.users = [user];
    state.currentScreenId = firstAllowedScreenId();
}

function showDbNotice() {
    els.dbAlert.hidden = !state.dbUnavailable;
}

function numberFromApi(value) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : 0;
}

function periodLabel(periodo) {
    const date = new Date(`${periodo}T00:00:00`);
    return Number.isNaN(date.getTime()) ? periodo : date.toLocaleDateString("pt-BR", { month: "short", year: "2-digit" });
}

function sumRows(rows, key) {
    return rows.reduce((total, row) => total + Number(row[key] || 0), 0);
}

function topBy(rows, key) {
    return [...rows].sort((a, b) => Number(b[key] || 0) - Number(a[key] || 0))[0];
}

function clone(value) {
    return JSON.parse(JSON.stringify(value));
}

async function loadSelects() {
    const [filiais, categorias] = await Promise.all([
        fetchJson("/filiais"),
        fetchJson("/categorias")
    ]);
    state.apiFiliais = filiais;
    populateSelect(els.filialSelect, filiais, "Todas");
    populateSelect(els.categoriaSelect, categorias, "Todas");
    await loadProducts();
}

async function loadProducts() {
    const category = els.categoriaSelect.value;
    const url = `/produtos?categoria=${encodeURIComponent(category)}`;
    const products = await fetchJson(url);
    populateSelect(els.produtoSelect, products, "Todos");
}

function populateSelect(select, values, defaultLabel) {
    select.innerHTML = `<option value="">${defaultLabel}</option>`;
    values.forEach((value) => {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value;
        select.appendChild(option);
    });
}

async function loadDashboardData() {
    state.dbUnavailable = false;
    const params = buildParams();
    const query = params.toString();
    const [
        receitaBruta, receitaLiquida, custoTotal, margemBruta, margemPercentual,
        monthly, branches, categories, products, catalogProducts, clients
    ] = await Promise.all([
        fetchJson(`/faturamento?${query}`),
        fetchJson(`/receita_liquida?${query}`),
        fetchJson(`/custo_total?${query}`),
        fetchJson(`/margem_bruta?${query}`),
        fetchJson(`/margem_bruta_percentual?${query}`),
        fetchJson(`/pergunta_faturamento?${query}`),
        fetchJson(`/pergunta_receita_liquida?${query}`),
        fetchJson(`/pergunta_receita_liquida_categoria?${query}`),
        fetchJson(`/pergunta_produtos_vendidos?${query}`),
        fetchJson(`/produtos_detalhados?categoria=${encodeURIComponent(els.categoriaSelect.value)}`),
        fetchJson("/clientes")
    ]);

    const normalizedProducts = products.map((item) => ({
        produto: item.produto || item.nome_produto,
        categoria: item.categoria,
        quantidade_vendida: Number(item.quantidade_vendida || item.vendidos || 0),
        receita_liquida: Number(item.receita_liquida || item.receita || 0)
    }));

    state.data = {
        kpis: {
            receitaBruta: numberFromApi(receitaBruta),
            receitaLiquida: numberFromApi(receitaLiquida),
            custoTotal: numberFromApi(custoTotal),
            margemBruta: numberFromApi(margemBruta),
            margemPercentual: numberFromApi(margemPercentual),
            vendas: sumRows(monthly, "quantidade_de_vendas"),
            produtosVendidos: sumRows(monthly, "quantidade_vendida"),
            totalClientes: clients.length
        },
        monthly: clone(monthly),
        branches: clone(branches),
        categories: clone(categories),
        products: normalizedProducts
    };
    state.apiProducts = catalogProducts;
    state.apiClients = clients;
    state.data.catalogProducts = catalogProducts;
    state.data.clients = clients;
    showDbNotice();
}

function renderRoles() {
    updateRoleDescription();
}

function updateRoleDescription() {
    const user = getUser();
    const role = getRole(user);
    const scope = role.forcedFilial ? ` Escopo: ${role.forcedFilial}.` : "";
    if (els.roleDescription) {
        els.roleDescription.innerHTML = `${user.name}<br><strong>${role.name}</strong><br>${role.description}${scope}`;
    }
    els.filialSelect.disabled = Boolean(role.forcedFilial);
    if (role.forcedFilial) {
        els.filialSelect.value = role.forcedFilial;
    }
}

async function authenticateSelectedUser() {
    if (!els.roleSelect || !els.rolePassword) {
        return true;
    }
    const nextUser = getUser(els.roleSelect.value);
    if (nextUser.status !== "Ativo") {
        setRoleMessage("Acesso negado", "error");
        els.roleSelect.value = state.currentUserId;
        return false;
    }

    try {
        await fetchJsonWithOptions("/auth/login-perfil", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                id: nextUser.id,
                password: els.rolePassword.value
            })
        });
    } catch (error) {
        setRoleMessage(error.message, "error");
        els.roleSelect.value = state.currentUserId;
        els.rolePassword.value = "";
        return false;
    }
    state.currentUserId = nextUser.id;
    els.rolePassword.value = "";
    setRoleMessage("Usuario autenticado", "success");
    updateRoleDescription();
    if (!hasPermission(state.currentScreenId)) {
        state.currentScreenId = firstAllowedScreenId();
    }
    return true;
}

function renderNav() {
    const role = getRole();
    const allowedScreens = screens.filter((screen) => role.permissions.includes(screen.permission));
    els.mainNav.innerHTML = allowedScreens.map((screen) => {
        const active = screen.id === state.currentScreenId ? "active" : "";
        return `
            <button class="nav-button ${active}" type="button" data-screen="${screen.id}">
                <span class="nav-icon" aria-hidden="true">${screen.icon}</span>
                <span>${screen.label}</span>
            </button>
        `;
    }).join("");
}

function setScreen(screenId) {
    state.currentScreenId = screenId;
    render();
}

function clearCharts() {
    state.charts.forEach((chart) => chart.destroy());
    state.charts = [];
}

function card(label, value, detail = "") {
    return `<article class="kpi-card"><span>${label}</span><strong>${value}</strong><small>${detail}</small></article>`;
}

function renderKpis(keys) {
    const data = state.data;
    const bestBranch = topBy(data.branches, "receita_liquida");
    const bestCategory = topBy(data.categories, "receita_liquida");
    const ticket = data.kpis.vendas ? data.kpis.receitaLiquida / data.kpis.vendas : 0;
    const available = {
        receita: card("Receita total", currency.format(data.kpis.receitaLiquida), "Receita liquida no periodo"),
        vendas: card("Quantidade de vendas", integer.format(data.kpis.vendas), "Pedidos concluidos"),
        ticket: card("Ticket medio", currency.format(ticket), "Receita por venda"),
        produtos: card("Produtos vendidos", integer.format(data.kpis.produtosVendidos), "Unidades comercializadas"),
        filial: card("Melhor filial", bestBranch?.filial || bestBranch?.nome_filial || "-", currency.format(bestBranch?.receita_liquida || 0)),
        categoria: card("Melhor categoria", bestCategory?.categoria || "-", currency.format(bestCategory?.receita_liquida || 0)),
        clientes: card("Total de clientes", integer.format(data.kpis.totalClientes), "Clientes cadastrados"),
        margem: card("Margem bruta", currency.format(data.kpis.margemBruta), `${data.kpis.margemPercentual.toFixed(1)}% medio`)
    };
    return `<section class="kpi-grid">${keys.map((key) => available[key]).join("")}</section>`;
}

function chartCard(title, canvasId) {
    return `<article class="chart-card"><h3>${title}</h3><div class="chart-box"><canvas id="${canvasId}"></canvas></div></article>`;
}

function renderCharts(configs) {
    if (!window.Chart) {
        return;
    }
    configs.forEach((config) => {
        const ctx = document.getElementById(config.id);
        if (!ctx) {
            return;
        }
        state.charts.push(new Chart(ctx, {
            type: config.type,
            data: config.data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: config.legend !== false },
                    tooltip: {
                        callbacks: {
                            label: (item) => `${item.dataset.label || item.label}: ${currency.format(item.parsed.y ?? item.parsed)}`
                        }
                    }
                },
                scales: config.type === "doughnut" ? {} : { y: { beginAtZero: true }, x: { grid: { display: false } } }
            }
        }));
    });
}

function table(headers, rows) {
    return `
        <div class="table-wrap">
            <table>
                <thead><tr>${headers.map((header) => `<th>${header}</th>`).join("")}</tr></thead>
                <tbody>${rows.join("")}</tbody>
            </table>
        </div>
    `;
}

function renderGeneralDashboard() {
    const monthly = state.data.monthly;
    const branches = state.data.branches;
    const categories = state.data.categories;
    els.viewRoot.innerHTML = `
        ${renderKpis(["receita", "vendas", "ticket", "produtos", "filial", "categoria", "clientes", "margem"])}
        <section class="chart-grid">
            ${chartCard("Evolucao da receita", "chartRevenueEvolution")}
            ${chartCard("Receita por filial", "chartBranchRevenue")}
            ${chartCard("Receita por categoria", "chartCategoryRevenue")}
            ${chartCard("Produtos mais vendidos", "chartTopProducts")}
        </section>
    `;
    renderCharts([
        { id: "chartRevenueEvolution", type: "line", legend: false, data: { labels: monthly.map((item) => periodLabel(item.periodo)), datasets: [{ label: "Receita liquida", data: monthly.map((item) => item.receita_liquida), borderColor: "#0f7b6c", backgroundColor: "rgba(15, 123, 108, 0.16)", fill: true, tension: 0.35 }] } },
        { id: "chartBranchRevenue", type: "bar", legend: false, data: { labels: branches.map((item) => item.filial || item.nome_filial), datasets: [{ label: "Receita liquida", data: branches.map((item) => item.receita_liquida), backgroundColor: "#2457a6" }] } },
        { id: "chartCategoryRevenue", type: "doughnut", data: { labels: categories.map((item) => item.categoria), datasets: [{ label: "Receita liquida", data: categories.map((item) => item.receita_liquida), backgroundColor: ["#0f7b6c", "#2457a6", "#c2410c", "#7c3aed", "#64748b", "#0891b2"] }] } },
        { id: "chartTopProducts", type: "bar", legend: false, data: { labels: state.data.products.slice(0, 6).map((item) => item.produto), datasets: [{ label: "Receita liquida", data: state.data.products.slice(0, 6).map((item) => item.receita_liquida), backgroundColor: "#c2410c" }] } }
    ]);
}

function renderSalesDashboard() {
    const monthly = state.data.monthly;
    const rows = monthly;
    els.viewRoot.innerHTML = `
        ${renderKpis(["receita", "vendas", "ticket", "produtos"])}
        <section class="chart-grid">
            ${chartCard("Vendas por mes", "chartSalesMonth")}
            ${chartCard("Evolucao da receita", "chartSalesRevenue")}
        </section>
        <section class="data-card">
            <h3>Resumo mensal</h3>
            ${table(["Periodo", "Receita bruta", "Descontos", "Receita liquida", "Vendas"], rows.map((item) => `
                <tr><td>${periodLabel(item.periodo)}</td><td>${currency.format(item.receita_bruta)}</td><td>${currency.format(item.desconto_total)}</td><td>${currency.format(item.receita_liquida)}</td><td>${integer.format(item.quantidade_de_vendas)}</td></tr>
            `))}
        </section>
    `;
    renderCharts([
        { id: "chartSalesMonth", type: "bar", legend: false, data: { labels: rows.map((item) => periodLabel(item.periodo)), datasets: [{ label: "Vendas", data: rows.map((item) => item.quantidade_de_vendas), backgroundColor: "#2457a6" }] } },
        { id: "chartSalesRevenue", type: "line", legend: false, data: { labels: rows.map((item) => periodLabel(item.periodo)), datasets: [{ label: "Receita liquida", data: rows.map((item) => item.receita_liquida), borderColor: "#0f7b6c", backgroundColor: "rgba(15, 123, 108, 0.16)", fill: true, tension: 0.35 }] } }
    ]);
}

function renderBranchDashboard() {
    const branches = state.data.branches;
    els.viewRoot.innerHTML = `
        ${renderKpis(["filial", "receita", "margem", "vendas"])}
        <section class="chart-grid">
            ${chartCard("Receita por filial", "chartBranches")}
            <article class="data-card">
                <h3>Ranking de filiais</h3>
                ${table(["Filial", "Receita liquida", "Margem media"], branches.map((item) => `
                    <tr><td>${item.filial || item.nome_filial}</td><td>${currency.format(item.receita_liquida)}</td><td>${Number(item.margem_bruta_percentual || 0).toFixed(1)}%</td></tr>
                `))}
            </article>
        </section>
    `;
    renderCharts([{ id: "chartBranches", type: "bar", legend: false, data: { labels: branches.map((item) => item.filial || item.nome_filial), datasets: [{ label: "Receita liquida", data: branches.map((item) => item.receita_liquida), backgroundColor: "#0f7b6c" }] } }]);
}

function renderCategoryDashboard() {
    const categories = state.data.categories;
    els.viewRoot.innerHTML = `
        ${renderKpis(["categoria", "receita", "produtos", "margem"])}
        <section class="chart-grid">
            ${chartCard("Receita por categoria", "chartCategories")}
            <article class="data-card">
                <h3>Categorias</h3>
                ${table(["Categoria", "Quantidade vendida", "Receita liquida", "Margem media"], categories.map((item) => `
                    <tr><td>${item.categoria}</td><td>${integer.format(item.quantidade_vendida)}</td><td>${currency.format(item.receita_liquida)}</td><td>${Number(item.margem_bruta_percentual || 0).toFixed(1)}%</td></tr>
                `))}
            </article>
        </section>
    `;
    renderCharts([{ id: "chartCategories", type: "doughnut", data: { labels: categories.map((item) => item.categoria), datasets: [{ label: "Receita liquida", data: categories.map((item) => item.receita_liquida), backgroundColor: ["#0f7b6c", "#2457a6", "#c2410c", "#7c3aed", "#64748b", "#0891b2"] }] } }]);
}

function renderProducts() {
    const selectedCategory = els.categoriaSelect.value;
    const source = state.data?.catalogProducts || [];
    const products = source.filter((item) => !selectedCategory || item.categoria === selectedCategory);
    els.viewRoot.innerHTML = `
        <section class="data-card">
            <h3>Produtos</h3>
            ${table(["Produto", "Categoria", "Marca", "Preco", "Status", "Receita"], products.map((item) => `
                <tr><td>${item.produto}</td><td>${item.categoria}</td><td>${item.marca}</td><td>${currency.format(item.preco)}</td><td><span class="badge">${item.status}</span></td><td>${currency.format(item.receita)}</td></tr>
            `))}
        </section>
    `;
}

function renderClients() {
    const clients = state.data?.clients || [];
    els.viewRoot.innerHTML = `
        ${renderKpis(["clientes", "vendas", "ticket", "receita"])}
        <section class="data-card">
            <h3>Clientes</h3>
            ${table(["Cliente", "Tipo", "Cidade", "UF", "Cadastro"], clients.map((item) => `
                <tr><td>${item.nome}</td><td><span class="badge">${item.tipo}</span></td><td>${item.cidade}</td><td>${item.uf}</td><td>${new Date(`${item.cadastro}T00:00:00`).toLocaleDateString("pt-BR")}</td></tr>
            `))}
        </section>
    `;
}

function renderUserManagement() {
    const canCreate = can("usuarios:criar");
    const canEdit = can("usuarios:editar");
    const canRemove = can("usuarios:remover");
    els.viewRoot.innerHTML = `
        <section class="data-card">
            <h3>Gerenciar Usuarios</h3>
            ${canCreate ? `
                <form id="userForm" class="form-grid">
                    <label>Nome<input name="name" required></label>
                    <label>Email<input name="email" type="email" required></label>
                    <label>Senha<input name="password" type="password" required></label>
                    <label>Perfil/Cargo<select name="roleId">${Object.entries(roleProfiles).map(([id, role]) => `<option value="${id}">${role.name}</option>`).join("")}</select></label>
                    <label>Status<select name="status"><option>Ativo</option><option>Inativo</option></select></label>
                    <div class="form-actions"><button class="primary-button" type="submit">Cadastrar usuario</button><span id="userFormMessage" class="form-message"></span></div>
                </form>
            ` : `<p class="muted">Acesso negado para criar usuarios.</p>`}
        </section>
        <section class="data-card">
            <h3>Usuarios cadastrados</h3>
            ${table(["Nome", "Email", "Perfil", "Status", "Acoes"], state.users.map((user) => `
                <tr>
                    <td>${user.name}</td>
                    <td>${user.email}</td>
                    <td><span class="badge">${getRole(user).name}</span></td>
                    <td>${user.status}</td>
                    <td>
                        ${canEdit ? `<button class="primary-button" type="button" data-edit-user="${user.id}">Editar status</button>` : ""}
                        ${canRemove && user.id !== state.currentUserId ? `<button class="danger-button" type="button" data-remove-user="${user.id}">Remover</button>` : ""}
                    </td>
                </tr>
            `))}
        </section>
    `;
}

function renderNewSale() {
    const role = getRole();
    const clients = state.apiClients;
    const products = state.apiProducts;
    const filiais = state.apiFiliais;
    const missingData = !clients.length || !products.length || !filiais.length;
    els.viewRoot.innerHTML = `
        <section class="data-card">
            <h3>Nova Venda</h3>
            ${missingData ? `<p class="muted">Cadastre clientes, produtos e filiais no banco antes de criar uma venda.</p>` : ""}
            <form id="saleForm" class="form-grid">
                <label>Cliente<select name="cliente">${clients.map((client) => `<option>${client.nome}</option>`).join("")}</select></label>
                <label>Produto<select name="produto">${products.map((product) => `<option>${product.produto}</option>`).join("")}</select></label>
                <label>Quantidade<input name="quantidade" type="number" min="1" value="1" required></label>
                <label>Desconto<input name="desconto" type="number" min="0" step="0.01" value="0" required></label>
                <label>Filial<select name="filial" ${role.forcedFilial ? "disabled" : ""}>${filiais.map((filial) => `<option ${filial === role.forcedFilial ? "selected" : ""}>${filial}</option>`).join("")}</select></label>
                <label>Data da venda<input name="data" type="date" required></label>
                <div class="form-actions"><button class="primary-button" type="submit" ${missingData ? "disabled" : ""}>Cadastrar venda</button><span id="saleFormMessage" class="form-message"></span></div>
            </form>
        </section>
    `;
}

function renderPermissions() {
    const permissionRows = Object.entries(roleProfiles).map(([id, role]) => ({ id, ...role }));
    els.viewRoot.innerHTML = `
        <section class="data-card">
            <h3>Matriz de permissoes</h3>
            ${table(["Tela", ...permissionRows.map((role) => role.name)], screens.map((screen) => `
                <tr><td>${screen.label}</td>${permissionRows.map((role) => `<td>${role.permissions.includes(screen.permission) ? '<span class="badge">Permitido</span>' : '<span class="muted">Bloqueado</span>'}</td>`).join("")}</tr>
            `))}
        </section>
    `;
}

function renderReports() {
    els.viewRoot.innerHTML = `
        ${renderKpis(["receita", "margem", "filial", "categoria"])}
        <section class="chart-grid">
            ${chartCard("Receita por filial", "chartReportBranch")}
            ${chartCard("Receita por categoria", "chartReportCategory")}
        </section>
    `;
    renderCharts([
        { id: "chartReportBranch", type: "bar", legend: false, data: { labels: state.data.branches.map((item) => item.filial || item.nome_filial), datasets: [{ label: "Receita liquida", data: state.data.branches.map((item) => item.receita_liquida), backgroundColor: "#2457a6" }] } },
        { id: "chartReportCategory", type: "bar", legend: false, data: { labels: state.data.categories.map((item) => item.categoria), datasets: [{ label: "Receita liquida", data: state.data.categories.map((item) => item.receita_liquida), backgroundColor: "#0f7b6c" }] } }
    ]);
}

function renderDenied() {
    const role = getRole();
    const screen = getScreen();
    els.viewRoot.innerHTML = `
        <section class="denied">
            <h2>Acesso negado</h2>
            <p>O perfil <strong>${role.name}</strong> nao possui permissao para acessar <strong>${screen.label}</strong>.</p>
            <p class="muted">Entre com um usuario autorizado ou selecione uma tela permitida para continuar.</p>
        </section>
    `;
}

function renderCurrentScreen() {
    if (!hasPermission(state.currentScreenId)) {
        renderDenied();
        return;
    }
    const renderers = {
        "dashboard-geral": renderGeneralDashboard,
        "dashboard-vendas": renderSalesDashboard,
        "dashboard-filial": renderBranchDashboard,
        "dashboard-categoria": renderCategoryDashboard,
        "nova-venda": renderNewSale,
        produtos: renderProducts,
        clientes: renderClients,
        "gerenciar-usuarios": renderUserManagement,
        permissoes: renderPermissions,
        relatorios: renderReports
    };
    renderers[state.currentScreenId]();
}

function render() {
    clearCharts();
    const screen = getScreen();
    els.pageTitle.textContent = screen.label;
    renderNav();
    renderCurrentScreen();
}

async function refreshData() {
    try {
        await loadDashboardData();
        render();
    } catch (error) {
        state.dbUnavailable = true;
        showDbNotice();
        els.viewRoot.innerHTML = `
            <section class="denied">
                <h2>Banco indisponivel</h2>
                <p>${error.message}</p>
            </section>
        `;
    }
}

async function handleCreateUser(event) {
    event.preventDefault();
    const message = document.getElementById("userFormMessage");
    if (!assertPermission("usuarios:criar", message)) {
        return;
    }
    const form = new FormData(event.currentTarget);
    const user = {
        name: form.get("name").trim(),
        email: form.get("email").trim(),
        password: form.get("password"),
        roleId: form.get("roleId"),
        status: form.get("status")
    };

    try {
        const createdUser = await fetchJsonWithOptions("/usuarios", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(user)
        });
        state.users.push(createdUser);
        showFormMessage(message, "Usuario cadastrado no banco", "success");
        renderRoles();
        renderUserManagement();
    } catch (error) {
        showFormMessage(message, error.message, "error");
    }
}

async function handleCreateSale(event) {
    event.preventDefault();
    const message = document.getElementById("saleFormMessage");
    if (!assertPermission("vendas:criar", message)) {
        return;
    }
    const form = new FormData(event.currentTarget);
    const role = getRole();
    const sale = {
        id: `sale-${Date.now()}`,
        vendedorId: state.currentUserId,
        cliente: form.get("cliente"),
        produto: form.get("produto"),
        quantidade: Number(form.get("quantidade")),
        desconto: Number(form.get("desconto")),
        filial: role.forcedFilial || form.get("filial"),
        data: form.get("data")
    };
    if (!sale.quantidade || sale.quantidade < 1) {
        showFormMessage(message, "Quantidade invalida", "error");
        return;
    }
    try {
        await fetchJsonWithOptions("/vendas", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(sale)
        });
        showFormMessage(message, "Venda cadastrada no banco e dashboards atualizados", "success");
        await refreshData();
    } catch (error) {
        showFormMessage(message, error.message, "error");
    }
}

async function handleTableActions(event) {
    const removeButton = event.target.closest("[data-remove-user]");
    const editButton = event.target.closest("[data-edit-user]");
    if (removeButton) {
        if (!assertPermission("usuarios:remover", document.querySelector(".form-message"))) {
            return;
        }
        const userId = removeButton.dataset.removeUser;
        try {
            await fetchJsonWithOptions(`/usuarios/${encodeURIComponent(userId)}`, {
                method: "DELETE"
            });
            state.users = state.users.filter((user) => user.id !== userId);
        } catch (error) {
            setRoleMessage(error.message, "error");
        }
        renderRoles();
        renderUserManagement();
    }
    if (editButton) {
        if (!assertPermission("usuarios:editar", document.querySelector(".form-message"))) {
            return;
        }
        const user = getUser(editButton.dataset.editUser);
        const nextStatus = user.status === "Ativo" ? "Inativo" : "Ativo";
        try {
            const updatedUser = await fetchJsonWithOptions(`/usuarios/${encodeURIComponent(user.id)}/status`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ status: nextStatus })
            });
            Object.assign(user, updatedUser);
        } catch (error) {
            setRoleMessage(error.message, "error");
        }
        renderRoles();
        renderUserManagement();
    }
}

function bindEvents() {
    if (els.btnTrocarUsuario) {
        els.btnTrocarUsuario.addEventListener("click", async () => {
            if (await authenticateSelectedUser()) {
                await refreshData();
            }
        });
    }
    if (els.roleSelect) {
        els.roleSelect.addEventListener("change", () => {
            setRoleMessage("Digite a senha para trocar de usuario", "success");
        });
    }
    els.mainNav.addEventListener("click", (event) => {
        const button = event.target.closest("[data-screen]");
        if (button) {
            setScreen(button.dataset.screen);
        }
    });
    els.viewRoot.addEventListener("submit", (event) => {
        if (event.target.id === "userForm") {
            handleCreateUser(event);
        }
        if (event.target.id === "saleForm") {
            handleCreateSale(event);
        }
    });
    els.viewRoot.addEventListener("click", handleTableActions);
    els.categoriaSelect.addEventListener("change", async () => {
        try {
            await loadProducts();
            await refreshData();
        } catch (error) {
            state.dbUnavailable = true;
            showDbNotice();
            els.viewRoot.innerHTML = `
                <section class="denied">
                    <h2>Banco indisponivel</h2>
                    <p>${error.message}</p>
                </section>
            `;
        }
    });
    els.btnAplicar.addEventListener("click", refreshData);
}

async function init() {
    await loadCurrentUser();
    if (can("usuarios:gerenciar")) {
        await loadUsers();
    }
    renderRoles();
    bindEvents();
    await loadSelects();
    await refreshData();
}

init().catch((error) => {
    console.error("Erro ao iniciar interface:", error);
    state.dbUnavailable = true;
    showDbNotice();
    els.viewRoot.innerHTML = `
        <section class="denied">
            <h2>Banco indisponivel</h2>
            <p>${error.message}</p>
        </section>
    `;
});

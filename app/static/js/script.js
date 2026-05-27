const roleProfiles = {
    admin_comercial: {
        name: "Administrador",
        description: "Pode criar, editar e remover usuarios; visualiza todos os dados e dashboards.",
        forcedFilial: "",
        permissions: [
            "dashboard:geral", "dashboard:vendas", "dashboard:filial", "dashboard:categoria",
            "produtos:ver", "clientes:ver", "filiais:ver", "vendas:ver:todas", "vendas:criar",
            "usuarios:gerenciar", "usuarios:criar", "usuarios:editar", "usuarios:remover",
            "permissoes:ver", "relatorios:ver", "dados:todos", "dados:criar", "categorias:ver",
            "rotinas:ver"
        ]
    },
    gerente_comercial: {
        name: "Gerente Comercial",
        description: "Visualiza dashboards, vendas, produtos, clientes, filiais e relatorios.",
        forcedFilial: "",
        permissions: [
            "dashboard:geral", "dashboard:vendas", "dashboard:filial", "dashboard:categoria",
            "produtos:ver", "clientes:ver", "filiais:ver", "categorias:ver", "vendas:ver:todas", "relatorios:ver"
        ]
    },
    operador_comercial: {
        name: "Operador Comercial",
        description: "Pode adicionar vendas, visualizar produtos, clientes e dashboards permitidos.",
        forcedFilial: "",
        permissions: ["dashboard:vendas", "produtos:ver", "clientes:ver", "filiais:ver", "categorias:ver", "vendas:ver:proprias", "vendas:criar", "dados:criar"]
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
    { id: "filiais", label: "Filiais", icon: "F", permission: "filiais:ver" },
    { id: "categorias", label: "Categorias", icon: "C", permission: "categorias:ver" },
    { id: "gerenciar-usuarios", label: "Gerenciar Usuarios", icon: "U", permission: "usuarios:gerenciar" },
    { id: "permissoes", label: "Permissoes", icon: "A", permission: "permissoes:ver" },
    { id: "rotinas-sql", label: "Rotinas SQL", icon: "SQL", permission: "rotinas:ver" },
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
    apiBranchesDetailed: [],
    apiCategoriesDetailed: [],
    apiProducts: [],
    apiClients: [],
    apiChannels: [],
    apiChannelsDetailed: [],
    apiSales: [],
    dbRoutines: null,
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
        throw new Error(data.error || data.erro || data.message || `Falha em ${path}`);
    }
    return data;
}

async function fetchJsonWithOptions(path, options) {
    const response = await fetch(path, options);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(data.error || data.erro || data.message || `Falha em ${path}`);
    }
    return data;
}

function unwrapApi(response) {
    return response && response.success ? response.data : response;
}

async function loadChannels() {
    try {
        const channels = unwrapApi(await fetchJson("/api/canais"));
        return channels.map((channel) => (
            typeof channel === "string"
                ? { id: channel, nome: channel, descricao: "", ativo: true }
                : channel
        ));
    } catch (error) {
        console.warn("Falha ao carregar /api/canais. Tentando rota legada /canais.", error);
        const legacyChannels = await fetchJson("/canais");
        return legacyChannels.map((channel) => ({
            id: channel,
            nome: channel,
            descricao: "",
            ativo: true
        }));
    }
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

function toNumberOrZero(value) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : 0;
}

function getReferenceId(collection, rawValue) {
    const numericValue = toNumberOrZero(rawValue);
    if (numericValue) {
        return numericValue;
    }
    const textValue = String(rawValue || "").trim();
    const match = collection.find((item) => (
        String(item.id) === textValue ||
        item.nome === textValue ||
        item.produto === textValue ||
        item.nome_canal === textValue ||
        item.nome_filial === textValue
    ));
    return match ? toNumberOrZero(match.id) : 0;
}

async function loadSelects() {
    const [filiais, categorias, canais, filiaisDetalhadas, categoriasDetalhadas] = await Promise.all([
        fetchJson("/filiais"),
        fetchJson("/categorias"),
        loadChannels(),
        fetchJson("/api/filiais").then(unwrapApi),
        fetchJson("/api/categorias").then(unwrapApi)
    ]);
    state.apiFiliais = filiais;
    state.apiBranchesDetailed = filiaisDetalhadas;
    state.apiCategoriesDetailed = categoriasDetalhadas;
    state.apiChannelsDetailed = canais;
    state.apiChannels = canais.map((channel) => channel.nome);
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
        monthly, branches, categories, products, catalogProducts, clients, subquerySummary
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
        fetchJson("/api/clientes").then(unwrapApi),
        fetchJson("/resumo_subqueries")
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
    state.data.catalogProducts = catalogProducts;
    state.data.clients = clients;
    state.data.subquerySummary = subquerySummary;
    showDbNotice();
}

async function loadRecentSales() {
    state.apiSales = await fetchJson("/vendas?limite=50");
}

async function loadReferenceData() {
    const [clients, products, branches, categories, channels] = await Promise.all([
        fetchJson("/api/clientes").then(unwrapApi),
        fetchJson("/api/produtos").then(unwrapApi),
        fetchJson("/api/filiais").then(unwrapApi),
        fetchJson("/api/categorias").then(unwrapApi),
        loadChannels()
    ]);
    state.apiClients = clients;
    state.apiProducts = products;
    state.apiBranchesDetailed = branches;
    state.apiCategoriesDetailed = categories;
    state.apiChannelsDetailed = channels;
    state.apiChannels = channels.map((channel) => channel.nome);
}

async function loadDatabaseRoutines() {
    state.dbRoutines = unwrapApi(await fetchJson("/api/banco/rotinas"));
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
    const subqueries = data.subquerySummary || {};
    const available = {
        receita: card("Receita total", currency.format(data.kpis.receitaLiquida), "Receita liquida no periodo"),
        vendas: card("Quantidade de vendas", integer.format(data.kpis.vendas), "Pedidos concluidos"),
        ticket: card("Ticket medio", currency.format(ticket), "Receita por venda"),
        produtos: card("Produtos vendidos", integer.format(data.kpis.produtosVendidos), "Unidades comercializadas"),
        filial: card("Melhor filial", bestBranch?.filial || bestBranch?.nome_filial || "-", currency.format(bestBranch?.receita_liquida || 0)),
        categoria: card("Melhor categoria", bestCategory?.categoria || "-", currency.format(bestCategory?.receita_liquida || 0)),
        clientes: card("Total de clientes", integer.format(data.kpis.totalClientes), "Clientes cadastrados"),
        margem: card("Margem bruta", currency.format(data.kpis.margemBruta), `${data.kpis.margemPercentual.toFixed(1)}% medio`),
        subqueries: card("Vendas acima da media", integer.format(subqueries.vendasAcimaTicketMedio || 0), "Consulta com subqueries")
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
        ${renderKpis(["receita", "vendas", "ticket", "produtos", "filial", "categoria", "clientes", "subqueries"])}
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
    const source = state.data?.catalogProducts || state.apiProducts || [];
    const products = source.filter((item) => !selectedCategory || item.categoria === selectedCategory);
    const canCreateData = can("dados:criar");
    const categories = [...new Set(source.map((item) => item.categoria).filter(Boolean))];
    els.viewRoot.innerHTML = `
        ${canCreateData ? `
            <section class="data-card">
                <h3>Cadastrar Produto</h3>
                <form id="productForm" class="form-grid">
                    <label>Produto<input name="produto" required></label>
                    <label>Categoria<select name="categoria" required>${categories.map((category) => `<option>${category}</option>`).join("")}</select></label>
                    <label>Marca<input name="marca"></label>
                    <label>Preco<input name="preco" type="number" min="0.01" step="0.01" required></label>
                    <label>Custo<input name="custo" type="number" min="0" step="0.01" required></label>
                    <label>Status<select name="status"><option>ATIVO</option><option>INATIVO</option></select></label>
                    <div class="form-actions"><button class="primary-button" type="submit">Cadastrar produto</button><span id="productFormMessage" class="form-message"></span></div>
                </form>
            </section>
        ` : ""}
        <section class="data-card">
            <h3>Produtos</h3>
            ${table(["Produto", "Categoria", "Marca", "Preco", "Status", "Receita"], products.map((item) => `
                <tr><td>${item.produto}</td><td>${item.categoria}</td><td>${item.marca}</td><td>${currency.format(item.preco)}</td><td><span class="badge">${item.status}</span></td><td>${currency.format(item.receita)}</td></tr>
            `))}
        </section>
    `;
}

function renderClients() {
    const clients = state.data?.clients || state.apiClients || [];
    const canCreateData = can("dados:criar");
    els.viewRoot.innerHTML = `
        ${renderKpis(["clientes", "vendas", "ticket", "receita"])}
        ${canCreateData ? `
            <section class="data-card">
                <h3>Cadastrar Cliente</h3>
                <form id="clientForm" class="form-grid">
                    <label>Nome<input name="nome" required></label>
                    <label>Tipo<select name="tipo"><option>B2C</option><option>B2B</option></select></label>
                    <label>Cidade<input name="cidade"></label>
                    <label>UF<input name="uf" maxlength="2"></label>
                    <label>Cadastro<input name="cadastro" type="date" required></label>
                    <div class="form-actions"><button class="primary-button" type="submit">Cadastrar cliente</button><span id="clientFormMessage" class="form-message"></span></div>
                </form>
            </section>
        ` : ""}
        <section class="data-card">
            <h3>Clientes</h3>
            ${table(["Cliente", "Tipo", "Cidade", "UF", "Cadastro"], clients.map((item) => `
                <tr><td>${item.nome}</td><td><span class="badge">${item.tipo}</span></td><td>${item.cidade}</td><td>${item.uf}</td><td>${new Date(`${item.cadastro}T00:00:00`).toLocaleDateString("pt-BR")}</td></tr>
            `))}
        </section>
    `;
}

function renderBranches() {
    const canCreateData = can("dados:criar");
    const branches = state.apiBranchesDetailed || [];
    els.viewRoot.innerHTML = `
        ${canCreateData ? `
            <section class="data-card">
                <h3>Cadastrar Filial</h3>
                <form id="branchForm" class="form-grid">
                    <label>Nome<input name="nome" required></label>
                    <label>Cidade<input name="cidade" required></label>
                    <label>UF<input name="uf" maxlength="2" required></label>
                    <label>Regiao<input name="regiao" required></label>
                    <label>Porte<select name="porte"><option>Pequena</option><option>Media</option><option>Grande</option></select></label>
                    <div class="form-actions"><button class="primary-button" type="submit">Cadastrar filial</button><span id="branchFormMessage" class="form-message"></span></div>
                </form>
            </section>
        ` : ""}
        <section class="data-card">
            <h3>Filiais</h3>
            ${table(["Nome", "Cidade", "UF", "Regiao", "Porte"], branches.map((item) => `
                <tr><td>${item.nome}</td><td>${item.cidade}</td><td>${item.uf}</td><td>${item.regiao}</td><td>${item.porte}</td></tr>
            `))}
        </section>
    `;
}

function renderCategories() {
    const canCreateData = can("dados:criar");
    const categories = state.apiCategoriesDetailed || [];
    els.viewRoot.innerHTML = `
        ${canCreateData ? `
            <section class="data-card">
                <h3>Cadastrar Categoria</h3>
                <form id="categoryForm" class="form-grid">
                    <label>Nome<input name="nome" required></label>
                    <label>Descricao<input name="descricao"></label>
                    <div class="form-actions"><button class="primary-button" type="submit">Cadastrar categoria</button><span id="categoryFormMessage" class="form-message"></span></div>
                </form>
            </section>
        ` : ""}
        <section class="data-card">
            <h3>Categorias</h3>
            ${table(["Nome", "Descricao"], categories.map((item) => `
                <tr><td>${item.nome}</td><td>${item.descricao || "-"}</td></tr>
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
    const filiais = state.apiBranchesDetailed || [];
    const channels = state.apiChannelsDetailed || [];
    const sales = state.apiSales;
    const missingData = !clients.length || !products.length || !filiais.length || !channels.length;
    els.viewRoot.innerHTML = `
        <section class="data-card">
            <h3>Nova Venda</h3>
            ${missingData ? `<p class="muted">Cadastre clientes, produtos e filiais no banco antes de criar uma venda.</p>` : ""}
            <form id="saleForm" class="form-grid">
                <label>Cliente<select name="id_cliente">${clients.map((client) => `<option value="${client.id}">${client.nome}</option>`).join("")}</select></label>
                <label>Produto<select name="id_produto">${products.map((product) => `<option value="${product.id}" data-preco="${product.preco}">${product.produto}</option>`).join("")}</select></label>
                <label>Quantidade<input name="quantidade" type="number" min="1" value="1" required></label>
                <label>Desconto<input name="desconto" type="number" min="0" step="0.01" value="0" required></label>
                <label>Filial<select name="id_filial" ${role.forcedFilial ? "disabled" : ""}>${filiais.map((filial) => `<option value="${filial.id}" ${filial.nome === role.forcedFilial ? "selected" : ""}>${filial.nome}</option>`).join("")}</select></label>
                <label>Canal<select name="id_canal">${channels.map((channel) => `<option value="${channel.id}">${channel.nome}</option>`).join("")}</select></label>
                <label>Data da venda<input name="data_venda" type="date" required></label>
                <div class="form-actions"><button class="primary-button" type="submit" ${missingData ? "disabled" : ""}>Cadastrar venda</button><span id="saleFormMessage" class="form-message"></span></div>
            </form>
        </section>
        <section class="data-card">
            <h3>Vendas cadastradas</h3>
            ${table(["Pedido", "Data", "Cliente", "Produto", "Filial", "Canal", "Responsavel", "Quantidade", "Valor"], sales.map((sale) => `
                <tr>
                    <td>${sale.numeroPedido}</td>
                    <td>${new Date(`${sale.data}T00:00:00`).toLocaleDateString("pt-BR")}</td>
                    <td>${sale.cliente || "-"}</td>
                    <td>${sale.produtos || "-"}</td>
                    <td>${sale.filial}</td>
                    <td>${sale.canal || "-"}</td>
                    <td>${sale.responsavel}</td>
                    <td>${integer.format(sale.quantidade)}</td>
                    <td>${currency.format(sale.valorLiquido)}</td>
                </tr>
            `))}
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

function renderSqlRoutines() {
    const routines = state.dbRoutines || {
        totalTriggers: 0,
        totalRotinas: 0,
        requisitoTriggersOk: false,
        requisitoRotinasOk: false,
        triggers: [],
        rotinas: []
    };
    els.viewRoot.innerHTML = `
        <section class="kpi-grid">
            ${card("Triggers", integer.format(routines.totalTriggers), routines.requisitoTriggersOk ? "Requisito minimo atendido" : "Minimo exigido: 4")}
            ${card("Procedures/functions", integer.format(routines.totalRotinas), routines.requisitoRotinasOk ? "Requisito minimo atendido" : "Minimo exigido: 4")}
            ${card("SQL unico", "db/banco_completo.sql", "Script consolidado do projeto")}
        </section>
        <section class="data-card">
            <h3>Executar rotinas do banco</h3>
            <div class="form-actions">
                <button class="primary-button" type="button" data-run-routines-demo>Executar demo</button>
                <span id="routinesMessage" class="form-message"></span>
            </div>
        </section>
        <section class="data-card">
            <h3>Triggers cadastradas</h3>
            ${table(["Nome", "Tabela", "Momento", "Evento"], routines.triggers.map((item) => `
                <tr><td>${item.nome}</td><td>${item.tabela}</td><td>${item.momento}</td><td>${item.evento}</td></tr>
            `))}
        </section>
        <section class="data-card">
            <h3>Procedures e functions</h3>
            ${table(["Nome", "Tipo", "Retorno"], routines.rotinas.map((item) => `
                <tr><td>${item.nome}</td><td>${item.tipo}</td><td>${item.retorno || "-"}</td></tr>
            `))}
        </section>
    `;
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
        filiais: renderBranches,
        categorias: renderCategories,
        "gerenciar-usuarios": renderUserManagement,
        permissoes: renderPermissions,
        "rotinas-sql": renderSqlRoutines,
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
        await loadRecentSales();
        await loadReferenceData();
        if (can("rotinas:ver")) {
            await loadDatabaseRoutines();
        }
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
    const formElement = event.target.closest("form");
    const message = document.getElementById("userFormMessage");
    if (!formElement) {
        showFormMessage(message, "Formulario de usuario nao encontrado.", "error");
        return;
    }
    if (!assertPermission("usuarios:criar", message)) {
        return;
    }
    const form = new FormData(formElement);
    const user = {
        nome: form.get("name").trim(),
        email: form.get("email").trim(),
        senha: form.get("password"),
        perfil: form.get("roleId"),
        ativo: form.get("status") === "Ativo"
    };
    if (!user.nome || !user.email || !user.senha || !user.perfil) {
        showFormMessage(message, "Campo obrigatorio nao informado.", "error");
        return;
    }
    console.log("Clique no botao cadastrar usuario");
    console.log("Dados enviados:", user);

    try {
        showFormMessage(message, "Cadastrando usuario...", "success");
        const response = await fetchJsonWithOptions("/api/usuarios", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(user)
        });
        formElement.reset();
        await loadUsers();
        renderRoles();
        renderUserManagement();
        showFormMessage(document.getElementById("userFormMessage"), response.message || "Usuario cadastrado com sucesso.", "success");
    } catch (error) {
        showFormMessage(message, `Erro ao cadastrar usuario: ${error.message}`, "error");
    }
}

async function handleCreateSale(event) {
    event.preventDefault();
    const formElement = event.target.closest("form");
    const message = document.getElementById("saleFormMessage");
    if (!formElement) {
        showFormMessage(message, "Formulario de venda nao encontrado.", "error");
        return;
    }
    if (!assertPermission("vendas:criar", message)) {
        return;
    }
    const form = new FormData(formElement);
    const role = getRole();
    const productSelect = formElement.querySelector('select[name="id_produto"]');
    const selectedProduct = productSelect?.selectedOptions?.[0];
    const precoUnitario = Number(selectedProduct?.dataset?.preco || 0);
    const rawFilial = form.get("id_filial");
    const rawCliente = form.get("id_cliente");
    const rawCanal = form.get("id_canal");
    const rawProduto = form.get("id_produto");
    const canalId = getReferenceId(state.apiChannelsDetailed, rawCanal);
    const sale = {
        id_filial: getReferenceId(state.apiBranchesDetailed, rawFilial),
        id_cliente: getReferenceId(state.apiClients, rawCliente),
        id_canal: canalId || rawCanal,
        canal: rawCanal,
        data_venda: form.get("data_venda"),
        itens: [
            {
                id_produto: getReferenceId(state.apiProducts, rawProduto),
                quantidade: Number(form.get("quantidade")),
                preco_unitario: precoUnitario,
                desconto: Number(form.get("desconto"))
            }
        ]
    };
    console.log("Dados enviados:", sale);
    if (!sale.itens[0].quantidade || sale.itens[0].quantidade < 1) {
        showFormMessage(message, "Quantidade invalida", "error");
        return;
    }
    if (!sale.itens[0].preco_unitario || sale.itens[0].preco_unitario <= 0) {
        showFormMessage(message, "Preco unitario invalido", "error");
        return;
    }
    const missingFields = [];
    if (!sale.id_filial) missingFields.push("filial");
    if (!sale.id_cliente) missingFields.push("cliente");
    if (!sale.id_canal) missingFields.push("canal");
    if (!sale.data_venda) missingFields.push("data da venda");
    if (!sale.itens[0].id_produto) missingFields.push("produto");
    if (missingFields.length) {
        showFormMessage(message, `Campo obrigatorio nao informado: ${missingFields.join(", ")}.`, "error");
        console.warn("Campos invalidos da venda:", {
            missingFields,
            rawValues: { rawFilial, rawCliente, rawCanal, rawProduto, data_venda: sale.data_venda },
            sale
        });
        return;
    }
    try {
        showFormMessage(message, "Registrando venda...", "success");
        const response = await fetchJsonWithOptions("/api/vendas", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(sale)
        });
        formElement.reset();
        await refreshData();
        if (state.currentScreenId === "nova-venda") {
            showFormMessage(document.getElementById("saleFormMessage"), response.message || "Venda registrada com sucesso.", "success");
        }
    } catch (error) {
        showFormMessage(message, `Erro ao registrar venda: ${error.message}`, "error");
    }
}

async function handleCreateProduct(event) {
    event.preventDefault();
    const formElement = event.target.closest("form");
    const message = document.getElementById("productFormMessage");
    if (!formElement) {
        showFormMessage(message, "Formulario de produto nao encontrado.", "error");
        return;
    }
    if (!assertPermission("dados:criar", message)) {
        return;
    }
    const form = new FormData(formElement);
    const product = {
        produto: form.get("produto").trim(),
        categoria: form.get("categoria"),
        marca: form.get("marca").trim(),
        preco: Number(form.get("preco")),
        custo: Number(form.get("custo")),
        status: form.get("status")
    };

    try {
        await fetchJsonWithOptions("/produtos", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(product)
        });
        formElement.reset();
        await loadProducts();
        await refreshData();
        if (state.currentScreenId === "produtos") {
            showFormMessage(document.getElementById("productFormMessage"), "Produto cadastrado e lista atualizada", "success");
        }
    } catch (error) {
        showFormMessage(message, error.message, "error");
    }
}

async function handleCreateClient(event) {
    event.preventDefault();
    const formElement = event.target.closest("form");
    const message = document.getElementById("clientFormMessage");
    if (!formElement) {
        showFormMessage(message, "Formulario de cliente nao encontrado.", "error");
        return;
    }
    if (!assertPermission("dados:criar", message)) {
        return;
    }
    const form = new FormData(formElement);
    const client = {
        nome: form.get("nome").trim(),
        tipo: form.get("tipo"),
        cidade: form.get("cidade").trim(),
        uf: form.get("uf").trim(),
        cadastro: form.get("cadastro")
    };

    try {
        await fetchJsonWithOptions("/clientes", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(client)
        });
        formElement.reset();
        await refreshData();
        if (state.currentScreenId === "clientes") {
            showFormMessage(document.getElementById("clientFormMessage"), "Cliente cadastrado e lista atualizada", "success");
        }
    } catch (error) {
        showFormMessage(message, error.message, "error");
    }
}

async function handleCreateBranch(event) {
    event.preventDefault();
    const formElement = event.target.closest("form");
    const message = document.getElementById("branchFormMessage");
    if (!formElement) {
        showFormMessage(message, "Formulario de filial nao encontrado.", "error");
        return;
    }
    if (!assertPermission("dados:criar", message)) {
        return;
    }
    const form = new FormData(formElement);
    const branch = {
        nome: form.get("nome").trim(),
        cidade: form.get("cidade").trim(),
        uf: form.get("uf").trim(),
        regiao: form.get("regiao").trim(),
        porte: form.get("porte")
    };

    try {
        await fetchJsonWithOptions("/api/filiais", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(branch)
        });
        formElement.reset();
        await loadSelects();
        await refreshData();
        if (state.currentScreenId === "filiais") {
            showFormMessage(document.getElementById("branchFormMessage"), "Filial cadastrada com sucesso.", "success");
        }
    } catch (error) {
        showFormMessage(message, `Erro ao cadastrar filial: ${error.message}`, "error");
    }
}

async function handleCreateCategory(event) {
    event.preventDefault();
    const formElement = event.target.closest("form");
    const message = document.getElementById("categoryFormMessage");
    if (!formElement) {
        showFormMessage(message, "Formulario de categoria nao encontrado.", "error");
        return;
    }
    if (!assertPermission("dados:criar", message)) {
        return;
    }
    const form = new FormData(formElement);
    const category = {
        nome: form.get("nome").trim(),
        descricao: form.get("descricao").trim()
    };

    try {
        await fetchJsonWithOptions("/api/categorias", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(category)
        });
        formElement.reset();
        await loadSelects();
        await refreshData();
        if (state.currentScreenId === "categorias") {
            showFormMessage(document.getElementById("categoryFormMessage"), "Categoria cadastrada com sucesso.", "success");
        }
    } catch (error) {
        showFormMessage(message, `Erro ao cadastrar categoria: ${error.message}`, "error");
    }
}

async function handleTableActions(event) {
    const removeButton = event.target.closest("[data-remove-user]");
    const editButton = event.target.closest("[data-edit-user]");
    const runRoutinesButton = event.target.closest("[data-run-routines-demo]");

    if (runRoutinesButton) {
        const message = document.getElementById("routinesMessage");
        try {
            showFormMessage(message, "Executando procedures e functions...", "success");
            const response = await fetchJsonWithOptions("/api/banco/rotinas/executar-demo", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({})
            });
            await loadDatabaseRoutines();
            renderSqlRoutines();
            const result = response.data || {};
            showFormMessage(
                document.getElementById("routinesMessage"),
                `${response.message} Receita exemplo: ${currency.format(result.receitaLiquidaExemplo || 0)}.`,
                "success"
            );
        } catch (error) {
            showFormMessage(message, `Erro ao executar rotinas: ${error.message}`, "error");
        }
        return;
    }
    if (removeButton) {
        if (!assertPermission("usuarios:remover", document.querySelector(".form-message"))) {
            return;
        }
        const userId = removeButton.dataset.removeUser;
        try {
            await fetchJsonWithOptions(`/usuarios/${encodeURIComponent(userId)}`, {
                method: "DELETE"
            });
            await loadUsers();
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
            await loadUsers();
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
        if (event.target.id === "productForm") {
            handleCreateProduct(event);
        }
        if (event.target.id === "clientForm") {
            handleCreateClient(event);
        }
        if (event.target.id === "branchForm") {
            handleCreateBranch(event);
        }
        if (event.target.id === "categoryForm") {
            handleCreateCategory(event);
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
    await loadReferenceData();
    if (can("rotinas:ver")) {
        await loadDatabaseRoutines();
    }
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

const roleProfiles = {
    administrador: {
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
    gerente: {
        name: "Gerente",
        description: "Pode criar e remover usuarios; visualiza dashboards, vendas, produtos, clientes e filiais.",
        forcedFilial: "",
        permissions: [
            "dashboard:geral", "dashboard:vendas", "dashboard:filial", "dashboard:categoria",
            "produtos:ver", "clientes:ver", "filiais:ver", "vendas:ver:todas",
            "usuarios:gerenciar", "usuarios:criar", "usuarios:remover", "relatorios:ver"
        ]
    },
    vendedor: {
        name: "Vendedor",
        description: "Pode adicionar vendas, visualizar produtos, clientes e somente suas vendas.",
        forcedFilial: "Filial Campinas",
        permissions: ["dashboard:vendas", "produtos:ver", "clientes:ver", "vendas:ver:proprias", "vendas:criar"]
    },
    analista: {
        name: "Analista",
        description: "Pode apenas visualizar dados, dashboards e relatorios. Nao cadastra, edita ou remove dados.",
        forcedFilial: "",
        permissions: [
            "dashboard:geral", "dashboard:vendas", "dashboard:filial", "dashboard:categoria",
            "produtos:ver", "clientes:ver", "filiais:ver", "vendas:ver:todas", "relatorios:ver"
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

const mock = {
    users: [
        { id: "u-admin", name: "Marina Costa", email: "admin@aurora.local", password: "admin123", roleId: "administrador", status: "Ativo" },
        { id: "u-gerente", name: "Rafael Lima", email: "gerente@aurora.local", password: "gerente123", roleId: "gerente", status: "Ativo" },
        { id: "u-vendedor", name: "Bianca Alves", email: "vendedor@aurora.local", password: "vendedor123", roleId: "vendedor", status: "Ativo" },
        { id: "u-analista", name: "Lucas Pereira", email: "analista@aurora.local", password: "analista123", roleId: "analista", status: "Ativo" }
    ],
    filiais: [
        "Filial Sao Paulo Centro", "Filial Campinas", "Filial Rio Capital", "Filial Belo Horizonte",
        "Filial Curitiba", "Filial Porto Alegre", "Filial Salvador", "Filial Recife",
        "Filial Goiania", "Filial Brasilia"
    ],
    categorias: ["Perifericos", "Hardware", "Computadores", "Monitores", "Armazenamento", "Redes"],
    produtos: [
        { produto: "Mouse Gamer RGB", categoria: "Perifericos", marca: "RedTech", preco: 129.9, status: "ATIVO", vendidos: 3280, receita: 426072 },
        { produto: "Teclado Mecanico", categoria: "Perifericos", marca: "KeyPro", preco: 249.9, status: "ATIVO", vendidos: 2910, receita: 727209 },
        { produto: "Notebook i5 16GB", categoria: "Computadores", marca: "NotePro", preco: 3599.9, status: "ATIVO", vendidos: 740, receita: 2663926 },
        { produto: "PC Gamer Completo", categoria: "Computadores", marca: "ByteMachine", preco: 4999.9, status: "ATIVO", vendidos: 610, receita: 3049939 },
        { produto: "Monitor Gamer 144Hz", categoria: "Monitores", marca: "ViewMax", preco: 1299.9, status: "ATIVO", vendidos: 1090, receita: 1416891 },
        { produto: "SSD NVMe 1TB", categoria: "Armazenamento", marca: "StorageX", preco: 499.9, status: "ATIVO", vendidos: 1920, receita: 959808 },
        { produto: "Roteador Dual Band", categoria: "Redes", marca: "NetFast", preco: 199.9, status: "ATIVO", vendidos: 1610, receita: 321839 }
    ],
    clientes: [
        { nome: "Cliente 12", tipo: "B2B", cidade: "Sao Paulo", uf: "SP", cadastro: "2025-10-11" },
        { nome: "Cliente 41", tipo: "B2C", cidade: "Belo Horizonte", uf: "MG", cadastro: "2025-12-03" },
        { nome: "Cliente 87", tipo: "B2C", cidade: "Rio de Janeiro", uf: "RJ", cadastro: "2026-01-19" },
        { nome: "Cliente 156", tipo: "B2B", cidade: "Curitiba", uf: "PR", cadastro: "2026-02-22" },
        { nome: "Cliente 244", tipo: "B2C", cidade: "Brasilia", uf: "DF", cadastro: "2026-03-07" }
    ],
    monthly: [
        { periodo: "2025-07-01", receita_bruta: 695000, receita_liquida: 658000, desconto_total: 37000, quantidade_vendida: 1450, quantidade_de_vendas: 520 },
        { periodo: "2025-08-01", receita_bruta: 734000, receita_liquida: 692000, desconto_total: 42000, quantidade_vendida: 1510, quantidade_de_vendas: 548 },
        { periodo: "2025-09-01", receita_bruta: 763000, receita_liquida: 724500, desconto_total: 38500, quantidade_vendida: 1580, quantidade_de_vendas: 571 },
        { periodo: "2025-10-01", receita_bruta: 812000, receita_liquida: 769000, desconto_total: 43000, quantidade_vendida: 1664, quantidade_de_vendas: 602 },
        { periodo: "2025-11-01", receita_bruta: 881000, receita_liquida: 831000, desconto_total: 50000, quantidade_vendida: 1785, quantidade_de_vendas: 649 },
        { periodo: "2025-12-01", receita_bruta: 943000, receita_liquida: 898000, desconto_total: 45000, quantidade_vendida: 1938, quantidade_de_vendas: 704 }
    ],
    branchRevenue: [
        { filial: "Filial Sao Paulo Centro", receita_liquida: 1250000, margem_bruta_percentual: 34.2 },
        { filial: "Filial Belo Horizonte", receita_liquida: 1084000, margem_bruta_percentual: 32.7 },
        { filial: "Filial Campinas", receita_liquida: 997000, margem_bruta_percentual: 31.5 },
        { filial: "Filial Curitiba", receita_liquida: 916000, margem_bruta_percentual: 30.8 },
        { filial: "Filial Salvador", receita_liquida: 870000, margem_bruta_percentual: 29.4 }
    ],
    categoryRevenue: [
        { categoria: "Computadores", quantidade_vendida: 1740, receita_liquida: 4312000, margem_bruta_percentual: 28.8 },
        { categoria: "Monitores", quantidade_vendida: 2490, receita_liquida: 2177000, margem_bruta_percentual: 34.9 },
        { categoria: "Hardware", quantidade_vendida: 3180, receita_liquida: 1949000, margem_bruta_percentual: 30.1 },
        { categoria: "Perifericos", quantidade_vendida: 4200, receita_liquida: 1510000, margem_bruta_percentual: 39.2 },
        { categoria: "Armazenamento", quantidade_vendida: 2670, receita_liquida: 1128000, margem_bruta_percentual: 36.4 }
    ],
    sales: []
};

const state = {
    currentUserId: "u-admin",
    currentScreenId: "dashboard-geral",
    charts: [],
    data: null,
    users: cloneUsers(),
    apiFiliais: [],
    apiProducts: [],
    apiClients: [],
    usingMockUsers: false,
    usingMock: false
};

const els = {
    roleSelect: document.getElementById("roleSelect"),
    rolePassword: document.getElementById("rolePassword"),
    roleMessage: document.getElementById("roleMessage"),
    roleDescription: document.getElementById("roleDescription"),
    btnTrocarUsuario: document.getElementById("btnTrocarUsuario"),
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

function cloneUsers() {
    return mock.users.map(({ password, ...user }) => ({ ...user, password }));
}

function getUser(userId = state.currentUserId) {
    return state.users.find((user) => user.id === userId) || state.users[0] || mock.users[0];
}

function getRole(user = getUser()) {
    return roleProfiles[user.roleId] || roleProfiles.vendedor;
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
    if (!response.ok) {
        throw new Error(`Falha em ${path}`);
    }
    return response.json();
}

async function fetchJsonWithOptions(path, options) {
    const response = await fetch(path, options);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(data.erro || `Falha em ${path}`);
    }
    return data;
}

async function fetchOptional(path, fallback) {
    try {
        return await fetchJson(path);
    } catch (error) {
        state.usingMock = true;
        return fallback;
    }
}

async function loadUsers() {
    state.usingMockUsers = false;
    try {
        state.users = await fetchJson("/usuarios");
        if (!state.users.length) {
            state.users = cloneUsers();
            state.usingMockUsers = true;
        }
    } catch (error) {
        state.usingMockUsers = true;
        state.users = cloneUsers();
    }

    if (!state.users.some((user) => user.id === state.currentUserId)) {
        state.currentUserId = state.users[0]?.id || "u-admin";
    }
}

function showMockNotice() {
    els.dbAlert.hidden = !state.usingMock;
}

function numberFromApi(value) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : 0;
}

function periodLabel(periodo) {
    const date = new Date(`${periodo}T00:00:00`);
    return Number.isNaN(date.getTime()) ? periodo : date.toLocaleDateString("pt-BR", { month: "short", year: "2-digit" });
}

function monthKey(dateValue) {
    const date = dateValue ? new Date(`${dateValue}T00:00:00`) : new Date();
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-01`;
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
        fetchOptional("/filiais", mock.filiais),
        fetchOptional("/categorias", mock.categorias)
    ]);
    state.apiFiliais = filiais;
    populateSelect(els.filialSelect, filiais, "Todas");
    populateSelect(els.categoriaSelect, categorias, "Todas");
    await loadProducts();
}

async function loadProducts() {
    const category = els.categoriaSelect.value;
    const url = `/produtos?categoria=${encodeURIComponent(category)}`;
    const products = await fetchOptional(
        url,
        mock.produtos.filter((item) => !category || item.categoria === category).map((item) => item.produto)
    );
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

function applyLocalSales(data) {
    mock.sales.forEach((sale) => {
        const product = mock.produtos.find((item) => item.produto === sale.produto);
        const category = product?.categoria || "Outros";
        const gross = sale.quantidade * (product?.preco || 0);
        const discount = Math.min(sale.desconto, gross);
        const net = gross - discount;
        const period = monthKey(sale.data);

        let month = data.monthly.find((item) => item.periodo === period);
        if (!month) {
            month = { periodo: period, receita_bruta: 0, receita_liquida: 0, desconto_total: 0, quantidade_vendida: 0, quantidade_de_vendas: 0 };
            data.monthly.push(month);
        }
        month.receita_bruta += gross;
        month.receita_liquida += net;
        month.desconto_total += discount;
        month.quantidade_vendida += sale.quantidade;
        month.quantidade_de_vendas += 1;

        let branch = data.branches.find((item) => (item.filial || item.nome_filial) === sale.filial);
        if (!branch) {
            branch = { filial: sale.filial, receita_liquida: 0, margem_bruta_percentual: 30 };
            data.branches.push(branch);
        }
        branch.receita_liquida += net;

        let categoryRow = data.categories.find((item) => item.categoria === category);
        if (!categoryRow) {
            categoryRow = { categoria: category, quantidade_vendida: 0, receita_liquida: 0, margem_bruta_percentual: 30 };
            data.categories.push(categoryRow);
        }
        categoryRow.quantidade_vendida += sale.quantidade;
        categoryRow.receita_liquida += net;

        let productRow = data.products.find((item) => item.produto === sale.produto);
        if (!productRow) {
            productRow = { produto: sale.produto, categoria: category, quantidade_vendida: 0, receita_liquida: 0 };
            data.products.push(productRow);
        }
        productRow.quantidade_vendida += sale.quantidade;
        productRow.receita_liquida += net;
    });

    data.monthly.sort((a, b) => a.periodo.localeCompare(b.periodo));
    data.kpis.receitaBruta = sumRows(data.monthly, "receita_bruta");
    data.kpis.receitaLiquida = sumRows(data.monthly, "receita_liquida");
    data.kpis.vendas = sumRows(data.monthly, "quantidade_de_vendas");
    data.kpis.produtosVendidos = sumRows(data.monthly, "quantidade_vendida");
}

async function loadDashboardData() {
    state.usingMock = false;
    const params = buildParams();
    const query = params.toString();
    const [
        receitaBruta, receitaLiquida, custoTotal, margemBruta, margemPercentual,
        monthly, branches, categories, products, catalogProducts, clients
    ] = await Promise.all([
        fetchOptional(`/faturamento?${query}`, String(sumRows(mock.monthly, "receita_bruta"))),
        fetchOptional(`/receita_liquida?${query}`, String(sumRows(mock.monthly, "receita_liquida"))),
        fetchOptional(`/custo_total?${query}`, "4360000"),
        fetchOptional(`/margem_bruta?${query}`, "1783000"),
        fetchOptional(`/margem_bruta_percentual?${query}`, "32.6"),
        fetchOptional(`/pergunta_faturamento?${query}`, clone(mock.monthly)),
        fetchOptional(`/pergunta_receita_liquida?${query}`, clone(mock.branchRevenue)),
        fetchOptional(`/pergunta_receita_liquida_categoria?${query}`, clone(mock.categoryRevenue)),
        fetchOptional(`/pergunta_produtos_vendidos?${query}`, clone(mock.produtos)),
        fetchOptional(`/produtos_detalhados?categoria=${encodeURIComponent(els.categoriaSelect.value)}`, clone(mock.produtos)),
        fetchOptional("/clientes", clone(mock.clientes))
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
            totalClientes: mock.clientes.length
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
    state.data.kpis.totalClientes = clients.length;
    if (state.usingMock) {
        applyLocalSales(state.data);
    }
    showMockNotice();
}

function renderRoles() {
    els.roleSelect.innerHTML = state.users.map((user) => {
        const role = roleProfiles[user.roleId];
        return `<option value="${user.id}">${user.name} - ${role.name}</option>`;
    }).join("");
    els.roleSelect.value = state.currentUserId;
    updateRoleDescription();
}

function updateRoleDescription() {
    const user = getUser();
    const role = getRole(user);
    const scope = role.forcedFilial ? ` Escopo: ${role.forcedFilial}.` : "";
    els.roleDescription.textContent = `Usuario logado: ${user.name} (${role.name}). ${role.description}${scope}`;
    els.filialSelect.disabled = Boolean(role.forcedFilial);
    if (role.forcedFilial) {
        els.filialSelect.value = role.forcedFilial;
    }
}

async function authenticateSelectedUser() {
    const nextUser = getUser(els.roleSelect.value);
    if (nextUser.status !== "Ativo") {
        setRoleMessage("Acesso negado", "error");
        els.roleSelect.value = state.currentUserId;
        return false;
    }

    if (state.usingMockUsers) {
        if (els.rolePassword.value !== nextUser.password) {
            setRoleMessage("Senha incorreta", "error");
            els.roleSelect.value = state.currentUserId;
            els.rolePassword.value = "";
            return false;
        }
    } else {
        try {
            await fetchJsonWithOptions("/auth/login", {
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
    els.mainNav.innerHTML = screens.map((screen) => {
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
        clientes: card("Total de clientes", integer.format(data.kpis.totalClientes), "Clientes mock/API"),
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
    const user = getUser();
    const rows = can("vendas:ver:todas")
        ? monthly
        : monthly.map((item) => ({ ...item, quantidade_de_vendas: Math.max(1, Math.round(item.quantidade_de_vendas * 0.08)), receita_liquida: item.receita_liquida * 0.08, receita_bruta: item.receita_bruta * 0.08, desconto_total: item.desconto_total * 0.08 }));
    els.viewRoot.innerHTML = `
        ${renderKpis(["receita", "vendas", "ticket", "produtos"])}
        <section class="chart-grid">
            ${chartCard(can("vendas:ver:todas") ? "Vendas por mes" : `Vendas de ${user.name}`, "chartSalesMonth")}
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
    const source = state.data?.catalogProducts?.length ? state.data.catalogProducts : mock.produtos;
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
    const clients = state.data?.clients?.length ? state.data.clients : mock.clientes;
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
                    <td><span class="badge">${roleProfiles[user.roleId].name}</span></td>
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
    const clients = state.apiClients.length ? state.apiClients : mock.clientes;
    const products = state.apiProducts.length ? state.apiProducts : mock.produtos;
    const filiais = state.apiFiliais.length ? state.apiFiliais : mock.filiais;
    els.viewRoot.innerHTML = `
        <section class="data-card">
            <h3>Nova Venda</h3>
            <form id="saleForm" class="form-grid">
                <label>Cliente<select name="cliente">${clients.map((client) => `<option>${client.nome}</option>`).join("")}</select></label>
                <label>Produto<select name="produto">${products.map((product) => `<option>${product.produto}</option>`).join("")}</select></label>
                <label>Quantidade<input name="quantidade" type="number" min="1" value="1" required></label>
                <label>Desconto<input name="desconto" type="number" min="0" step="0.01" value="0" required></label>
                <label>Filial<select name="filial" ${role.forcedFilial ? "disabled" : ""}>${filiais.map((filial) => `<option ${filial === role.forcedFilial ? "selected" : ""}>${filial}</option>`).join("")}</select></label>
                <label>Data da venda<input name="data" type="date" required></label>
                <div class="form-actions"><button class="primary-button" type="submit">Cadastrar venda</button><span id="saleFormMessage" class="form-message"></span></div>
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
            <p class="muted">Troque o usuario na Barra de Perfis ou selecione uma tela permitida para continuar.</p>
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
    await loadDashboardData();
    render();
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

    if (state.usingMockUsers) {
        state.users.push({ id: `u-${Date.now()}`, ...user });
        showFormMessage(message, "Usuario cadastrado localmente", "success");
        renderRoles();
        renderUserManagement();
        return;
    }

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
    if (state.usingMock) {
        mock.sales.push(sale);
        showFormMessage(message, "Venda cadastrada localmente e dashboards atualizados", "success");
        await refreshData();
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
        if (state.usingMockUsers) {
            state.users = state.users.filter((user) => user.id !== userId);
            renderRoles();
            renderUserManagement();
            return;
        }
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
        if (state.usingMockUsers) {
            user.status = nextStatus;
            renderRoles();
            renderUserManagement();
            return;
        }
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
    els.btnTrocarUsuario.addEventListener("click", async () => {
        if (await authenticateSelectedUser()) {
            await refreshData();
        }
    });
    els.roleSelect.addEventListener("change", () => {
        setRoleMessage("Digite a senha para trocar de usuario", "success");
    });
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
        await loadProducts();
        await refreshData();
    });
    els.btnAplicar.addEventListener("click", refreshData);
}

async function init() {
    await loadUsers();
    renderRoles();
    bindEvents();
    await loadSelects();
    await refreshData();
    setRoleMessage("Sessao iniciada como Administrador", "success");
}

init().catch((error) => {
    console.error("Erro ao iniciar interface:", error);
    state.usingMock = true;
    showMockNotice();
});

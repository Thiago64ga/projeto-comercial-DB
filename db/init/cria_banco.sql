DROP SCHEMA IF EXISTS comercial CASCADE;
CREATE SCHEMA comercial AUTHORIZATION bi_user;

CREATE TABLE comercial.dim_calendario (
    id_data SERIAL PRIMARY KEY,
    data_completa DATE NOT NULL UNIQUE,
    ano INT NOT NULL,
    mes INT NOT NULL,
    nome_mes VARCHAR(20) NOT NULL,
    trimestre INT NOT NULL,
    semestre INT NOT NULL
);

CREATE TABLE comercial.dim_filial (
    id_filial SERIAL PRIMARY KEY,
    nome_filial VARCHAR(100) NOT NULL UNIQUE,
    cidade VARCHAR(80) NOT NULL,
    uf CHAR(2) NOT NULL,
    regiao VARCHAR(30) NOT NULL,
    porte VARCHAR(30) NOT NULL
);

CREATE TABLE comercial.dim_categoria (
    id_categoria SERIAL PRIMARY KEY,
    nome_categoria VARCHAR(100) NOT NULL UNIQUE,
    descricao VARCHAR(255)
);

CREATE TABLE comercial.dim_produto (
    id_produto SERIAL PRIMARY KEY,
    id_categoria INT NOT NULL REFERENCES comercial.dim_categoria(id_categoria),
    nome_produto VARCHAR(120) NOT NULL UNIQUE,
    marca VARCHAR(80),
    preco_venda NUMERIC(10,2) NOT NULL,
    custo_produto NUMERIC(10,2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ATIVO'
);

CREATE TABLE comercial.dim_cliente (
    id_cliente SERIAL PRIMARY KEY,
    nome_cliente VARCHAR(120) NOT NULL,
    tipo_cliente VARCHAR(30) NOT NULL,
    cidade VARCHAR(80),
    uf CHAR(2),
    data_cadastro DATE NOT NULL
);

CREATE TABLE comercial.app_usuario (
    id_usuario SERIAL PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    senha VARCHAR(120) NOT NULL,
    perfil VARCHAR(30) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Ativo',
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (perfil IN ('admin_comercial', 'gerente_comercial', 'operador_comercial', 'leitura_comercial')),
    CHECK (status IN ('Ativo', 'Inativo')),
    CHECK (LENGTH(nome) >= 3),
    CHECK (LENGTH(senha) >= 6)
);

CREATE TABLE comercial.fato_vendas (
    id_venda BIGSERIAL PRIMARY KEY,
    id_data INT NOT NULL REFERENCES comercial.dim_calendario(id_data),
    id_filial INT NOT NULL REFERENCES comercial.dim_filial(id_filial),
    id_cliente INT REFERENCES comercial.dim_cliente(id_cliente),
    numero_pedido VARCHAR(30) NOT NULL UNIQUE,
    forma_pagamento VARCHAR(40) NOT NULL,
    status_venda VARCHAR(30) NOT NULL DEFAULT 'CONCLUIDA',
    valor_bruto NUMERIC(14,2) NOT NULL,
    desconto NUMERIC(14,2) NOT NULL,
    valor_liquido NUMERIC(14,2) NOT NULL
);

CREATE TABLE comercial.fato_itens_venda (
    id_item BIGSERIAL PRIMARY KEY,
    id_venda BIGINT NOT NULL REFERENCES comercial.fato_vendas(id_venda),
    id_produto INT NOT NULL REFERENCES comercial.dim_produto(id_produto),
    quantidade INT NOT NULL,
    valor_unitario NUMERIC(10,2) NOT NULL,
    custo_unitario NUMERIC(10,2) NOT NULL,
    valor_total NUMERIC(14,2) NOT NULL,
    custo_total NUMERIC(14,2) NOT NULL
);

INSERT INTO comercial.dim_calendario
SELECT
    ROW_NUMBER() OVER () AS id_data,
    gs::date,
    EXTRACT(YEAR FROM gs)::INT,
    EXTRACT(MONTH FROM gs)::INT,
    TO_CHAR(gs, 'TMMonth'),
    EXTRACT(QUARTER FROM gs)::INT,
    CASE WHEN EXTRACT(MONTH FROM gs) <= 6 THEN 1 ELSE 2 END
FROM generate_series(
    CURRENT_DATE - INTERVAL '5 years',
    CURRENT_DATE,
    INTERVAL '1 day'
) AS gs;

INSERT INTO comercial.dim_filial (nome_filial, cidade, uf, regiao, porte) VALUES
('Filial Sao Paulo Centro', 'Sao Paulo', 'SP', 'Sudeste', 'Grande'),
('Filial Campinas', 'Campinas', 'SP', 'Sudeste', 'Media'),
('Filial Rio Capital', 'Rio de Janeiro', 'RJ', 'Sudeste', 'Grande'),
('Filial Belo Horizonte', 'Belo Horizonte', 'MG', 'Sudeste', 'Grande'),
('Filial Curitiba', 'Curitiba', 'PR', 'Sul', 'Media'),
('Filial Porto Alegre', 'Porto Alegre', 'RS', 'Sul', 'Media'),
('Filial Salvador', 'Salvador', 'BA', 'Nordeste', 'Grande'),
('Filial Recife', 'Recife', 'PE', 'Nordeste', 'Media'),
('Filial Goiania', 'Goiania', 'GO', 'Centro-Oeste', 'Media'),
('Filial Brasilia', 'Brasilia', 'DF', 'Centro-Oeste', 'Grande');

INSERT INTO comercial.dim_categoria (nome_categoria, descricao) VALUES
('Perifericos', 'Mouse, teclado, headset e acessórios gamer'),
('Hardware', 'Peças internas para computadores'),
('Computadores', 'Desktops, notebooks e workstations'),
('Monitores', 'Monitores para uso comum e gamer'),
('Armazenamento', 'HDs, SSDs e dispositivos de armazenamento'),
('Redes', 'Roteadores, switches e placas de rede');

INSERT INTO comercial.dim_produto (
    id_categoria, nome_produto, marca, preco_venda, custo_produto, status
) VALUES
(1, 'Mouse Gamer RGB', 'RedTech', 129.90, 70.00, 'ATIVO'),
(1, 'Teclado Mecanico', 'KeyPro', 249.90, 140.00, 'ATIVO'),
(1, 'Headset Gamer 7.1', 'SoundMax', 299.90, 170.00, 'ATIVO'),
(1, 'Mousepad Gamer XL', 'RedTech', 89.90, 35.00, 'ATIVO'),
(2, 'Placa Mae B550', 'TechBoard', 699.90, 470.00, 'ATIVO'),
(2, 'Processador Ryzen 5', 'AMD', 899.90, 650.00, 'ATIVO'),
(2, 'Memoria RAM 16GB', 'FastMemory', 299.90, 180.00, 'ATIVO'),
(2, 'Fonte 650W', 'PowerMax', 399.90, 250.00, 'ATIVO'),
(3, 'Notebook i5 16GB', 'NotePro', 3599.90, 2800.00, 'ATIVO'),
(3, 'PC Gamer Completo', 'ByteMachine', 4999.90, 3800.00, 'ATIVO'),
(3, 'Mini PC Office', 'ByteMachine', 2499.90, 1800.00, 'ATIVO'),
(4, 'Monitor 24 Polegadas', 'ViewMax', 799.90, 520.00, 'ATIVO'),
(4, 'Monitor Gamer 144Hz', 'ViewMax', 1299.90, 850.00, 'ATIVO'),
(4, 'Monitor Ultrawide 29', 'ViewMax', 1699.90, 1100.00, 'ATIVO'),
(5, 'SSD 480GB', 'StorageX', 229.90, 130.00, 'ATIVO'),
(5, 'HD Externo 1TB', 'StorageX', 349.90, 230.00, 'ATIVO'),
(5, 'SSD NVMe 1TB', 'StorageX', 499.90, 310.00, 'ATIVO'),
(6, 'Roteador Dual Band', 'NetFast', 199.90, 110.00, 'ATIVO'),
(6, 'Switch 8 Portas', 'NetFast', 159.90, 90.00, 'ATIVO'),
(6, 'Placa de Rede Wi-Fi', 'NetFast', 139.90, 75.00, 'ATIVO');

INSERT INTO comercial.dim_cliente (
    nome_cliente, tipo_cliente, cidade, uf, data_cadastro
)
SELECT
    'Cliente ' || gs,
    CASE WHEN gs % 4 = 0 THEN 'B2B' ELSE 'B2C' END,
    CASE 
        WHEN gs % 5 = 0 THEN 'Sao Paulo'
        WHEN gs % 5 = 1 THEN 'Belo Horizonte'
        WHEN gs % 5 = 2 THEN 'Rio de Janeiro'
        WHEN gs % 5 = 3 THEN 'Curitiba'
        ELSE 'Brasilia'
    END,
    CASE 
        WHEN gs % 5 = 0 THEN 'SP'
        WHEN gs % 5 = 1 THEN 'MG'
        WHEN gs % 5 = 2 THEN 'RJ'
        WHEN gs % 5 = 3 THEN 'PR'
        ELSE 'DF'
    END,
    CURRENT_DATE - ((RANDOM() * 1000)::INT)
FROM generate_series(1, 500) AS gs;

INSERT INTO comercial.app_usuario (nome, email, senha, perfil, status) VALUES
('Admin Comercial', 'admin@aurora.local', 'admin123', 'admin_comercial', 'Ativo'),
('Gerente Comercial', 'gerente@aurora.local', 'gerente123', 'gerente_comercial', 'Ativo'),
('Operador Comercial', 'operador@aurora.local', 'operador123', 'operador_comercial', 'Ativo'),
('Leitura Comercial', 'leitura@aurora.local', 'leitura123', 'leitura_comercial', 'Ativo');

INSERT INTO comercial.fato_vendas (
    id_data, id_filial, id_cliente, numero_pedido,
    forma_pagamento, status_venda, valor_bruto, desconto, valor_liquido
)
SELECT
    (1 + FLOOR(RANDOM() * (SELECT COUNT(*) FROM comercial.dim_calendario)))::INT,
    (1 + FLOOR(RANDOM() * 10))::INT,
    (1 + FLOOR(RANDOM() * 500))::INT,
    'PED-' || gs,
    CASE 
        WHEN gs % 5 = 0 THEN 'PIX'
        WHEN gs % 5 = 1 THEN 'Cartao Credito'
        WHEN gs % 5 = 2 THEN 'Cartao Debito'
        WHEN gs % 5 = 3 THEN 'Boleto'
        ELSE 'Dinheiro'
    END,
    'CONCLUIDA',
    0,
    0,
    0
FROM generate_series(1, 10000) AS gs;

INSERT INTO comercial.fato_itens_venda (
    id_venda, id_produto, quantidade,
    valor_unitario, custo_unitario, valor_total, custo_total
)
SELECT
    v.id_venda,
    p.id_produto,
    (1 + FLOOR(RANDOM() * 5))::INT,
    p.preco_venda,
    p.custo_produto,
    0,
    0
FROM comercial.fato_vendas v
JOIN comercial.dim_produto p
    ON p.id_produto = ((v.id_venda - 1) % 20) + 1;

UPDATE comercial.fato_itens_venda
SET 
    valor_total = quantidade * valor_unitario,
    custo_total = quantidade * custo_unitario;

UPDATE comercial.fato_vendas v
SET 
    valor_bruto = sub.total_bruto,
    desconto = sub.desconto,
    valor_liquido = sub.total_bruto - sub.desconto
FROM (
    SELECT 
        id_venda,
        SUM(valor_total) AS total_bruto,
        ROUND((SUM(valor_total) * (RANDOM() * 0.10))::NUMERIC, 2) AS desconto
    FROM comercial.fato_itens_venda
    GROUP BY id_venda
) sub
WHERE sub.id_venda = v.id_venda;

CREATE INDEX idx_vendas_data ON comercial.fato_vendas(id_data);
CREATE INDEX idx_vendas_filial ON comercial.fato_vendas(id_filial);
CREATE INDEX idx_vendas_cliente ON comercial.fato_vendas(id_cliente);
CREATE INDEX idx_itens_venda ON comercial.fato_itens_venda(id_venda);
CREATE INDEX idx_itens_produto ON comercial.fato_itens_venda(id_produto);
CREATE INDEX idx_produto_categoria ON comercial.dim_produto(id_categoria);
CREATE INDEX idx_calendario_data ON comercial.dim_calendario(data_completa);
CREATE INDEX idx_app_usuario_perfil ON comercial.app_usuario(perfil);
CREATE INDEX idx_app_usuario_status ON comercial.app_usuario(status);

CREATE MATERIALIZED VIEW comercial.vm_kpis_comercial_mensal AS
SELECT
    c.ano,
    c.mes,
    c.nome_mes,
    DATE_TRUNC('month', c.data_completa)::DATE AS periodo,
    f.nome_filial,
    f.cidade,
    f.uf,
    f.regiao,
    cat.nome_categoria,
    p.nome_produto,
    COUNT(DISTINCT v.id_venda) AS quantidade_de_vendas,
    SUM(i.quantidade) AS quantidade_vendida,
    SUM(i.valor_total) AS faturamento_bruto,
    SUM(v.desconto) AS desconto_total,
    SUM(i.valor_total) - SUM(v.desconto) AS receita_liquida,
    SUM(i.custo_total) AS custo_total,
    SUM(i.valor_total) - SUM(v.desconto) - SUM(i.custo_total) AS margem_bruta,
    ROUND(
        ((SUM(i.valor_total) - SUM(v.desconto) - SUM(i.custo_total))
        / NULLIF(SUM(i.valor_total) - SUM(v.desconto), 0)) * 100,
        2
    ) AS margem_bruta_percentual,
    ROUND(
        (SUM(i.valor_total) - SUM(v.desconto))
        / NULLIF(COUNT(DISTINCT v.id_venda), 0),
        2
    ) AS ticket_medio
FROM comercial.fato_itens_venda i
JOIN comercial.fato_vendas v ON v.id_venda = i.id_venda
JOIN comercial.dim_calendario c ON c.id_data = v.id_data
JOIN comercial.dim_filial f ON f.id_filial = v.id_filial
JOIN comercial.dim_produto p ON p.id_produto = i.id_produto
JOIN comercial.dim_categoria cat ON cat.id_categoria = p.id_categoria
WHERE v.status_venda = 'CONCLUIDA'
GROUP BY
    c.ano, c.mes, c.nome_mes,
    DATE_TRUNC('month', c.data_completa)::DATE,
    f.nome_filial, f.cidade, f.uf, f.regiao,
    cat.nome_categoria, p.nome_produto;

CREATE INDEX idx_vm_comercial_periodo ON comercial.vm_kpis_comercial_mensal(periodo);
CREATE INDEX idx_vm_comercial_filial ON comercial.vm_kpis_comercial_mensal(nome_filial);
CREATE INDEX idx_vm_comercial_produto ON comercial.vm_kpis_comercial_mensal(nome_produto);
CREATE INDEX idx_vm_comercial_categoria ON comercial.vm_kpis_comercial_mensal(nome_categoria);

CREATE OR REPLACE VIEW comercial.vw_resumo_vendas AS
SELECT
    v.id_venda,
    c.data_completa,
    f.nome_filial,
    cli.nome_cliente,
    v.numero_pedido,
    v.forma_pagamento,
    v.status_venda,
    v.valor_bruto,
    v.desconto,
    v.valor_liquido
FROM comercial.fato_vendas v
JOIN comercial.dim_calendario c ON c.id_data = v.id_data
JOIN comercial.dim_filial f ON f.id_filial = v.id_filial
LEFT JOIN comercial.dim_cliente cli ON cli.id_cliente = v.id_cliente;

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'admin_comercial') THEN
        CREATE ROLE admin_comercial LOGIN PASSWORD 'admin123';
    END IF;

    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'gerente_comercial') THEN
        CREATE ROLE gerente_comercial LOGIN PASSWORD 'gerente123';
    END IF;

    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'operador_comercial') THEN
        CREATE ROLE operador_comercial LOGIN PASSWORD 'operador123';
    END IF;

    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'leitura_comercial') THEN
        CREATE ROLE leitura_comercial LOGIN PASSWORD 'leitura123';
    END IF;
END $$;

GRANT ALL PRIVILEGES ON SCHEMA comercial TO admin_comercial;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA comercial TO admin_comercial;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA comercial TO admin_comercial;

GRANT USAGE ON SCHEMA comercial TO gerente_comercial;
GRANT SELECT ON ALL TABLES IN SCHEMA comercial TO gerente_comercial;

GRANT USAGE ON SCHEMA comercial TO operador_comercial;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA comercial TO operador_comercial;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA comercial TO operador_comercial;

GRANT USAGE ON SCHEMA comercial TO leitura_comercial;
GRANT SELECT ON comercial.vw_resumo_vendas TO leitura_comercial;
GRANT SELECT ON comercial.vm_kpis_comercial_mensal TO leitura_comercial;

REVOKE INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA comercial FROM leitura_comercial;

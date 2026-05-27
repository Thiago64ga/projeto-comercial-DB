-- Rede Comercial Aurora - SQL completo consolidado
-- Inclui criacao do banco, triggers, procedures/functions, fix de schema e consultas com subqueries.


-- ============================================================
-- Fonte: db/init/cria_banco.sql
-- ============================================================

-- Rede Comercial Aurora - criacao completa do schema PostgreSQL.
-- Requisitos academicos atendidos neste arquivo:
-- - 10+ tabelas no schema comercial;
-- - 6 triggers uteis;
-- - 8 procedures/functions de negocio;
-- - views/materialized views e dados de teste.

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

CREATE TABLE comercial.dim_fornecedor (
    id_fornecedor SERIAL PRIMARY KEY,
    nome_fornecedor VARCHAR(120) NOT NULL UNIQUE,
    cnpj VARCHAR(20),
    email VARCHAR(120),
    telefone VARCHAR(30),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE comercial.dim_produto (
    id_produto SERIAL PRIMARY KEY,
    id_categoria INT NOT NULL REFERENCES comercial.dim_categoria(id_categoria),
    id_fornecedor INT REFERENCES comercial.dim_fornecedor(id_fornecedor),
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

CREATE TABLE comercial.dim_canal_venda (
    id_canal SERIAL PRIMARY KEY,
    nome_canal VARCHAR(80) NOT NULL UNIQUE,
    descricao VARCHAR(255),
    ativo BOOLEAN NOT NULL DEFAULT TRUE
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

CREATE TABLE comercial.usuarios (
    id_usuario SERIAL PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    perfil VARCHAR(30) NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (LENGTH(TRIM(nome)) >= 3),
    CHECK (LENGTH(TRIM(email)) >= 5),
    CHECK (LENGTH(TRIM(senha_hash)) >= 6),
    CHECK (perfil IN ('admin_comercial', 'gerente_comercial', 'operador_comercial', 'leitura_comercial'))
);

CREATE TABLE comercial.log_operacao (
    id_log BIGSERIAL PRIMARY KEY,
    tabela VARCHAR(80) NOT NULL,
    operacao VARCHAR(20) NOT NULL,
    registro_id TEXT NOT NULL,
    usuario_banco VARCHAR(80) NOT NULL DEFAULT CURRENT_USER,
    detalhes JSONB,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE comercial.fato_vendas (
    id_venda BIGSERIAL PRIMARY KEY,
    id_data INT NOT NULL REFERENCES comercial.dim_calendario(id_data),
    id_filial INT NOT NULL REFERENCES comercial.dim_filial(id_filial),
    id_cliente INT REFERENCES comercial.dim_cliente(id_cliente),
    id_usuario INT REFERENCES comercial.app_usuario(id_usuario),
    id_canal INT REFERENCES comercial.dim_canal_venda(id_canal),
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

CREATE TABLE comercial.movimentacao_estoque (
    id_movimentacao BIGSERIAL PRIMARY KEY,
    id_produto INT NOT NULL REFERENCES comercial.dim_produto(id_produto),
    id_venda BIGINT REFERENCES comercial.fato_vendas(id_venda),
    tipo_movimentacao VARCHAR(20) NOT NULL,
    quantidade INT NOT NULL,
    observacao VARCHAR(255),
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (tipo_movimentacao IN ('ENTRADA', 'SAIDA', 'AJUSTE')),
    CHECK (quantidade > 0)
);

CREATE OR REPLACE FUNCTION comercial.fn_calcular_receita_liquida(
    p_valor_bruto NUMERIC,
    p_desconto NUMERIC
)
RETURNS NUMERIC
LANGUAGE plpgsql
AS $$
BEGIN
    IF COALESCE(p_valor_bruto, 0) < 0 THEN
        RAISE EXCEPTION 'Valor bruto nao pode ser negativo';
    END IF;
    IF COALESCE(p_desconto, 0) < 0 THEN
        RAISE EXCEPTION 'Desconto nao pode ser negativo';
    END IF;
    IF COALESCE(p_desconto, 0) > COALESCE(p_valor_bruto, 0) THEN
        RAISE EXCEPTION 'Desconto nao pode ser maior que o valor bruto';
    END IF;
    RETURN ROUND((COALESCE(p_valor_bruto, 0) - COALESCE(p_desconto, 0))::NUMERIC, 2);
END;
$$;

CREATE OR REPLACE FUNCTION comercial.fn_obter_ou_criar_data(p_data DATE)
RETURNS INT
LANGUAGE plpgsql
AS $$
DECLARE
    v_id_data INT;
BEGIN
    SELECT id_data INTO v_id_data
    FROM comercial.dim_calendario
    WHERE data_completa = p_data;

    IF v_id_data IS NULL THEN
        INSERT INTO comercial.dim_calendario (
            data_completa, ano, mes, nome_mes, trimestre, semestre
        )
        VALUES (
            p_data,
            EXTRACT(YEAR FROM p_data)::INT,
            EXTRACT(MONTH FROM p_data)::INT,
            TO_CHAR(p_data, 'TMMonth'),
            EXTRACT(QUARTER FROM p_data)::INT,
            CASE WHEN EXTRACT(MONTH FROM p_data) <= 6 THEN 1 ELSE 2 END
        )
        RETURNING id_data INTO v_id_data;
    END IF;

    RETURN v_id_data;
END;
$$;

CREATE OR REPLACE FUNCTION comercial.fn_resumo_comercial_subqueries()
RETURNS TABLE (
    total_clientes BIGINT,
    produtos_acima_media BIGINT,
    vendas_acima_ticket_medio BIGINT,
    ultima_venda DATE
)
LANGUAGE sql
AS $$
    SELECT
        (SELECT COUNT(*) FROM comercial.dim_cliente) AS total_clientes,
        (
            SELECT COUNT(*)
            FROM comercial.dim_produto p
            WHERE p.preco_venda > (SELECT AVG(preco_venda) FROM comercial.dim_produto)
        ) AS produtos_acima_media,
        (
            SELECT COUNT(*)
            FROM comercial.fato_vendas v
            WHERE v.valor_liquido > (
                SELECT AVG(valor_liquido)
                FROM comercial.fato_vendas
                WHERE status_venda = 'CONCLUIDA'
            )
        ) AS vendas_acima_ticket_medio,
        (
            SELECT MAX(c.data_completa)
            FROM comercial.fato_vendas v
            JOIN comercial.dim_calendario c ON c.id_data = v.id_data
        ) AS ultima_venda;
$$;

CREATE OR REPLACE PROCEDURE comercial.pr_refresh_kpis()
LANGUAGE plpgsql
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW comercial.vm_kpis_comercial_mensal;
END;
$$;

CREATE OR REPLACE PROCEDURE comercial.pr_cadastrar_usuario(
    p_nome VARCHAR,
    p_email VARCHAR,
    p_senha_hash VARCHAR,
    p_perfil VARCHAR,
    p_ativo BOOLEAN DEFAULT TRUE
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_nome IS NULL OR LENGTH(TRIM(p_nome)) < 3 THEN
        RAISE EXCEPTION 'Nome obrigatorio ou invalido';
    END IF;
    IF p_email IS NULL OR LENGTH(TRIM(p_email)) < 5 THEN
        RAISE EXCEPTION 'Email obrigatorio ou invalido';
    END IF;
    IF p_senha_hash IS NULL OR LENGTH(TRIM(p_senha_hash)) < 6 THEN
        RAISE EXCEPTION 'Senha obrigatoria ou invalida';
    END IF;

    INSERT INTO comercial.usuarios (nome, email, senha_hash, perfil, ativo)
    VALUES (TRIM(p_nome), LOWER(TRIM(p_email)), p_senha_hash, p_perfil, COALESCE(p_ativo, TRUE));
END;
$$;

CREATE OR REPLACE PROCEDURE comercial.pr_cadastrar_produto(
    p_categoria VARCHAR,
    p_produto VARCHAR,
    p_marca VARCHAR,
    p_preco NUMERIC,
    p_custo NUMERIC
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_id_categoria INT;
BEGIN
    SELECT id_categoria INTO v_id_categoria
    FROM comercial.dim_categoria
    WHERE nome_categoria = p_categoria;

    IF v_id_categoria IS NULL THEN
        RAISE EXCEPTION 'Categoria nao encontrada: %', p_categoria;
    END IF;
    IF p_preco <= 0 OR p_custo < 0 THEN
        RAISE EXCEPTION 'Preco ou custo invalido';
    END IF;

    INSERT INTO comercial.dim_produto (
        id_categoria, nome_produto, marca, preco_venda, custo_produto, status
    )
    VALUES (v_id_categoria, TRIM(p_produto), TRIM(p_marca), p_preco, p_custo, 'ATIVO');
END;
$$;

CREATE OR REPLACE FUNCTION comercial.fn_faturamento_periodo(p_inicio DATE, p_fim DATE)
RETURNS NUMERIC
LANGUAGE sql
AS $$
    SELECT COALESCE(SUM(v.valor_liquido), 0)
    FROM comercial.fato_vendas v
    JOIN comercial.dim_calendario c ON c.id_data = v.id_data
    WHERE c.data_completa BETWEEN p_inicio AND p_fim
      AND v.status_venda = 'CONCLUIDA';
$$;

CREATE OR REPLACE FUNCTION comercial.fn_ranking_produtos(p_limite INT DEFAULT 10)
RETURNS TABLE (
    produto VARCHAR,
    quantidade_vendida BIGINT,
    receita_liquida NUMERIC
)
LANGUAGE sql
AS $$
    SELECT
        p.nome_produto,
        SUM(i.quantidade)::BIGINT,
        SUM(i.valor_total - (v.desconto / NULLIF(item_totais.total_itens, 0)))::NUMERIC
    FROM comercial.fato_itens_venda i
    JOIN comercial.fato_vendas v ON v.id_venda = i.id_venda
    JOIN comercial.dim_produto p ON p.id_produto = i.id_produto
    JOIN (
        SELECT id_venda, COUNT(*) AS total_itens
        FROM comercial.fato_itens_venda
        GROUP BY id_venda
    ) item_totais ON item_totais.id_venda = v.id_venda
    WHERE v.status_venda = 'CONCLUIDA'
    GROUP BY p.nome_produto
    ORDER BY SUM(i.quantidade) DESC, SUM(i.valor_total) DESC
    LIMIT GREATEST(COALESCE(p_limite, 10), 1);
$$;

CREATE OR REPLACE FUNCTION comercial.fn_trg_calcular_totais_item()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.quantidade <= 0 THEN
        RAISE EXCEPTION 'Quantidade do item deve ser maior que zero';
    END IF;
    NEW.valor_total := ROUND((NEW.quantidade * NEW.valor_unitario)::NUMERIC, 2);
    NEW.custo_total := ROUND((NEW.quantidade * NEW.custo_unitario)::NUMERIC, 2);
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION comercial.fn_trg_validar_venda()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.valor_liquido := comercial.fn_calcular_receita_liquida(NEW.valor_bruto, NEW.desconto);
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION comercial.fn_trg_auditar_usuario()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO comercial.log_operacao (tabela, operacao, registro_id, detalhes)
    VALUES (
        'app_usuario',
        TG_OP,
        COALESCE(NEW.id_usuario, OLD.id_usuario)::TEXT,
        jsonb_build_object(
            'email', COALESCE(NEW.email, OLD.email),
            'perfil', COALESCE(NEW.perfil, OLD.perfil),
            'status', COALESCE(NEW.status, OLD.status)
        )
    );
    RETURN COALESCE(NEW, OLD);
END;
$$;

CREATE OR REPLACE FUNCTION comercial.fn_trg_auditar_venda()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO comercial.log_operacao (tabela, operacao, registro_id, detalhes)
    VALUES (
        'fato_vendas',
        TG_OP,
        COALESCE(NEW.id_venda, OLD.id_venda)::TEXT,
        jsonb_build_object(
            'numero_pedido', COALESCE(NEW.numero_pedido, OLD.numero_pedido),
            'valor_liquido', COALESCE(NEW.valor_liquido, OLD.valor_liquido)
        )
    );
    RETURN COALESCE(NEW, OLD);
END;
$$;

CREATE OR REPLACE FUNCTION comercial.fn_trg_atualizar_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.atualizado_em := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION comercial.fn_trg_movimentar_estoque_venda()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO comercial.movimentacao_estoque (
        id_produto,
        id_venda,
        tipo_movimentacao,
        quantidade,
        observacao
    )
    VALUES (
        NEW.id_produto,
        NEW.id_venda,
        'SAIDA',
        NEW.quantidade,
        'Saida automatica por venda'
    );
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_calcular_totais_item
BEFORE INSERT OR UPDATE ON comercial.fato_itens_venda
FOR EACH ROW EXECUTE FUNCTION comercial.fn_trg_calcular_totais_item();

CREATE TRIGGER trg_validar_venda
BEFORE INSERT OR UPDATE ON comercial.fato_vendas
FOR EACH ROW EXECUTE FUNCTION comercial.fn_trg_validar_venda();

CREATE TRIGGER trg_auditar_usuario
AFTER INSERT OR UPDATE OR DELETE ON comercial.app_usuario
FOR EACH ROW EXECUTE FUNCTION comercial.fn_trg_auditar_usuario();

CREATE TRIGGER trg_auditar_venda
AFTER INSERT OR UPDATE OR DELETE ON comercial.fato_vendas
FOR EACH ROW EXECUTE FUNCTION comercial.fn_trg_auditar_venda();

CREATE TRIGGER trg_usuarios_updated_at
BEFORE UPDATE ON comercial.usuarios
FOR EACH ROW EXECUTE FUNCTION comercial.fn_trg_atualizar_updated_at();

CREATE TRIGGER trg_movimentar_estoque_venda
AFTER INSERT ON comercial.fato_itens_venda
FOR EACH ROW EXECUTE FUNCTION comercial.fn_trg_movimentar_estoque_venda();

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
('Perifericos', 'Mouse, teclado, headset e acessÃ³rios gamer'),
('Hardware', 'PeÃ§as internas para computadores'),
('Computadores', 'Desktops, notebooks e workstations'),
('Monitores', 'Monitores para uso comum e gamer'),
('Armazenamento', 'HDs, SSDs e dispositivos de armazenamento'),
('Redes', 'Roteadores, switches e placas de rede');

INSERT INTO comercial.dim_fornecedor (nome_fornecedor, cnpj, email, telefone) VALUES
('Aurora Distribuidora Tech', '12.345.678/0001-10', 'contato@auroradist.local', '(11) 3000-1000'),
('Norte Sul Componentes', '23.456.789/0001-20', 'vendas@nortesul.local', '(31) 3000-2000'),
('Rede Digital Atacado', '34.567.890/0001-30', 'comercial@rededigital.local', '(41) 3000-3000');

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

INSERT INTO comercial.dim_canal_venda (nome_canal, descricao) VALUES
('Loja Fisica', 'Venda presencial registrada em filial'),
('E-commerce', 'Venda realizada pelo canal digital'),
('Televendas', 'Venda realizada por atendimento remoto'),
('Marketplace', 'Venda intermediada por parceiro');

INSERT INTO comercial.app_usuario (nome, email, senha, perfil, status) VALUES
('Admin Comercial', 'admin@aurora.local', 'admin123', 'admin_comercial', 'Ativo'),
('Gerente Comercial', 'gerente@aurora.local', 'gerente123', 'gerente_comercial', 'Ativo'),
('Operador Comercial', 'operador@aurora.local', 'operador123', 'operador_comercial', 'Ativo'),
('Leitura Comercial', 'leitura@aurora.local', 'leitura123', 'leitura_comercial', 'Ativo');

INSERT INTO comercial.usuarios (nome, email, senha_hash, perfil, ativo) VALUES
('Admin Comercial', 'admin@aurora.local', 'admin123', 'admin_comercial', TRUE),
('Gerente Comercial', 'gerente@aurora.local', 'gerente123', 'gerente_comercial', TRUE),
('Operador Comercial', 'operador@aurora.local', 'operador123', 'operador_comercial', TRUE),
('Leitura Comercial', 'leitura@aurora.local', 'leitura123', 'leitura_comercial', TRUE);

INSERT INTO comercial.fato_vendas (
    id_data, id_filial, id_cliente, id_usuario, id_canal, numero_pedido,
    forma_pagamento, status_venda, valor_bruto, desconto, valor_liquido
)
SELECT
    (1 + FLOOR(RANDOM() * (SELECT COUNT(*) FROM comercial.dim_calendario)))::INT,
    (1 + FLOOR(RANDOM() * 10))::INT,
    (1 + FLOOR(RANDOM() * 500))::INT,
    (1 + FLOOR(RANDOM() * 4))::INT,
    (1 + FLOOR(RANDOM() * 4))::INT,
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
CREATE INDEX idx_vendas_usuario ON comercial.fato_vendas(id_usuario);
CREATE INDEX idx_vendas_canal ON comercial.fato_vendas(id_canal);
CREATE INDEX idx_itens_venda ON comercial.fato_itens_venda(id_venda);
CREATE INDEX idx_itens_produto ON comercial.fato_itens_venda(id_produto);
CREATE INDEX idx_produto_categoria ON comercial.dim_produto(id_categoria);
CREATE INDEX idx_calendario_data ON comercial.dim_calendario(data_completa);
CREATE INDEX idx_app_usuario_perfil ON comercial.app_usuario(perfil);
CREATE INDEX idx_app_usuario_status ON comercial.app_usuario(status);
CREATE INDEX idx_log_operacao_tabela ON comercial.log_operacao(tabela, criado_em);

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
JOIN comercial.dim_canal_venda cv ON cv.id_canal = v.id_canal
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
    cv.nome_canal,
    u.nome AS responsavel,
    v.numero_pedido,
    v.forma_pagamento,
    v.status_venda,
    v.valor_bruto,
    v.desconto,
    v.valor_liquido
FROM comercial.fato_vendas v
JOIN comercial.dim_calendario c ON c.id_data = v.id_data
JOIN comercial.dim_filial f ON f.id_filial = v.id_filial
LEFT JOIN comercial.dim_canal_venda cv ON cv.id_canal = v.id_canal
LEFT JOIN comercial.dim_cliente cli ON cli.id_cliente = v.id_cliente
LEFT JOIN comercial.app_usuario u ON u.id_usuario = v.id_usuario;

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
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA comercial TO admin_comercial;

GRANT USAGE ON SCHEMA comercial TO gerente_comercial;
GRANT SELECT ON ALL TABLES IN SCHEMA comercial TO gerente_comercial;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA comercial TO gerente_comercial;

GRANT USAGE ON SCHEMA comercial TO operador_comercial;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA comercial TO operador_comercial;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA comercial TO operador_comercial;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA comercial TO operador_comercial;

GRANT USAGE ON SCHEMA comercial TO leitura_comercial;
GRANT SELECT ON comercial.vw_resumo_vendas TO leitura_comercial;
GRANT SELECT ON comercial.vm_kpis_comercial_mensal TO leitura_comercial;
GRANT EXECUTE ON FUNCTION comercial.fn_resumo_comercial_subqueries() TO leitura_comercial;

REVOKE INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA comercial FROM leitura_comercial;

-- ============================================================
-- Fonte: db/fixes/001_add_coluna_ativo.sql
-- ============================================================

ALTER TABLE comercial.dim_canal_venda
ADD COLUMN IF NOT EXISTS ativo BOOLEAN DEFAULT TRUE;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'comercial'
          AND table_name = 'dim_canal_venda'
          AND column_name = 'status'
    ) THEN
        UPDATE comercial.dim_canal_venda
        SET ativo = COALESCE(
            UPPER(status) NOT IN ('INATIVO', 'INATIVA', 'INACTIVE', 'FALSE', '0'),
            TRUE
        )
        WHERE ativo IS NULL;
    ELSE
        UPDATE comercial.dim_canal_venda
        SET ativo = TRUE
        WHERE ativo IS NULL;
    END IF;
END $$;

ALTER TABLE comercial.dim_canal_venda
ALTER COLUMN ativo SET DEFAULT TRUE;

ALTER TABLE comercial.dim_canal_venda
ALTER COLUMN ativo SET NOT NULL;


-- ============================================================
-- Fonte: db/consultas_subqueries.sql
-- ============================================================

-- 1. Produtos que venderam acima da media geral de quantidade.
SELECT
    p.nome_produto,
    SUM(i.quantidade) AS quantidade_vendida
FROM comercial.dim_produto p
JOIN comercial.fato_itens_venda i ON i.id_produto = p.id_produto
GROUP BY p.nome_produto
HAVING SUM(i.quantidade) > (
    SELECT AVG(total_produto)
    FROM (
        SELECT SUM(i2.quantidade) AS total_produto
        FROM comercial.fato_itens_venda i2
        GROUP BY i2.id_produto
    ) media_produtos
)
ORDER BY quantidade_vendida DESC;

-- 2. Filiais com receita maior que a media geral das filiais.
SELECT
    filial.nome_filial,
    filial.receita_liquida
FROM (
    SELECT
        f.nome_filial,
        SUM(v.valor_liquido) AS receita_liquida
    FROM comercial.fato_vendas v
    JOIN comercial.dim_filial f ON f.id_filial = v.id_filial
    GROUP BY f.nome_filial
) filial
WHERE filial.receita_liquida > (
    SELECT AVG(receita_filial)
    FROM (
        SELECT SUM(v2.valor_liquido) AS receita_filial
        FROM comercial.fato_vendas v2
        GROUP BY v2.id_filial
    ) medias
)
ORDER BY filial.receita_liquida DESC;

-- 3. Clientes que possuem compras, usando EXISTS.
SELECT
    c.nome_cliente,
    c.tipo_cliente
FROM comercial.dim_cliente c
WHERE EXISTS (
    SELECT 1
    FROM comercial.fato_vendas v
    WHERE v.id_cliente = c.id_cliente
)
ORDER BY c.nome_cliente
LIMIT 100;

-- 4. Categorias com faturamento superior a media das categorias, usando IN.
SELECT
    c.nome_categoria
FROM comercial.dim_categoria c
WHERE c.id_categoria IN (
    SELECT p.id_categoria
    FROM comercial.dim_produto p
    JOIN comercial.fato_itens_venda i ON i.id_produto = p.id_produto
    GROUP BY p.id_categoria
    HAVING SUM(i.valor_total) > (
        SELECT AVG(faturamento_categoria)
        FROM (
            SELECT SUM(i2.valor_total) AS faturamento_categoria
            FROM comercial.dim_produto p2
            JOIN comercial.fato_itens_venda i2 ON i2.id_produto = p2.id_produto
            GROUP BY p2.id_categoria
        ) medias
    )
);

-- 5. Produtos nunca vendidos.
SELECT
    p.nome_produto
FROM comercial.dim_produto p
WHERE p.id_produto NOT IN (
    SELECT DISTINCT id_produto
    FROM comercial.fato_itens_venda
)
ORDER BY p.nome_produto;

-- 6. Vendas acima do ticket medio.
SELECT
    v.numero_pedido,
    v.valor_liquido,
    (SELECT AVG(valor_liquido) FROM comercial.fato_vendas WHERE status_venda = 'CONCLUIDA') AS ticket_medio
FROM comercial.fato_vendas v
WHERE v.valor_liquido > (
    SELECT AVG(valor_liquido)
    FROM comercial.fato_vendas
    WHERE status_venda = 'CONCLUIDA'
)
ORDER BY v.valor_liquido DESC;


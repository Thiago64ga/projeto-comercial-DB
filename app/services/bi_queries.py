from sqlalchemy import text

from app.db import get_session 
from datetime import date, datetime
import re

PERFIS_VALIDOS = {"admin_comercial", "gerente_comercial", "operador_comercial", "leitura_comercial"}
STATUS_USUARIO_VALIDOS = {"Ativo", "Inativo"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
TIPOS_CLIENTE_VALIDOS = {"B2B", "B2C"}
STATUS_PRODUTO_VALIDOS = {"ATIVO", "INATIVO"}
PERFIL_ALIASES = {
    "Administrador": "admin_comercial",
    "Admin": "admin_comercial",
    "Gerente Comercial": "gerente_comercial",
    "Operador Comercial": "operador_comercial",
    "Leitura Comercial": "leitura_comercial",
}

def executar_validacao_banco():
    """
    Abre uma sessão temporária e testa a conexão com o Postgres.
    Se o banco estiver fora, o SQLAlchemy lança a exceção.
    """
    session = get_session()
    try:
        session.execute(text("SELECT 1"))
    finally:
        session.close() # Garante que a sessão feche para não travar o pool




    
def get_filiais():
    """Retorna a query para listar as filiais únicas."""
    
    
    sql = """
        SELECT nome_filial
        FROM comercial.vm_kpis_comercial_mensal
        GROUP BY nome_filial
        ORDER BY nome_filial
    """
    return text(sql)

def get_produtos(categoria=None):

    sql = """
        SELECT DISTINCT nome_produto
        FROM comercial.vm_kpis_comercial_mensal
        WHERE 1=1
    """

    if categoria:
        sql += " AND nome_categoria = :categoria"

    sql += " ORDER BY nome_produto"

    return text(sql)

def get_produtos_detalhados(categoria=None):
    sql = """
        SELECT
            p.id_produto AS id,
            p.nome_produto AS produto,
            c.nome_categoria AS categoria,
            p.marca,
            p.preco_venda AS preco,
            p.status,
            COALESCE(SUM(vm.quantidade_vendida), 0) AS vendidos,
            COALESCE(SUM(vm.receita_liquida), 0) AS receita
        FROM comercial.dim_produto p
        JOIN comercial.dim_categoria c ON c.id_categoria = p.id_categoria
        LEFT JOIN comercial.vm_kpis_comercial_mensal vm
            ON vm.nome_produto = p.nome_produto
        WHERE 1=1
    """
    params = {}

    if categoria:
        sql += " AND c.nome_categoria = :categoria"
        params["categoria"] = categoria

    sql += """
        GROUP BY
            p.id_produto,
            p.nome_produto,
            c.nome_categoria,
            p.marca,
            p.preco_venda,
            p.status
        ORDER BY p.nome_produto
    """

    return text(sql), params

def get_clientes():
    sql = """
        SELECT
            id_cliente AS id,
            nome_cliente AS nome,
            tipo_cliente AS tipo,
            cidade,
            uf,
            data_cadastro AS cadastro
        FROM comercial.dim_cliente
        ORDER BY nome_cliente
        LIMIT 500
    """
    return text(sql)

def normalizar_usuario(row):
    return {
        "id": f"u-{row.id_usuario}",
        "id_usuario": int(row.id_usuario),
        "dbId": int(row.id_usuario),
        "name": row.nome,
        "nome": row.nome,
        "email": row.email,
        "roleId": row.perfil,
        "perfil": row.perfil,
        "status": row.status,
        "ativo": row.status == "Ativo",
    }

def resolver_responsavel_venda(session, usuario_id=None):
    candidato = None
    if usuario_id:
        try:
            candidato = int(str(usuario_id).replace("u-", ""))
        except (TypeError, ValueError):
            candidato = None

    if candidato:
        existe = session.execute(
            text("SELECT id_usuario FROM comercial.app_usuario WHERE id_usuario = :id_usuario"),
            {"id_usuario": candidato}
        ).fetchone()
        if existe:
            return int(existe.id_usuario)

    fallback = session.execute(text("""
        SELECT id_usuario
        FROM comercial.app_usuario
        WHERE email = 'admin@aurora.local'
           OR perfil = 'admin_comercial'
        ORDER BY
            CASE WHEN email = 'admin@aurora.local' THEN 0 ELSE 1 END,
            id_usuario
        LIMIT 1
    """)).fetchone()
    return int(fallback.id_usuario) if fallback else None

def validar_usuario(nome, email, senha, perfil, status="Ativo", exigir_senha=True):
    perfil = PERFIL_ALIASES.get(perfil, perfil)
    if not nome or len(nome.strip()) < 3:
        raise ValueError("O nome deve ter pelo menos 3 caracteres.")
    if not email or not EMAIL_RE.match(email.strip()):
        raise ValueError("Informe um email valido.")
    if perfil not in PERFIS_VALIDOS:
        raise ValueError("Perfil invalido.")
    if status not in STATUS_USUARIO_VALIDOS:
        raise ValueError("Status invalido.")
    if exigir_senha and (not senha or len(str(senha)) < 6):
        raise ValueError("A senha deve ter pelo menos 6 caracteres.")

def normalizar_perfil(perfil):
    return PERFIL_ALIASES.get(perfil, perfil)

def garantir_extensoes_modelo(session):
    session.execute(text("""
        CREATE TABLE IF NOT EXISTS comercial.dim_fornecedor (
            id_fornecedor SERIAL PRIMARY KEY,
            nome_fornecedor VARCHAR(120) NOT NULL UNIQUE,
            cnpj VARCHAR(20),
            email VARCHAR(120),
            telefone VARCHAR(30),
            ativo BOOLEAN NOT NULL DEFAULT TRUE,
            criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """))
    session.execute(text("""
        INSERT INTO comercial.dim_fornecedor (nome_fornecedor, cnpj, email, telefone)
        VALUES
            ('Aurora Distribuidora Tech', '12.345.678/0001-10', 'contato@auroradist.local', '(11) 3000-1000'),
            ('Norte Sul Componentes', '23.456.789/0001-20', 'vendas@nortesul.local', '(31) 3000-2000'),
            ('Rede Digital Atacado', '34.567.890/0001-30', 'comercial@rededigital.local', '(41) 3000-3000')
        ON CONFLICT (nome_fornecedor) DO NOTHING
    """))
    session.execute(text("""
        ALTER TABLE comercial.dim_produto
        ADD COLUMN IF NOT EXISTS id_fornecedor INT REFERENCES comercial.dim_fornecedor(id_fornecedor)
    """))
    session.execute(text("""
        CREATE TABLE IF NOT EXISTS comercial.usuarios (
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
        )
    """))
    session.execute(text("""
        CREATE TABLE IF NOT EXISTS comercial.dim_canal_venda (
            id_canal SERIAL PRIMARY KEY,
            nome_canal VARCHAR(80) NOT NULL UNIQUE,
            descricao VARCHAR(255),
            ativo BOOLEAN NOT NULL DEFAULT TRUE
        )
    """))
    session.execute(text("""
        ALTER TABLE comercial.dim_canal_venda
        ADD COLUMN IF NOT EXISTS ativo BOOLEAN DEFAULT TRUE
    """))
    session.execute(text("""
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
    """))
    session.execute(text("""
        ALTER TABLE comercial.dim_canal_venda
        ALTER COLUMN ativo SET DEFAULT TRUE
    """))
    session.execute(text("""
        ALTER TABLE comercial.dim_canal_venda
        ALTER COLUMN ativo SET NOT NULL
    """))
    session.execute(text("""
        CREATE TABLE IF NOT EXISTS comercial.log_operacao (
            id_log BIGSERIAL PRIMARY KEY,
            tabela VARCHAR(80) NOT NULL,
            operacao VARCHAR(20) NOT NULL,
            registro_id TEXT NOT NULL,
            usuario_banco VARCHAR(80) NOT NULL DEFAULT CURRENT_USER,
            detalhes JSONB,
            criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """))
    session.execute(text("""
        CREATE TABLE IF NOT EXISTS comercial.movimentacao_estoque (
            id_movimentacao BIGSERIAL PRIMARY KEY,
            id_produto INT NOT NULL REFERENCES comercial.dim_produto(id_produto),
            id_venda BIGINT REFERENCES comercial.fato_vendas(id_venda),
            tipo_movimentacao VARCHAR(20) NOT NULL,
            quantidade INT NOT NULL,
            observacao VARCHAR(255),
            criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CHECK (tipo_movimentacao IN ('ENTRADA', 'SAIDA', 'AJUSTE')),
            CHECK (quantidade > 0)
        )
    """))
    session.execute(text("""
        INSERT INTO comercial.dim_canal_venda (nome_canal, descricao)
        VALUES
            ('Loja Fisica', 'Venda presencial registrada em filial'),
            ('E-commerce', 'Venda realizada pelo canal digital'),
            ('Televendas', 'Venda realizada por atendimento remoto'),
            ('Marketplace', 'Venda intermediada por parceiro')
        ON CONFLICT (nome_canal) DO NOTHING
    """))
    session.execute(text("""
        ALTER TABLE comercial.fato_vendas
        ADD COLUMN IF NOT EXISTS id_canal INT REFERENCES comercial.dim_canal_venda(id_canal)
    """))
    session.execute(text("""
        UPDATE comercial.fato_vendas
        SET id_canal = (SELECT id_canal FROM comercial.dim_canal_venda WHERE nome_canal = 'Loja Fisica')
        WHERE id_canal IS NULL
    """))
    session.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_vendas_canal ON comercial.fato_vendas(id_canal)
    """))
    session.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_log_operacao_tabela ON comercial.log_operacao(tabela, criado_em)
    """))
    session.execute(text("""
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
    """))
    session.execute(text("""
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
    """))
    session.execute(text("""
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
    """))
    session.execute(text("""
        CREATE OR REPLACE PROCEDURE comercial.pr_refresh_kpis()
        LANGUAGE plpgsql
        AS $$
        BEGIN
            REFRESH MATERIALIZED VIEW comercial.vm_kpis_comercial_mensal;
        END;
        $$;
    """))
    session.execute(text("""
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
    """))
    session.execute(text("""
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
    """))
    session.execute(text("""
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
    """))
    session.execute(text("""
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
    """))
    session.execute(text("""
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
    """))
    session.execute(text("""
        CREATE OR REPLACE FUNCTION comercial.fn_trg_validar_venda()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        AS $$
        BEGIN
            NEW.valor_liquido := comercial.fn_calcular_receita_liquida(NEW.valor_bruto, NEW.desconto);
            RETURN NEW;
        END;
        $$;
    """))
    session.execute(text("""
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
    """))
    session.execute(text("""
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
    """))
    session.execute(text("""
        CREATE OR REPLACE FUNCTION comercial.fn_trg_atualizar_updated_at()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        AS $$
        BEGIN
            NEW.atualizado_em := CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$;
    """))
    session.execute(text("""
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
    """))
    session.execute(text("DROP TRIGGER IF EXISTS trg_calcular_totais_item ON comercial.fato_itens_venda"))
    session.execute(text("""
        CREATE TRIGGER trg_calcular_totais_item
        BEFORE INSERT OR UPDATE ON comercial.fato_itens_venda
        FOR EACH ROW EXECUTE FUNCTION comercial.fn_trg_calcular_totais_item()
    """))
    session.execute(text("DROP TRIGGER IF EXISTS trg_validar_venda ON comercial.fato_vendas"))
    session.execute(text("""
        CREATE TRIGGER trg_validar_venda
        BEFORE INSERT OR UPDATE ON comercial.fato_vendas
        FOR EACH ROW EXECUTE FUNCTION comercial.fn_trg_validar_venda()
    """))
    session.execute(text("DROP TRIGGER IF EXISTS trg_auditar_usuario ON comercial.app_usuario"))
    session.execute(text("""
        CREATE TRIGGER trg_auditar_usuario
        AFTER INSERT OR UPDATE OR DELETE ON comercial.app_usuario
        FOR EACH ROW EXECUTE FUNCTION comercial.fn_trg_auditar_usuario()
    """))
    session.execute(text("DROP TRIGGER IF EXISTS trg_auditar_venda ON comercial.fato_vendas"))
    session.execute(text("""
        CREATE TRIGGER trg_auditar_venda
        AFTER INSERT OR UPDATE OR DELETE ON comercial.fato_vendas
        FOR EACH ROW EXECUTE FUNCTION comercial.fn_trg_auditar_venda()
    """))
    session.execute(text("DROP TRIGGER IF EXISTS trg_usuarios_updated_at ON comercial.usuarios"))
    session.execute(text("""
        CREATE TRIGGER trg_usuarios_updated_at
        BEFORE UPDATE ON comercial.usuarios
        FOR EACH ROW EXECUTE FUNCTION comercial.fn_trg_atualizar_updated_at()
    """))
    session.execute(text("DROP TRIGGER IF EXISTS trg_movimentar_estoque_venda ON comercial.fato_itens_venda"))
    session.execute(text("""
        CREATE TRIGGER trg_movimentar_estoque_venda
        AFTER INSERT ON comercial.fato_itens_venda
        FOR EACH ROW EXECUTE FUNCTION comercial.fn_trg_movimentar_estoque_venda()
    """))

def garantir_tabela_usuarios(session):
    session.execute(text("""
        CREATE TABLE IF NOT EXISTS comercial.app_usuario (
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
        )
    """))
    session.execute(text("""
        DO $$
        DECLARE
            constraint_name text;
        BEGIN
            FOR constraint_name IN
                SELECT con.conname
                FROM pg_constraint con
                JOIN pg_class rel ON rel.oid = con.conrelid
                JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
                WHERE nsp.nspname = 'comercial'
                  AND rel.relname = 'app_usuario'
                  AND con.contype = 'c'
                  AND pg_get_constraintdef(con.oid) LIKE '%administrador%'
            LOOP
                EXECUTE format('ALTER TABLE comercial.app_usuario DROP CONSTRAINT %I', constraint_name);
            END LOOP;

        END $$;
    """))
    session.execute(text("""
        UPDATE comercial.app_usuario
        SET perfil = CASE perfil
            WHEN 'administrador' THEN 'admin_comercial'
            WHEN 'gerente' THEN 'gerente_comercial'
            WHEN 'vendedor' THEN 'operador_comercial'
            WHEN 'analista' THEN 'leitura_comercial'
            ELSE perfil
        END
        WHERE perfil IN ('administrador', 'gerente', 'vendedor', 'analista')
    """))
    session.execute(text("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint con
                JOIN pg_class rel ON rel.oid = con.conrelid
                JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
                WHERE nsp.nspname = 'comercial'
                  AND rel.relname = 'app_usuario'
                  AND con.contype = 'c'
                  AND pg_get_constraintdef(con.oid) LIKE '%admin_comercial%'
            ) THEN
                ALTER TABLE comercial.app_usuario
                ADD CONSTRAINT app_usuario_perfil_check
                CHECK (perfil IN ('admin_comercial', 'gerente_comercial', 'operador_comercial', 'leitura_comercial'));
            END IF;
        END $$;
    """))

    total = session.execute(text("SELECT COUNT(*) FROM comercial.app_usuario")).scalar_one()
    if total == 0:
        session.execute(text("""
            INSERT INTO comercial.app_usuario (nome, email, senha, perfil, status) VALUES
            ('Admin Comercial', 'admin@aurora.local', 'admin123', 'admin_comercial', 'Ativo'),
            ('Gerente Comercial', 'gerente@aurora.local', 'gerente123', 'gerente_comercial', 'Ativo'),
            ('Operador Comercial', 'operador@aurora.local', 'operador123', 'operador_comercial', 'Ativo'),
            ('Leitura Comercial', 'leitura@aurora.local', 'leitura123', 'leitura_comercial', 'Ativo')
        """))
    session.execute(text("""
        CREATE TABLE IF NOT EXISTS comercial.usuarios (
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
        )
    """))
    session.execute(text("""
        INSERT INTO comercial.usuarios (nome, email, senha_hash, perfil, ativo)
        SELECT nome, email, senha, perfil, status = 'Ativo'
        FROM comercial.app_usuario
        ON CONFLICT (email) DO NOTHING
    """))

def garantir_responsavel_venda(session):
    garantir_tabela_usuarios(session)
    garantir_extensoes_modelo(session)
    session.execute(text("""
        ALTER TABLE comercial.fato_vendas
        ADD COLUMN IF NOT EXISTS id_usuario INT REFERENCES comercial.app_usuario(id_usuario)
    """))
    session.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_vendas_usuario
        ON comercial.fato_vendas(id_usuario)
    """))
    session.execute(text("DROP VIEW IF EXISTS comercial.vw_resumo_vendas"))
    session.execute(text("""
        CREATE VIEW comercial.vw_resumo_vendas AS
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
        LEFT JOIN comercial.app_usuario u ON u.id_usuario = v.id_usuario
    """))

def get_usuarios(session):
    garantir_tabela_usuarios(session)
    result = session.execute(text("""
        SELECT id_usuario, nome, email, perfil, status
        FROM comercial.app_usuario
        ORDER BY id_usuario
    """))
    return [normalizar_usuario(row) for row in result]

def autenticar_usuario(session, user_id, senha):
    garantir_tabela_usuarios(session)
    db_id = str(user_id or "").replace("u-", "")

    row = session.execute(
        text("""
            SELECT id_usuario, nome, email, perfil, status
            FROM comercial.app_usuario
            WHERE id_usuario = :id_usuario
              AND senha = :senha
        """),
        {"id_usuario": db_id, "senha": senha}
    ).fetchone()

    if not row:
        raise ValueError("Senha incorreta.")
    if row.status != "Ativo":
        raise ValueError("Acesso negado. Usuario inativo.")

    return normalizar_usuario(row)

def autenticar_usuario_por_email(session, email, senha):
    garantir_tabela_usuarios(session)
    email = (email or "").strip().lower()

    row = session.execute(
        text("""
            SELECT id_usuario, nome, email, perfil, status
            FROM comercial.app_usuario
            WHERE email = :email
              AND senha = :senha
        """),
        {"email": email, "senha": senha}
    ).fetchone()

    if not row:
        raise ValueError("Email ou senha incorretos.")
    if row.status != "Ativo":
        raise ValueError("Acesso negado. Usuario inativo.")

    return normalizar_usuario(row)

def criar_usuario(session, nome, email, senha, perfil, status="Ativo"):
    garantir_tabela_usuarios(session)
    nome = (nome or "").strip()
    email = (email or "").strip().lower()
    perfil = normalizar_perfil(perfil)
    validar_usuario(nome, email, senha, perfil, status)

    email_existe = session.execute(
        text("SELECT 1 FROM comercial.app_usuario WHERE email = :email"),
        {"email": email}
    ).fetchone()

    if email_existe:
        raise ValueError("Ja existe um usuario com esse email.")

    row = session.execute(
        text("""
            INSERT INTO comercial.app_usuario (nome, email, senha, perfil, status)
            VALUES (:nome, :email, :senha, :perfil, :status)
            RETURNING id_usuario, nome, email, perfil, status
        """),
        {
            "nome": nome,
            "email": email,
            "senha": senha,
            "perfil": perfil,
            "status": status,
        }
    ).fetchone()
    session.execute(
        text("""
            INSERT INTO comercial.usuarios (nome, email, senha_hash, perfil, ativo)
            VALUES (:nome, :email, :senha, :perfil, :ativo)
            ON CONFLICT (email) DO UPDATE
            SET
                nome = EXCLUDED.nome,
                senha_hash = EXCLUDED.senha_hash,
                perfil = EXCLUDED.perfil,
                ativo = EXCLUDED.ativo,
                atualizado_em = CURRENT_TIMESTAMP
        """),
        {
            "nome": nome,
            "email": email,
            "senha": senha,
            "perfil": perfil,
            "ativo": status == "Ativo",
        }
    )

    return normalizar_usuario(row)

def atualizar_status_usuario(session, user_id, status):
    garantir_tabela_usuarios(session)
    if status not in STATUS_USUARIO_VALIDOS:
        raise ValueError("Status invalido.")

    db_id = str(user_id or "").replace("u-", "")
    usuario_atual = session.execute(
        text("""
            SELECT perfil, status, email
            FROM comercial.app_usuario
            WHERE id_usuario = :id_usuario
        """),
        {"id_usuario": db_id}
    ).fetchone()

    if not usuario_atual:
        raise ValueError("Usuario nao encontrado.")

    if usuario_atual.perfil == "admin_comercial" and usuario_atual.status == "Ativo" and status == "Inativo":
        admins_ativos = session.execute(text("""
            SELECT COUNT(*)
            FROM comercial.app_usuario
            WHERE perfil = 'admin_comercial'
              AND status = 'Ativo'
        """)).scalar_one()

        if admins_ativos <= 1:
            raise ValueError("Nao e permitido inativar o ultimo administrador ativo.")

    row = session.execute(
        text("""
            UPDATE comercial.app_usuario
            SET status = :status
            WHERE id_usuario = :id_usuario
            RETURNING id_usuario, nome, email, perfil, status
        """),
        {"id_usuario": db_id, "status": status}
    ).fetchone()

    if not row:
        raise ValueError("Usuario nao encontrado.")

    session.execute(
        text("""
            UPDATE comercial.usuarios
            SET ativo = :ativo, atualizado_em = CURRENT_TIMESTAMP
            WHERE email = :email
        """),
        {"ativo": status == "Ativo", "email": row.email}
    )

    return normalizar_usuario(row)

def obter_usuario(session, user_id):
    garantir_tabela_usuarios(session)
    db_id = str(user_id or "").replace("u-", "")
    row = session.execute(
        text("""
            SELECT id_usuario, nome, email, perfil, status
            FROM comercial.app_usuario
            WHERE id_usuario = :id_usuario
        """),
        {"id_usuario": db_id}
    ).fetchone()
    if not row:
        raise ValueError("Usuario nao encontrado.")
    return normalizar_usuario(row)

def atualizar_usuario(session, user_id, dados):
    garantir_tabela_usuarios(session)
    db_id = str(user_id or "").replace("u-", "")
    atual = obter_usuario(session, db_id)
    nome = (dados.get("name") or dados.get("nome") or atual["name"]).strip()
    email = (dados.get("email") or atual["email"]).strip().lower()
    perfil = dados.get("roleId") or dados.get("perfil") or atual["roleId"]
    status = dados.get("status") or ("Ativo" if dados.get("ativo", atual["status"] == "Ativo") else "Inativo")
    senha = dados.get("password") or dados.get("senha") or dados.get("senha_hash")
    validar_usuario(nome, email, senha or "senha123", perfil, status, exigir_senha=False)

    email_existe = session.execute(
        text("""
            SELECT 1
            FROM comercial.app_usuario
            WHERE email = :email
              AND id_usuario <> :id_usuario
        """),
        {"email": email, "id_usuario": db_id}
    ).fetchone()
    if email_existe:
        raise ValueError("Ja existe um usuario com esse email.")

    if senha:
        row = session.execute(
            text("""
                UPDATE comercial.app_usuario
                SET nome = :nome, email = :email, senha = :senha, perfil = :perfil, status = :status
                WHERE id_usuario = :id_usuario
                RETURNING id_usuario, nome, email, perfil, status
            """),
            {"id_usuario": db_id, "nome": nome, "email": email, "senha": senha, "perfil": perfil, "status": status}
        ).fetchone()
    else:
        row = session.execute(
            text("""
                UPDATE comercial.app_usuario
                SET nome = :nome, email = :email, perfil = :perfil, status = :status
                WHERE id_usuario = :id_usuario
                RETURNING id_usuario, nome, email, perfil, status
            """),
            {"id_usuario": db_id, "nome": nome, "email": email, "perfil": perfil, "status": status}
        ).fetchone()
    if not row:
        raise ValueError("Usuario nao encontrado.")

    session.execute(
        text("""
            INSERT INTO comercial.usuarios (nome, email, senha_hash, perfil, ativo)
            VALUES (:nome, :email, COALESCE(:senha, 'senha_mantida'), :perfil, :ativo)
            ON CONFLICT (email) DO UPDATE
            SET nome = EXCLUDED.nome,
                senha_hash = CASE WHEN :senha IS NULL THEN comercial.usuarios.senha_hash ELSE EXCLUDED.senha_hash END,
                perfil = EXCLUDED.perfil,
                ativo = EXCLUDED.ativo
        """),
        {"nome": nome, "email": email, "senha": senha, "perfil": perfil, "ativo": status == "Ativo"}
    )
    return normalizar_usuario(row)

def remover_usuario(session, user_id):
    garantir_tabela_usuarios(session)
    db_id = str(user_id or "").replace("u-", "")
    usuario_atual = session.execute(
        text("""
            SELECT perfil, status, email
            FROM comercial.app_usuario
            WHERE id_usuario = :id_usuario
        """),
        {"id_usuario": db_id}
    ).fetchone()

    if not usuario_atual:
        raise ValueError("Usuario nao encontrado.")

    if usuario_atual.perfil == "admin_comercial" and usuario_atual.status == "Ativo":
        admins_ativos = session.execute(text("""
            SELECT COUNT(*)
            FROM comercial.app_usuario
            WHERE perfil = 'admin_comercial'
              AND status = 'Ativo'
        """)).scalar_one()

        if admins_ativos <= 1:
            raise ValueError("Nao e permitido remover o ultimo administrador ativo.")

    row = session.execute(
        text("""
            DELETE FROM comercial.app_usuario
            WHERE id_usuario = :id_usuario
            RETURNING id_usuario
        """),
        {"id_usuario": db_id}
    ).fetchone()

    if not row:
        raise ValueError("Usuario nao encontrado.")
    session.execute(
        text("""
            UPDATE comercial.usuarios
            SET ativo = FALSE, atualizado_em = CURRENT_TIMESTAMP
            WHERE email = :email
        """),
        {"email": usuario_atual.email}
    )

def criar_cliente(session, nome, tipo, cidade, uf, data_cadastro=None):
    nome = (nome or "").strip()
    tipo = (tipo or "").strip().upper()
    cidade = (cidade or "").strip()
    uf = (uf or "").strip().upper()
    data_cadastro = data_cadastro or date.today().isoformat()

    if len(nome) < 3:
        raise ValueError("O nome do cliente deve ter pelo menos 3 caracteres.")
    if tipo not in TIPOS_CLIENTE_VALIDOS:
        raise ValueError("Tipo de cliente invalido.")
    if uf and len(uf) != 2:
        raise ValueError("UF deve ter 2 letras.")
    try:
        data_cadastro = date.fromisoformat(str(data_cadastro)).isoformat()
    except (TypeError, ValueError):
        raise ValueError("Data de cadastro invalida.")

    row = session.execute(
        text("""
            INSERT INTO comercial.dim_cliente (
                nome_cliente,
                tipo_cliente,
                cidade,
                uf,
                data_cadastro
            )
            VALUES (:nome, :tipo, :cidade, :uf, CAST(:data_cadastro AS DATE))
            RETURNING nome_cliente AS nome, tipo_cliente AS tipo, cidade, uf, data_cadastro AS cadastro
        """),
        {
            "nome": nome,
            "tipo": tipo,
            "cidade": cidade or None,
            "uf": uf or None,
            "data_cadastro": data_cadastro,
        }
    ).fetchone()

    return {
        "nome": row.nome,
        "tipo": row.tipo,
        "cidade": row.cidade,
        "uf": row.uf,
        "cadastro": row.cadastro.isoformat() if row.cadastro else None,
    }

def listar_clientes_api(session):
    result = session.execute(text("""
        SELECT
            id_cliente,
            nome_cliente,
            tipo_cliente,
            cidade,
            uf,
            data_cadastro
        FROM comercial.dim_cliente
        ORDER BY id_cliente
        LIMIT 500
    """))
    return [
        {
            "id": int(row.id_cliente),
            "nome": row.nome_cliente,
            "tipo": row.tipo_cliente,
            "cidade": row.cidade,
            "uf": row.uf,
            "cadastro": row.data_cadastro.isoformat() if row.data_cadastro else None,
        }
        for row in result
    ]

def criar_produto(session, nome, categoria, marca, preco, custo, status="ATIVO"):
    nome = (nome or "").strip()
    categoria = (categoria or "").strip()
    marca = (marca or "").strip()
    status = (status or "ATIVO").strip().upper()

    if len(nome) < 3:
        raise ValueError("O nome do produto deve ter pelo menos 3 caracteres.")
    if status not in STATUS_PRODUTO_VALIDOS:
        raise ValueError("Status do produto invalido.")
    try:
        preco = float(preco)
        custo = float(custo)
    except (TypeError, ValueError):
        raise ValueError("Preco e custo devem ser numeros validos.")
    if preco <= 0:
        raise ValueError("Preco deve ser maior que zero.")
    if custo < 0:
        raise ValueError("Custo nao pode ser negativo.")

    categoria_row = session.execute(
        text("SELECT id_categoria FROM comercial.dim_categoria WHERE nome_categoria = :categoria"),
        {"categoria": categoria}
    ).fetchone()
    if not categoria_row:
        raise ValueError("Categoria nao encontrada no banco de dados.")

    existe = session.execute(
        text("SELECT 1 FROM comercial.dim_produto WHERE nome_produto = :nome"),
        {"nome": nome}
    ).fetchone()
    if existe:
        raise ValueError("Ja existe um produto com esse nome.")

    row = session.execute(
        text("""
            INSERT INTO comercial.dim_produto (
                id_categoria,
                nome_produto,
                marca,
                preco_venda,
                custo_produto,
                status
            )
            VALUES (:id_categoria, :nome, :marca, :preco, :custo, :status)
            RETURNING id_produto
        """),
        {
            "id_categoria": categoria_row.id_categoria,
            "nome": nome,
            "marca": marca or None,
            "preco": preco,
            "custo": custo,
            "status": status,
        }
    ).fetchone()

    return {
        "id_produto": int(row.id_produto),
        "produto": nome,
        "categoria": categoria,
        "marca": marca,
        "preco": preco,
        "status": status,
        "vendidos": 0,
        "receita": 0,
    }

def listar_produtos_api(session):
    garantir_extensoes_modelo(session)
    result = session.execute(text("""
        SELECT
            p.id_produto,
            p.nome_produto,
            c.nome_categoria,
            p.marca,
            p.preco_venda,
            p.custo_produto,
            p.status
        FROM comercial.dim_produto p
        JOIN comercial.dim_categoria c ON c.id_categoria = p.id_categoria
        ORDER BY p.id_produto
    """))
    return [
        {
            "id": int(row.id_produto),
            "produto": row.nome_produto,
            "categoria": row.nome_categoria,
            "marca": row.marca,
            "preco": float(row.preco_venda),
            "custo": float(row.custo_produto),
            "status": row.status,
        }
        for row in result
    ]

def atualizar_produto(session, id_produto, dados):
    garantir_extensoes_modelo(session)
    produto_atual = session.execute(
        text("SELECT 1 FROM comercial.dim_produto WHERE id_produto = :id_produto"),
        {"id_produto": id_produto}
    ).fetchone()
    if not produto_atual:
        raise ValueError("Produto nao encontrado.")

    nome = (dados.get("produto") or dados.get("nome") or "").strip()
    categoria = (dados.get("categoria") or "").strip()
    marca = (dados.get("marca") or "").strip()
    status = (dados.get("status") or "ATIVO").strip().upper()
    preco = dados.get("preco")
    custo = dados.get("custo")

    if len(nome) < 3:
        raise ValueError("O nome do produto deve ter pelo menos 3 caracteres.")
    if status not in STATUS_PRODUTO_VALIDOS:
        raise ValueError("Status do produto invalido.")
    try:
        preco = float(preco)
        custo = float(custo)
    except (TypeError, ValueError):
        raise ValueError("Preco e custo devem ser numeros validos.")
    if preco <= 0 or custo < 0:
        raise ValueError("Preco ou custo invalido.")

    categoria_row = session.execute(
        text("SELECT id_categoria FROM comercial.dim_categoria WHERE nome_categoria = :categoria"),
        {"categoria": categoria}
    ).fetchone()
    if not categoria_row:
        raise ValueError("Categoria nao encontrada.")

    row = session.execute(
        text("""
            UPDATE comercial.dim_produto
            SET
                id_categoria = :id_categoria,
                nome_produto = :nome,
                marca = :marca,
                preco_venda = :preco,
                custo_produto = :custo,
                status = :status
            WHERE id_produto = :id_produto
            RETURNING id_produto
        """),
        {
            "id_produto": id_produto,
            "id_categoria": categoria_row.id_categoria,
            "nome": nome,
            "marca": marca or None,
            "preco": preco,
            "custo": custo,
            "status": status,
        }
    ).fetchone()
    return {"id": int(row.id_produto), "produto": nome}

def remover_produto(session, id_produto):
    usado = session.execute(
        text("SELECT 1 FROM comercial.fato_itens_venda WHERE id_produto = :id_produto LIMIT 1"),
        {"id_produto": id_produto}
    ).fetchone()
    if usado:
        raise ValueError("Produto possui vendas vinculadas e nao pode ser removido.")
    row = session.execute(
        text("DELETE FROM comercial.dim_produto WHERE id_produto = :id_produto RETURNING id_produto"),
        {"id_produto": id_produto}
    ).fetchone()
    if not row:
        raise ValueError("Produto nao encontrado.")

def criar_filial(session, nome, cidade, uf, regiao, porte):
    nome = (nome or "").strip()
    cidade = (cidade or "").strip()
    uf = (uf or "").strip().upper()
    regiao = (regiao or "").strip()
    porte = (porte or "").strip()
    if not all([nome, cidade, uf, regiao, porte]):
        raise ValueError("Campo obrigatorio nao informado.")
    if len(uf) != 2:
        raise ValueError("UF deve ter 2 letras.")
    row = session.execute(
        text("""
            INSERT INTO comercial.dim_filial (nome_filial, cidade, uf, regiao, porte)
            VALUES (:nome, :cidade, :uf, :regiao, :porte)
            RETURNING id_filial, nome_filial, cidade, uf, regiao, porte
        """),
        {"nome": nome, "cidade": cidade, "uf": uf, "regiao": regiao, "porte": porte}
    ).fetchone()
    return {
        "id": int(row.id_filial),
        "nome": row.nome_filial,
        "cidade": row.cidade,
        "uf": row.uf,
        "regiao": row.regiao,
        "porte": row.porte,
    }

def listar_filiais_api(session):
    result = session.execute(text("""
        SELECT id_filial, nome_filial, cidade, uf, regiao, porte
        FROM comercial.dim_filial
        ORDER BY id_filial
    """))
    return [
        {
            "id": int(row.id_filial),
            "nome": row.nome_filial,
            "cidade": row.cidade,
            "uf": row.uf,
            "regiao": row.regiao,
            "porte": row.porte,
        }
        for row in result
    ]

def criar_categoria(session, nome, descricao=None):
    nome = (nome or "").strip()
    descricao = (descricao or "").strip()
    if len(nome) < 3:
        raise ValueError("O nome da categoria deve ter pelo menos 3 caracteres.")
    row = session.execute(
        text("""
            INSERT INTO comercial.dim_categoria (nome_categoria, descricao)
            VALUES (:nome, :descricao)
            RETURNING id_categoria, nome_categoria, descricao
        """),
        {"nome": nome, "descricao": descricao or None}
    ).fetchone()
    return {"id": int(row.id_categoria), "nome": row.nome_categoria, "descricao": row.descricao}

def listar_categorias_api(session):
    result = session.execute(text("""
        SELECT id_categoria, nome_categoria, descricao
        FROM comercial.dim_categoria
        ORDER BY id_categoria
    """))
    return [
        {"id": int(row.id_categoria), "nome": row.nome_categoria, "descricao": row.descricao}
        for row in result
    ]

def criar_venda(session, cliente, produto, filial, quantidade, desconto, data_venda, usuario_id=None, canal="Loja Fisica"):
    garantir_responsavel_venda(session)

    try:
        quantidade = int(quantidade)
    except (TypeError, ValueError):
        raise ValueError("Quantidade invalida.")

    if quantidade < 1:
        raise ValueError("A quantidade deve ser maior que zero.")

    try:
        desconto = float(desconto or 0)
    except (TypeError, ValueError):
        raise ValueError("Desconto invalido.")

    if desconto < 0:
        raise ValueError("O desconto nao pode ser negativo.")

    try:
        data_venda = date.fromisoformat(str(data_venda)).isoformat()
    except (TypeError, ValueError):
        raise ValueError("Data da venda invalida.")

    produto_row = session.execute(
        text("""
            SELECT id_produto, preco_venda, custo_produto
            FROM comercial.dim_produto
            WHERE nome_produto = :produto
        """),
        {"produto": produto}
    ).fetchone()

    filial_row = session.execute(
        text("""
            SELECT id_filial
            FROM comercial.dim_filial
            WHERE nome_filial = :filial
        """),
        {"filial": filial}
    ).fetchone()

    cliente_row = session.execute(
        text("""
            SELECT id_cliente
            FROM comercial.dim_cliente
            WHERE nome_cliente = :cliente
            ORDER BY id_cliente
            LIMIT 1
        """),
        {"cliente": cliente}
    ).fetchone()

    if not produto_row:
        raise ValueError("Produto nao encontrado no banco de dados.")
    if not filial_row:
        raise ValueError("Filial nao encontrada no banco de dados.")
    if not cliente_row:
        raise ValueError("Cliente nao encontrado no banco de dados.")

    canal_row = session.execute(
        text("""
            SELECT id_canal
            FROM comercial.dim_canal_venda
            WHERE nome_canal = :canal
              AND ativo = TRUE
        """),
        {"canal": canal or "Loja Fisica"}
    ).fetchone()

    if not canal_row:
        raise ValueError("Canal de venda nao encontrado no banco de dados.")

    responsavel_id = resolver_responsavel_venda(session, usuario_id)

    valor_bruto = float(produto_row.preco_venda) * quantidade
    desconto = min(max(desconto, 0), valor_bruto)
    valor_liquido = float(session.execute(
        text("""
            SELECT comercial.fn_calcular_receita_liquida(
                CAST(:valor_bruto AS NUMERIC),
                CAST(:desconto AS NUMERIC)
            )
        """),
        {"valor_bruto": valor_bruto, "desconto": desconto}
    ).scalar_one())
    custo_total = float(produto_row.custo_produto) * quantidade
    numero_pedido = f"PED-APP-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

    id_data = session.execute(
        text("SELECT comercial.fn_obter_ou_criar_data(CAST(:data_venda AS DATE))"),
        {"data_venda": data_venda}
    ).scalar_one()

    id_venda = session.execute(
        text("""
            INSERT INTO comercial.fato_vendas (
                id_data,
                id_filial,
                id_cliente,
                id_usuario,
                id_canal,
                numero_pedido,
                forma_pagamento,
                status_venda,
                valor_bruto,
                desconto,
                valor_liquido
            )
            VALUES (
                :id_data,
                :id_filial,
                :id_cliente,
                :id_usuario,
                :id_canal,
                :numero_pedido,
                'PIX',
                'CONCLUIDA',
                :valor_bruto,
                :desconto,
                :valor_liquido
            )
            RETURNING id_venda
        """),
        {
            "id_data": id_data,
            "id_filial": filial_row.id_filial,
            "id_cliente": cliente_row.id_cliente,
            "id_usuario": responsavel_id,
            "id_canal": canal_row.id_canal,
            "numero_pedido": numero_pedido,
            "valor_bruto": valor_bruto,
            "desconto": desconto,
            "valor_liquido": valor_liquido,
        }
    ).scalar_one()

    session.execute(
        text("""
            INSERT INTO comercial.fato_itens_venda (
                id_venda,
                id_produto,
                quantidade,
                valor_unitario,
                custo_unitario,
                valor_total,
                custo_total
            )
            VALUES (
                :id_venda,
                :id_produto,
                :quantidade,
                :valor_unitario,
                :custo_unitario,
                :valor_total,
                :custo_total
            )
        """),
        {
            "id_venda": id_venda,
            "id_produto": produto_row.id_produto,
            "quantidade": quantidade,
            "valor_unitario": produto_row.preco_venda,
            "custo_unitario": produto_row.custo_produto,
            "valor_total": valor_bruto,
            "custo_total": custo_total,
        }
    )

    session.execute(text("CALL comercial.pr_refresh_kpis()"))

    return {
        "id_venda": int(id_venda),
        "numero_pedido": numero_pedido,
        "valor_bruto": valor_bruto,
        "desconto": desconto,
        "valor_liquido": valor_liquido,
    }

def criar_venda_api(session, dados, usuario_id=None):
    garantir_responsavel_venda(session)
    itens = dados.get("itens") or []
    if not itens:
        raise ValueError("A venda precisa ter pelo menos um item.")

    try:
        id_filial = int(dados.get("id_filial"))
        id_cliente = int(dados.get("id_cliente"))
    except (TypeError, ValueError):
        raise ValueError("Filial e cliente sao obrigatorios.")

    canal_raw = dados.get("id_canal") or dados.get("canal") or dados.get("nome_canal")
    id_canal = None
    nome_canal = None
    try:
        id_canal = int(canal_raw)
    except (TypeError, ValueError):
        nome_canal = str(canal_raw or "").strip()
    if not id_canal and not nome_canal:
        raise ValueError("Canal e obrigatorio.")

    data_venda = dados.get("data_venda") or dados.get("data")
    try:
        data_venda = date.fromisoformat(str(data_venda)).isoformat()
    except (TypeError, ValueError):
        raise ValueError("Data da venda invalida.")

    filial_row = session.execute(
        text("SELECT id_filial FROM comercial.dim_filial WHERE id_filial = :id"),
        {"id": id_filial}
    ).fetchone()
    cliente_row = session.execute(
        text("SELECT id_cliente FROM comercial.dim_cliente WHERE id_cliente = :id"),
        {"id": id_cliente}
    ).fetchone()
    if id_canal:
        canal_row = session.execute(
            text("SELECT id_canal FROM comercial.dim_canal_venda WHERE id_canal = :id AND ativo = TRUE"),
            {"id": id_canal}
        ).fetchone()
    else:
        canal_row = session.execute(
            text("""
                SELECT id_canal
                FROM comercial.dim_canal_venda
                WHERE LOWER(nome_canal) = LOWER(:nome_canal)
                  AND ativo = TRUE
            """),
            {"nome_canal": nome_canal}
        ).fetchone()
    if not filial_row:
        raise ValueError("Filial nao encontrada.")
    if not cliente_row:
        raise ValueError("Cliente nao encontrado.")
    if not canal_row:
        detalhe_canal = nome_canal or id_canal
        raise ValueError(f"Canal de venda nao encontrado: {detalhe_canal}.")
    id_canal = int(canal_row.id_canal)

    responsavel_id = resolver_responsavel_venda(session, usuario_id)

    id_data = session.execute(
        text("SELECT comercial.fn_obter_ou_criar_data(CAST(:data_venda AS DATE))"),
        {"data_venda": data_venda}
    ).scalar_one()

    itens_normalizados = []
    total_bruto = 0.0
    desconto_total = 0.0

    for item in itens:
        try:
            id_produto = int(item.get("id_produto"))
            quantidade = int(item.get("quantidade"))
            desconto_item = float(item.get("desconto") or 0)
        except (TypeError, ValueError):
            raise ValueError("Item da venda invalido.")
        if quantidade <= 0:
            raise ValueError("Quantidade deve ser maior que zero.")
        if desconto_item < 0:
            raise ValueError("Desconto nao pode ser negativo.")

        produto_row = session.execute(
            text("""
                SELECT id_produto, preco_venda, custo_produto
                FROM comercial.dim_produto
                WHERE id_produto = :id_produto
            """),
            {"id_produto": id_produto}
        ).fetchone()
        if not produto_row:
            raise ValueError(f"Produto nao encontrado: {id_produto}.")

        preco_unitario = item.get("preco_unitario")
        if preco_unitario in (None, ""):
            preco_unitario = float(produto_row.preco_venda)
        else:
            try:
                preco_unitario = float(preco_unitario)
            except (TypeError, ValueError):
                raise ValueError("Preco unitario invalido.")
        if preco_unitario <= 0:
            raise ValueError("Preco unitario deve ser maior que zero.")

        valor_total = preco_unitario * quantidade
        if desconto_item > valor_total:
            raise ValueError("Desconto do item nao pode ser maior que o total do item.")

        total_bruto += valor_total
        desconto_total += desconto_item
        itens_normalizados.append({
            "id_produto": id_produto,
            "quantidade": quantidade,
            "valor_unitario": preco_unitario,
            "custo_unitario": float(produto_row.custo_produto),
            "valor_total": valor_total,
            "custo_total": float(produto_row.custo_produto) * quantidade,
        })

    receita_liquida = float(session.execute(
        text("""
            SELECT comercial.fn_calcular_receita_liquida(
                CAST(:valor_bruto AS NUMERIC),
                CAST(:desconto AS NUMERIC)
            )
        """),
        {"valor_bruto": total_bruto, "desconto": desconto_total}
    ).scalar_one())

    numero_pedido = f"PED-APP-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    id_venda = session.execute(
        text("""
            INSERT INTO comercial.fato_vendas (
                id_data,
                id_filial,
                id_cliente,
                id_usuario,
                id_canal,
                numero_pedido,
                forma_pagamento,
                status_venda,
                valor_bruto,
                desconto,
                valor_liquido
            )
            VALUES (
                :id_data,
                :id_filial,
                :id_cliente,
                :id_usuario,
                :id_canal,
                :numero_pedido,
                :forma_pagamento,
                'CONCLUIDA',
                :valor_bruto,
                :desconto,
                :valor_liquido
            )
            RETURNING id_venda
        """),
        {
            "id_data": id_data,
            "id_filial": id_filial,
            "id_cliente": id_cliente,
            "id_usuario": responsavel_id,
            "id_canal": id_canal,
            "numero_pedido": numero_pedido,
            "forma_pagamento": dados.get("forma_pagamento", "PIX"),
            "valor_bruto": total_bruto,
            "desconto": desconto_total,
            "valor_liquido": receita_liquida,
        }
    ).scalar_one()

    for item in itens_normalizados:
        session.execute(
            text("""
                INSERT INTO comercial.fato_itens_venda (
                    id_venda,
                    id_produto,
                    quantidade,
                    valor_unitario,
                    custo_unitario,
                    valor_total,
                    custo_total
                )
                VALUES (
                    :id_venda,
                    :id_produto,
                    :quantidade,
                    :valor_unitario,
                    :custo_unitario,
                    :valor_total,
                    :custo_total
                )
            """),
            {"id_venda": id_venda, **item}
        )

    session.execute(text("CALL comercial.pr_refresh_kpis()"))

    return {
        "id_venda": int(id_venda),
        "numero_pedido": numero_pedido,
        "total_bruto": total_bruto,
        "desconto_total": desconto_total,
        "receita_liquida": receita_liquida,
    }

def get_vendas_recentes(session, limite=50):
    garantir_responsavel_venda(session)
    try:
        limite = int(limite)
    except (TypeError, ValueError):
        limite = 50
    limite = min(max(limite, 1), 100)

    result = session.execute(
        text("""
            SELECT
                v.id_venda,
                c.data_completa,
                f.nome_filial,
                COALESCE(cv.nome_canal, 'Loja Fisica') AS canal,
                cli.nome_cliente,
                COALESCE(u.nome, 'Carga inicial') AS responsavel,
                v.numero_pedido,
                v.valor_liquido,
                STRING_AGG(p.nome_produto, ', ' ORDER BY p.nome_produto) AS produtos,
                SUM(i.quantidade) AS quantidade
            FROM comercial.fato_vendas v
            JOIN comercial.dim_calendario c ON c.id_data = v.id_data
            JOIN comercial.dim_filial f ON f.id_filial = v.id_filial
            LEFT JOIN comercial.dim_canal_venda cv ON cv.id_canal = v.id_canal
            LEFT JOIN comercial.dim_cliente cli ON cli.id_cliente = v.id_cliente
            LEFT JOIN comercial.app_usuario u ON u.id_usuario = v.id_usuario
            JOIN comercial.fato_itens_venda i ON i.id_venda = v.id_venda
            JOIN comercial.dim_produto p ON p.id_produto = i.id_produto
            GROUP BY
                v.id_venda,
                c.data_completa,
                f.nome_filial,
                cv.nome_canal,
                cli.nome_cliente,
                u.nome,
                v.numero_pedido,
                v.valor_liquido
            ORDER BY v.id_venda DESC
            LIMIT :limite
        """),
        {"limite": limite}
    )

    return [
        {
            "id": int(row.id_venda),
            "data": row.data_completa.isoformat() if row.data_completa else None,
            "filial": row.nome_filial,
            "canal": row.canal,
            "cliente": row.nome_cliente,
            "responsavel": row.responsavel,
            "numeroPedido": row.numero_pedido,
            "valorLiquido": float(row.valor_liquido or 0),
            "produtos": row.produtos,
            "quantidade": int(row.quantidade or 0),
        }
        for row in result
    ]

def get_categorias():
    """Retorna a Query da lista de Categorias"""

    sql = """
                SELECT nome_categoria
                FROM comercial.vm_kpis_comercial_mensal
                GROUP BY nome_categoria
                Order BY nome_categoria
                """
    return text(sql)

def get_canais(session):
    garantir_responsavel_venda(session)
    result = session.execute(text("""
        SELECT nome_canal
        FROM comercial.dim_canal_venda
        WHERE ativo = TRUE
        ORDER BY nome_canal
    """))
    return [row.nome_canal for row in result]

def listar_canais_api(session):
    garantir_responsavel_venda(session)
    result = session.execute(text("""
        SELECT id_canal, nome_canal, descricao, ativo
        FROM comercial.dim_canal_venda
        WHERE ativo = TRUE
        ORDER BY id_canal
    """))
    return [
        {
            "id": int(row.id_canal),
            "nome": row.nome_canal,
            "descricao": row.descricao,
            "ativo": bool(row.ativo),
        }
        for row in result
    ]

def get_resumo_subqueries(session):
    garantir_responsavel_venda(session)
    row = session.execute(text("""
        SELECT *
        FROM comercial.fn_resumo_comercial_subqueries()
    """)).fetchone()
    return {
        "totalClientes": int(row.total_clientes or 0),
        "produtosAcimaMedia": int(row.produtos_acima_media or 0),
        "vendasAcimaTicketMedio": int(row.vendas_acima_ticket_medio or 0),
        "ultimaVenda": row.ultima_venda.isoformat() if row.ultima_venda else None,
    }


def get_rotinas_banco(session):
    garantir_responsavel_venda(session)
    triggers = session.execute(text("""
        SELECT
            trigger_name,
            event_object_table,
            action_timing,
            event_manipulation
        FROM information_schema.triggers
        WHERE trigger_schema = 'comercial'
        ORDER BY event_object_table, trigger_name, event_manipulation
    """)).fetchall()
    rotinas = session.execute(text("""
        SELECT
            routine_name,
            routine_type,
            data_type
        FROM information_schema.routines
        WHERE specific_schema = 'comercial'
          AND routine_name NOT LIKE 'fn_trg_%'
        ORDER BY routine_type, routine_name
    """)).fetchall()

    return {
        "totalTriggers": len(triggers),
        "totalRotinas": len(rotinas),
        "requisitoTriggersOk": len(triggers) >= 4,
        "requisitoRotinasOk": len(rotinas) >= 4,
        "triggers": [
            {
                "nome": row.trigger_name,
                "tabela": row.event_object_table,
                "momento": row.action_timing,
                "evento": row.event_manipulation,
            }
            for row in triggers
        ],
        "rotinas": [
            {
                "nome": row.routine_name,
                "tipo": row.routine_type,
                "retorno": row.data_type,
            }
            for row in rotinas
        ],
    }


def executar_demo_rotinas_banco(session):
    garantir_responsavel_venda(session)
    session.execute(text("CALL comercial.pr_refresh_kpis()"))

    receita_liquida = session.execute(text("""
        SELECT comercial.fn_calcular_receita_liquida(1000.00, 75.50)
    """)).scalar_one()
    resumo = get_resumo_subqueries(session)
    faturamento = session.execute(text("""
        SELECT comercial.fn_faturamento_periodo((CURRENT_DATE - INTERVAL '365 days')::DATE, CURRENT_DATE)
    """)).scalar_one()
    ranking = session.execute(text("""
        SELECT *
        FROM comercial.fn_ranking_produtos(5)
    """)).fetchall()

    return {
        "procedureExecutada": "comercial.pr_refresh_kpis",
        "functionsExecutadas": [
            "comercial.fn_calcular_receita_liquida",
            "comercial.fn_resumo_comercial_subqueries",
            "comercial.fn_faturamento_periodo",
            "comercial.fn_ranking_produtos",
        ],
        "receitaLiquidaExemplo": float(receita_liquida or 0),
        "faturamentoPeriodo": float(faturamento or 0),
        "resumoSubqueries": resumo,
        "rankingProdutos": [
            {
                "produto": row.produto,
                "quantidadeVendida": int(row.quantidade_vendida or 0),
                "receitaLiquida": float(row.receita_liquida or 0),
            }
            for row in ranking
        ],
    }



def get_faturamento(filial=None,produto = None,categoria = None, data_inicio=None, data_fim=None):
    """
    Monta a query de faturamento dinamicamente com base nos filtros.
    Se os filtros forem None, retorna o total geral.
    """
    sql = "SELECT SUM(faturamento_bruto) as total FROM comercial.vm_kpis_comercial_mensal WHERE 1=1 "
    params = {}

    if filial:
        sql += " AND nome_filial = :filial"
        params['filial'] = filial

    if produto:
        sql += " AND nome_produto = :produto"
        params['produto'] = produto

    if categoria:
        sql += " AND nome_categoria = :categoria"
        params['categoria'] = categoria
    
    if data_inicio and data_fim:
        sql += " AND periodo BETWEEN :inicio AND :fim"
        params['inicio'] = data_inicio
        params['fim'] = data_fim

    return text(sql), params


def get_receitaLiquida(filial=None,produto = None,categoria = None, data_inicio=None, data_fim=None):
    """
    Monta a query da receita liquida dinamicamente com base nos filtros.
    Se os filtros forem None, retorna o total geral.
    """
    sql = "SELECT SUM(receita_liquida) as total FROM comercial.vm_kpis_comercial_mensal WHERE 1=1 "
    params = {}

    if filial:
        sql += " AND nome_filial = :filial"
        params['filial'] = filial

    if produto:
        sql += " AND nome_produto = :produto"
        params['produto'] = produto

    if categoria:
        sql += " AND nome_categoria = :categoria"
        params['categoria'] = categoria
    
    if data_inicio and data_fim:
        sql += " AND periodo BETWEEN :inicio AND :fim"
        params['inicio'] = data_inicio
        params['fim'] = data_fim

    return text(sql), params


def get_margem_bruta(filial=None,produto = None,categoria = None, data_inicio=None, data_fim=None):
    """
    Monta a query da receita liquida dinamicamente com base nos filtros.
    Se os filtros forem None, retorna o total geral.
    """
    sql = "SELECT SUM(margem_bruta) as total FROM comercial.vm_kpis_comercial_mensal WHERE 1=1 "
    params = {}

    if filial:
        sql += " AND nome_filial = :filial"
        params['filial'] = filial

    if produto:
        sql += " AND nome_produto = :produto"
        params['produto'] = produto

    if categoria:
        sql += " AND nome_categoria = :categoria"
        params['categoria'] = categoria
    
    if data_inicio and data_fim:
        sql += " AND periodo BETWEEN :inicio AND :fim"
        params['inicio'] = data_inicio
        params['fim'] = data_fim

    return text(sql), params



def get_margem_bruta_percentual(filial=None,produto = None,categoria = None, data_inicio=None, data_fim=None):
    """
    Monta a query da receita liquida dinamicamente com base nos filtros.
    Se os filtros forem None, retorna o total geral.
    """
    sql = "SELECT AVG(margem_bruta_percentual) as total FROM comercial.vm_kpis_comercial_mensal WHERE 1=1 "
    params = {}

    if filial:
        sql += " AND nome_filial = :filial"
        params['filial'] = filial

    if produto:
        sql += " AND nome_produto = :produto"
        params['produto'] = produto

    if categoria:
        sql += " AND nome_categoria = :categoria"
        params['categoria'] = categoria
    
    if data_inicio and data_fim:
        sql += " AND periodo BETWEEN :inicio AND :fim"
        params['inicio'] = data_inicio
        params['fim'] = data_fim

    return text(sql), params


    
def get_custo_total(filial=None,produto = None,categoria = None, data_inicio=None, data_fim=None):
    """
    Monta a query de faturamento dinamicamente com base nos filtros.
    Se os filtros forem None, retorna o total geral.
    """
    sql = "SELECT SUM(custo_total) as total FROM comercial.vm_kpis_comercial_mensal WHERE 1=1 "
    params = {}

    if filial:
        sql += " AND nome_filial = :filial"
        params['filial'] = filial

    if produto:
        sql += " AND nome_produto = :produto"
        params['produto'] = produto

    if categoria:
        sql += " AND nome_categoria = :categoria"
        params['categoria'] = categoria
    
    if data_inicio and data_fim:
        sql += " AND periodo BETWEEN :inicio AND :fim"
        params['inicio'] = data_inicio
        params['fim'] = data_fim

    return text(sql), params






















###grafico Receita Bruta

def get_grafico_receita_bruta(filial=None,produto = None,categoria = None, data_inicio=None, data_fim=None):
    """
    Monta a query da receita liquida dinamicamente com base nos filtros.
    Se os filtros forem None, retorna o total geral.
    """
    sql = "SELECT periodo,SUM(faturamento_bruto) as total FROM comercial.vm_kpis_comercial_mensal WHERE 1=1 "
    params = {}

    if filial:
        sql += " AND nome_filial = :filial"
        params['filial'] = filial

    if produto:
        sql += " AND nome_produto = :produto"
        params['produto'] = produto

    if categoria:
        sql += " AND nome_categoria = :categoria"
        params['categoria'] = categoria
    
    if data_inicio and data_fim:
        sql += " AND periodo BETWEEN :inicio AND :fim"
        params['inicio'] = data_inicio
        params['fim'] = data_fim
    sql += " GROUP BY periodo ORDER BY periodo"
    

    return text(sql), params




def get_grafico_receita_liquida(filial=None,produto = None,categoria = None, data_inicio=None, data_fim=None):
    """
    Monta a query da receita liquida dinamicamente com base nos filtros.
    Se os filtros forem None, retorna o total geral.
    """
    sql = "SELECT periodo,SUM(receita_liquida) as total FROM comercial.vm_kpis_comercial_mensal WHERE 1=1 "
    params = {}

    if filial:
        sql += " AND nome_filial = :filial"
        params['filial'] = filial

    if produto:
        sql += " AND nome_produto = :produto"
        params['produto'] = produto

    if categoria:
        sql += " AND nome_categoria = :categoria"
        params['categoria'] = categoria
    
    if data_inicio and data_fim:
        sql += " AND periodo BETWEEN :inicio AND :fim"
        params['inicio'] = data_inicio
        params['fim'] = data_fim
    sql += " GROUP BY periodo ORDER BY periodo"
    

    return text(sql), params

#Grafico Margem Média

def get_grafico_margem_bruta_percentual(filial=None,produto = None,categoria = None, data_inicio=None, data_fim=None):
    """
    Monta a query do grafico margem media percentual a dinamicamente com base nos filtros.
    Se os filtros forem None, retorna o total geral.
    """
    sql = "SELECT periodo,AVG(margem_bruta_percentual) as total FROM comercial.vm_kpis_comercial_mensal WHERE 1=1 "
    params = {}

    if filial:
        sql += " AND nome_filial = :filial"
        params['filial'] = filial

    if produto:
        sql += " AND nome_produto = :produto"
        params['produto'] = produto

    if categoria:
        sql += " AND nome_categoria = :categoria"
        params['categoria'] = categoria
    
    if data_inicio and data_fim:
        sql += " AND periodo BETWEEN :inicio AND :fim"
        params['inicio'] = data_inicio
        params['fim'] = data_fim
    sql += " GROUP BY periodo ORDER BY periodo"
    

    return text(sql), params



    # Rota das Perguntas 

def pergunta_faturamento(filial=None,produto = None,categoria = None, data_inicio=None, data_fim=None):
    """
    Monta a query do grafico margem media percentual a dinamicamente com base nos filtros.
    Se os filtros forem None, retorna o total geral.
    """
    sql = " SELECT periodo,SUM(faturamento_bruto) as receita_bruta ," \
    "SUM(desconto_total) as desconto_total, SUM(receita_liquida) as receita_liquida ," \
    "SUM(quantidade_vendida) as quantidade_vendida, " \
    "SUM(quantidade_de_vendas) as quantidade_de_vendas  FROM comercial.vm_kpis_comercial_mensal WHERE 1=1"
    params = {}

    if filial:
        sql += " AND nome_filial = :filial"
        params['filial'] = filial

    if produto:
        sql += " AND nome_produto = :produto"
        params['produto'] = produto

    if categoria:
        sql += " AND nome_categoria = :categoria"
        params['categoria'] = categoria
    
    if data_inicio and data_fim:
        sql += " AND periodo BETWEEN :inicio AND :fim"
        params['inicio'] = data_inicio
        params['fim'] = data_fim
    sql += " GROUP BY periodo ORDER BY periodo"
    

    return text(sql), params

def pergunta_receita_liquida(filial=None,produto = None,categoria = None, data_inicio=None, data_fim=None):
    """
    Monta a query do grafico margem media percentual a dinamicamente com base nos filtros.
    Se os filtros forem None, retorna o total geral.
    """
    sql = " SELECT nome_filial as nome_filial,SUM(faturamento_bruto) as receita_bruta ," \
    "SUM(desconto_total) as desconto_total, SUM(receita_liquida) as receita_liquida ," \
    "SUM(custo_total) as custo_total," \
     "SUM(margem_bruta) as margem_bruta, AVG(margem_bruta_percentual) as margem_bruta_percentual" \
     " FROM comercial.vm_kpis_comercial_mensal WHERE 1=1"
    params = {}

    if filial:
        sql += " AND nome_filial = :filial"
        params['filial'] = filial

    if produto:
        sql += " AND nome_produto = :produto"
        params['produto'] = produto

    if categoria:
        sql += " AND nome_categoria = :categoria"
        params['categoria'] = categoria
    
    if data_inicio and data_fim:
        sql += " AND periodo BETWEEN :inicio AND :fim"
        params['inicio'] = data_inicio
        params['fim'] = data_fim
    sql += " GROUP BY nome_filial ORDER BY nome_filial"
    

    return text(sql), params





def pergunta_receita_liquida_por_categoria(filial=None,produto = None,categoria = None, data_inicio=None, data_fim=None):
    """
    Monta a query do grafico margem media percentual a dinamicamente com base nos filtros.
    Se os filtros forem None, retorna o total geral.
    """
    sql = " SELECT nome_categoria as categoria, SUM(quantidade_vendida) as quantidade_vendida ," \
    "SUM(faturamento_bruto) as receita_bruta, SUM(receita_liquida) as receita_liquida," \
     "SUM(margem_bruta) as margem_bruta, AVG(margem_bruta_percentual) as margem_bruta_percentual" \
     " FROM comercial.vm_kpis_comercial_mensal WHERE 1=1"
    params = {}

    if filial:
        sql += " AND nome_filial = :filial"
        params['filial'] = filial

    if produto:
        sql += " AND nome_produto = :produto"
        params['produto'] = produto

    if categoria:
        sql += " AND nome_categoria = :categoria"
        params['categoria'] = categoria
    
    if data_inicio and data_fim:
        sql += " AND periodo BETWEEN :inicio AND :fim"
        params['inicio'] = data_inicio
        params['fim'] = data_fim
    sql += " GROUP BY nome_categoria ORDER BY nome_categoria"
    

    return text(sql), params





def pergunta_produtos_vendidos(filial=None,produto = None,categoria = None, data_inicio=None, data_fim=None):
    """
    Monta a query do grafico margem media percentual a dinamicamente com base nos filtros.
    Se os filtros forem None, retorna o total geral.
    """
    sql = " SELECT nome_produto as nome_produto ,nome_categoria as categoria, SUM(quantidade_vendida) as quantidade_vendida ," \
    "SUM(faturamento_bruto) as receita_bruta, SUM(receita_liquida) as receita_liquida" \
     " FROM comercial.vm_kpis_comercial_mensal WHERE 1=1"
    params = {}

    if filial:
        sql += " AND nome_filial = :filial"
        params['filial'] = filial

    if produto:
        sql += " AND nome_produto = :produto"
        params['produto'] = produto

    if categoria:
        sql += " AND nome_categoria = :categoria"
        params['categoria'] = categoria
    
    if data_inicio and data_fim:
        sql += " AND periodo BETWEEN :inicio AND :fim"
        params['inicio'] = data_inicio
        params['fim'] = data_fim
    sql += " GROUP BY nome_produto,nome_categoria ORDER BY nome_produto"
    

    return text(sql), params





def pergunta_margem_bruta(filial=None,produto = None,categoria = None, data_inicio=None, data_fim=None):
    """
    Monta a query do grafico margem media percentual a dinamicamente com base nos filtros.
    Se os filtros forem None, retorna o total geral.
    """
    sql = " SELECT periodo as periodo, nome_filial as nome_filial,nome_categoria as categoria, SUM(quantidade_vendida) as quantidade_vendida ," \
    " SUM(receita_liquida) as receita_liquida,SUM(custo_total) as custo_total," \
    "SUM(margem_bruta) as margem_bruta, AVG(margem_bruta_percentual) as margem_bruta_percentual" \
     " FROM comercial.vm_kpis_comercial_mensal WHERE 1=1"
    params = {}

    if filial:
        sql += " AND nome_filial = :filial"
        params['filial'] = filial

    if produto:
        sql += " AND nome_produto = :produto"
        params['produto'] = produto

    if categoria:
        sql += " AND nome_categoria = :categoria"
        params['categoria'] = categoria
    
    if data_inicio and data_fim:
        sql += " AND periodo BETWEEN :inicio AND :fim"
        params['inicio'] = data_inicio
        params['fim'] = data_fim
    sql += " GROUP BY periodo, nome_filial, nome_categoria ORDER BY periodo"
    

    return text(sql), params




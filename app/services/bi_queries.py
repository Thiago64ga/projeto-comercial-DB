from sqlalchemy import text

from app.db import get_session 
from datetime import datetime
import re

PERFIS_VALIDOS = {"administrador", "gerente", "vendedor", "analista"}
STATUS_USUARIO_VALIDOS = {"Ativo", "Inativo"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

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
        "dbId": int(row.id_usuario),
        "name": row.nome,
        "email": row.email,
        "roleId": row.perfil,
        "status": row.status
    }

def validar_usuario(nome, email, senha, perfil, status="Ativo", exigir_senha=True):
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
            CHECK (perfil IN ('administrador', 'gerente', 'vendedor', 'analista')),
            CHECK (status IN ('Ativo', 'Inativo')),
            CHECK (LENGTH(nome) >= 3),
            CHECK (LENGTH(senha) >= 6)
        )
    """))

    total = session.execute(text("SELECT COUNT(*) FROM comercial.app_usuario")).scalar_one()
    if total == 0:
        session.execute(text("""
            INSERT INTO comercial.app_usuario (nome, email, senha, perfil, status) VALUES
            ('Marina Costa', 'admin@aurora.local', 'admin123', 'administrador', 'Ativo'),
            ('Rafael Lima', 'gerente@aurora.local', 'gerente123', 'gerente', 'Ativo'),
            ('Bianca Alves', 'vendedor@aurora.local', 'vendedor123', 'vendedor', 'Ativo'),
            ('Lucas Pereira', 'analista@aurora.local', 'analista123', 'analista', 'Ativo')
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

def criar_usuario(session, nome, email, senha, perfil, status="Ativo"):
    garantir_tabela_usuarios(session)
    nome = (nome or "").strip()
    email = (email or "").strip().lower()
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

    return normalizar_usuario(row)

def atualizar_status_usuario(session, user_id, status):
    garantir_tabela_usuarios(session)
    if status not in STATUS_USUARIO_VALIDOS:
        raise ValueError("Status invalido.")

    db_id = str(user_id or "").replace("u-", "")
    usuario_atual = session.execute(
        text("""
            SELECT perfil, status
            FROM comercial.app_usuario
            WHERE id_usuario = :id_usuario
        """),
        {"id_usuario": db_id}
    ).fetchone()

    if not usuario_atual:
        raise ValueError("Usuario nao encontrado.")

    if usuario_atual.perfil == "administrador" and usuario_atual.status == "Ativo" and status == "Inativo":
        admins_ativos = session.execute(text("""
            SELECT COUNT(*)
            FROM comercial.app_usuario
            WHERE perfil = 'administrador'
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

    return normalizar_usuario(row)

def remover_usuario(session, user_id):
    garantir_tabela_usuarios(session)
    db_id = str(user_id or "").replace("u-", "")
    usuario_atual = session.execute(
        text("""
            SELECT perfil, status
            FROM comercial.app_usuario
            WHERE id_usuario = :id_usuario
        """),
        {"id_usuario": db_id}
    ).fetchone()

    if not usuario_atual:
        raise ValueError("Usuario nao encontrado.")

    if usuario_atual.perfil == "administrador" and usuario_atual.status == "Ativo":
        admins_ativos = session.execute(text("""
            SELECT COUNT(*)
            FROM comercial.app_usuario
            WHERE perfil = 'administrador'
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

def criar_venda(session, cliente, produto, filial, quantidade, desconto, data_venda):
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

    quantidade = int(quantidade)
    desconto = float(desconto or 0)
    valor_bruto = float(produto_row.preco_venda) * quantidade
    desconto = min(max(desconto, 0), valor_bruto)
    valor_liquido = valor_bruto - desconto
    custo_total = float(produto_row.custo_produto) * quantidade
    numero_pedido = f"PED-APP-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

    id_data = session.execute(
        text("""
            INSERT INTO comercial.dim_calendario (
                data_completa,
                ano,
                mes,
                nome_mes,
                trimestre,
                semestre
            )
            VALUES (
                CAST(:data_venda AS DATE),
                EXTRACT(YEAR FROM CAST(:data_venda AS DATE))::INT,
                EXTRACT(MONTH FROM CAST(:data_venda AS DATE))::INT,
                TO_CHAR(CAST(:data_venda AS DATE), 'TMMonth'),
                EXTRACT(QUARTER FROM CAST(:data_venda AS DATE))::INT,
                CASE WHEN EXTRACT(MONTH FROM CAST(:data_venda AS DATE)) <= 6 THEN 1 ELSE 2 END
            )
            ON CONFLICT (data_completa)
            DO UPDATE SET data_completa = EXCLUDED.data_completa
            RETURNING id_data
        """),
        {"data_venda": data_venda}
    ).scalar_one()

    id_venda = session.execute(
        text("""
            INSERT INTO comercial.fato_vendas (
                id_data,
                id_filial,
                id_cliente,
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

    session.execute(text("REFRESH MATERIALIZED VIEW comercial.vm_kpis_comercial_mensal"))

    return {
        "id_venda": int(id_venda),
        "numero_pedido": numero_pedido,
        "valor_bruto": valor_bruto,
        "desconto": desconto,
        "valor_liquido": valor_liquido,
    }

def get_categorias():
    """Retorna a Query da lista de Categorias"""

    sql = """
                SELECT nome_categoria
                FROM comercial.vm_kpis_comercial_mensal
                GROUP BY nome_categoria
                Order BY nome_categoria
                """
    return text(sql)



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




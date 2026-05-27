from functools import wraps
from datetime import date, datetime
from decimal import Decimal

from flask import render_template, jsonify, request, redirect, session, url_for
from app.db import get_session
from app.services import bi_queries
from sqlalchemy import text 

ROLE_PERMISSIONS = {
    "admin_comercial": {
        "usuarios:gerenciar", "usuarios:criar", "usuarios:editar", "usuarios:remover",
        "vendas:criar", "dados:ver", "dados:criar", "permissoes:ver"
    },
    "gerente_comercial": {"dados:ver"},
    "operador_comercial": {"dados:ver", "dados:criar", "vendas:criar"},
    "leitura_comercial": {"dados:ver"},
}



def init_routes(app):
    def usuario_logado():
        return session.get("usuario")

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not usuario_logado():
                return redirect(url_for("login"))
            return view(*args, **kwargs)
        return wrapped

    def api_login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not usuario_logado():
                return jsonify({"erro": "Sessao expirada. Faca login novamente."}), 401
            return view(*args, **kwargs)
        return wrapped

    def tem_permissao(permissao):
        usuario = usuario_logado() or {}
        return permissao in ROLE_PERMISSIONS.get(usuario.get("roleId"), set())

    def exigir_permissao(permissao):
        if tem_permissao(permissao):
            return None
        return jsonify({"erro": "Acesso negado para este perfil."}), 403

    def resposta_erro_banco(error):
        sqlstate = getattr(getattr(error, "orig", None), "sqlstate", "")
        if sqlstate == "42703":
            return jsonify({
                "erro": "Coluna inexistente no banco de dados. Execute db/fixes/001_add_coluna_ativo.sql ou recrie o banco com db/init/cria_banco.sql.",
                "status": "db_schema_error"
            }), 500
        if sqlstate == "42P01":
            return jsonify({
                "erro": "Tabela inexistente no banco de dados. Execute o script de criacao do banco.",
                "status": "db_schema_error"
            }), 500
        return jsonify({"erro": str(error)}), 500

    def api_success(data=None, message="Operacao realizada com sucesso.", status=200):
        return jsonify({"success": True, "message": message, "data": json_ready(data if data is not None else {})}), status

    def api_error(message="Erro ao realizar operacao.", error=None, status=400):
        return jsonify({"success": False, "message": message, "error": str(error or message)}), status

    def json_ready(value):
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        if isinstance(value, list):
            return [json_ready(item) for item in value]
        if isinstance(value, tuple):
            return [json_ready(item) for item in value]
        if isinstance(value, dict):
            return {key: json_ready(item) for key, item in value.items()}
        return value

    def executar_api(operacao, mensagem_sucesso="Operacao realizada com sucesso.", status_sucesso=200):
        db_session = get_session()
        try:
            data = operacao(db_session)
            db_session.commit()
            return api_success(data, mensagem_sucesso, status_sucesso)
        except ValueError as e:
            db_session.rollback()
            return api_error("Erro de validacao.", e, 400)
        except Exception as e:
            db_session.rollback()
            sqlstate = getattr(getattr(e, "orig", None), "sqlstate", "")
            if sqlstate in {"23505"}:
                return api_error("Registro duplicado.", e, 409)
            if sqlstate in {"42703", "42P01"}:
                return api_error("Erro de estrutura do banco de dados.", e, 500)
            return api_error("Erro ao realizar operacao.", e, 500)
        finally:
            db_session.close()

    
    @app.route("/login")
    def login():
        if usuario_logado():
            return redirect(url_for("index"))
        return render_template("login.html")


    @app.route("/")
    @login_required
    def index():

        banco_online = True

        session = get_session()

        try:

            session.execute(text("SELECT 1"))

        except Exception:

            banco_online = False

        finally:

            session.close()

        return render_template(
            "base.html",
            banco_online=banco_online,
            usuario=usuario_logado()
        )


    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))


    @app.route("/auth/me")
    @api_login_required
    def usuario_atual():
        return jsonify(usuario_logado())


    @app.route("/api/usuarios", methods=["GET"])
    @api_login_required
    def api_listar_usuarios():
        return executar_api(lambda s: bi_queries.get_usuarios(s), "Usuarios carregados com sucesso.")


    @app.route("/api/usuarios", methods=["POST"])
    @api_login_required
    def api_criar_usuario():
        dados = request.get_json(silent=True) or {}
        return executar_api(
            lambda s: bi_queries.criar_usuario(
                s,
                nome=dados.get("nome") or dados.get("name"),
                email=dados.get("email"),
                senha=dados.get("senha") or dados.get("password") or dados.get("senha_hash"),
                perfil=dados.get("perfil") or dados.get("roleId"),
                status=dados.get("status") or ("Ativo" if dados.get("ativo", True) else "Inativo")
            ),
            "Usuario cadastrado com sucesso.",
            201
        )


    @app.route("/api/usuarios/<user_id>", methods=["GET"])
    @api_login_required
    def api_obter_usuario(user_id):
        return executar_api(lambda s: bi_queries.obter_usuario(s, user_id), "Usuario carregado com sucesso.")


    @app.route("/api/usuarios/<user_id>", methods=["PUT"])
    @api_login_required
    def api_atualizar_usuario(user_id):
        dados = request.get_json(silent=True) or {}
        return executar_api(lambda s: bi_queries.atualizar_usuario(s, user_id, dados), "Usuario atualizado com sucesso.")


    @app.route("/api/usuarios/<user_id>", methods=["DELETE"])
    @api_login_required
    def api_remover_usuario(user_id):
        return executar_api(lambda s: bi_queries.remover_usuario(s, user_id) or {"id": user_id}, "Usuario removido com sucesso.")


    @app.route("/api/produtos", methods=["GET"])
    @api_login_required
    def api_listar_produtos():
        return executar_api(lambda s: bi_queries.listar_produtos_api(s), "Produtos carregados com sucesso.")


    @app.route("/api/produtos", methods=["POST"])
    @api_login_required
    def api_criar_produto():
        dados = request.get_json(silent=True) or {}
        return executar_api(
            lambda s: bi_queries.criar_produto(
                s,
                nome=dados.get("produto") or dados.get("nome"),
                categoria=dados.get("categoria"),
                marca=dados.get("marca"),
                preco=dados.get("preco"),
                custo=dados.get("custo"),
                status=dados.get("status", "ATIVO")
            ),
            "Produto cadastrado com sucesso.",
            201
        )


    @app.route("/api/produtos/<int:id_produto>", methods=["PUT"])
    @api_login_required
    def api_atualizar_produto(id_produto):
        dados = request.get_json(silent=True) or {}
        return executar_api(lambda s: bi_queries.atualizar_produto(s, id_produto, dados), "Produto atualizado com sucesso.")


    @app.route("/api/produtos/<int:id_produto>", methods=["DELETE"])
    @api_login_required
    def api_remover_produto(id_produto):
        return executar_api(lambda s: bi_queries.remover_produto(s, id_produto) or {"id": id_produto}, "Produto removido com sucesso.")


    @app.route("/api/filiais", methods=["GET"])
    @api_login_required
    def api_listar_filiais():
        return executar_api(lambda s: bi_queries.listar_filiais_api(s), "Filiais carregadas com sucesso.")


    @app.route("/api/clientes", methods=["GET"])
    @api_login_required
    def api_listar_clientes():
        return executar_api(lambda s: bi_queries.listar_clientes_api(s), "Clientes carregados com sucesso.")


    @app.route("/api/filiais", methods=["POST"])
    @api_login_required
    def api_criar_filial():
        dados = request.get_json(silent=True) or {}
        return executar_api(
            lambda s: bi_queries.criar_filial(
                s,
                nome=dados.get("nome") or dados.get("nome_filial"),
                cidade=dados.get("cidade"),
                uf=dados.get("uf"),
                regiao=dados.get("regiao"),
                porte=dados.get("porte")
            ),
            "Filial cadastrada com sucesso.",
            201
        )


    @app.route("/api/categorias", methods=["GET"])
    @api_login_required
    def api_listar_categorias():
        return executar_api(lambda s: bi_queries.listar_categorias_api(s), "Categorias carregadas com sucesso.")


    @app.route("/api/canais", methods=["GET"])
    @api_login_required
    def api_listar_canais():
        return executar_api(lambda s: bi_queries.listar_canais_api(s), "Canais carregados com sucesso.")


    @app.route("/api/categorias", methods=["POST"])
    @api_login_required
    def api_criar_categoria():
        dados = request.get_json(silent=True) or {}
        return executar_api(
            lambda s: bi_queries.criar_categoria(s, dados.get("nome") or dados.get("categoria"), dados.get("descricao")),
            "Categoria cadastrada com sucesso.",
            201
        )


    @app.route("/api/vendas", methods=["GET"])
    @api_login_required
    def api_listar_vendas():
        return executar_api(lambda s: bi_queries.get_vendas_recentes(s, request.args.get("limite", 50)), "Vendas carregadas com sucesso.")


    @app.route("/api/vendas", methods=["POST"])
    @api_login_required
    def api_criar_venda():
        dados = request.get_json(silent=True) or {}
        return executar_api(
            lambda s: bi_queries.criar_venda_api(s, dados, usuario_logado().get("dbId")),
            "Venda registrada com sucesso.",
            201
        )


    @app.route("/api/dashboard/resumo", methods=["GET"])
    @api_login_required
    def api_dashboard_resumo():
        def op(s):
            return {
                "receitaLiquida": s.execute(bi_queries.get_receitaLiquida()[0], {}).scalar() or 0,
                "custoTotal": s.execute(bi_queries.get_custo_total()[0], {}).scalar() or 0,
                "subqueries": bi_queries.get_resumo_subqueries(s)
            }
        return executar_api(op, "Resumo carregado com sucesso.")


    @app.route("/api/dashboard/vendas-mes", methods=["GET"])
    @api_login_required
    def api_dashboard_vendas_mes():
        return executar_api(lambda s: [dict(row._mapping) for row in s.execute(bi_queries.pergunta_faturamento()[0], {})], "Vendas por mes carregadas com sucesso.")


    @app.route("/api/dashboard/produtos-ranking", methods=["GET"])
    @api_login_required
    def api_dashboard_produtos_ranking():
        return executar_api(lambda s: [dict(row._mapping) for row in s.execute(text("SELECT * FROM comercial.fn_ranking_produtos(10)"))], "Ranking de produtos carregado com sucesso.")


    @app.route("/api/dashboard/filiais", methods=["GET"])
    @api_login_required
    def api_dashboard_filiais():
        return executar_api(lambda s: [dict(row._mapping) for row in s.execute(bi_queries.pergunta_receita_liquida()[0], {})], "Filiais carregadas com sucesso.")


    @app.route("/api/banco/rotinas", methods=["GET"])
    @api_login_required
    def api_rotinas_banco():
        return executar_api(lambda s: bi_queries.get_rotinas_banco(s), "Rotinas do banco carregadas com sucesso.")


    @app.route("/api/banco/rotinas/executar-demo", methods=["POST"])
    @api_login_required
    def api_executar_demo_rotinas_banco():
        return executar_api(
            lambda s: bi_queries.executar_demo_rotinas_banco(s),
            "Procedures e functions executadas com sucesso."
        )


 









    @app.route("/filiais")
    @api_login_required
    def filiais():
        session = get_session()
        try:
            # Puxa a query do seu arquivo de serviços
            query = bi_queries.get_filiais() 
            result = session.execute(query)
            
            # Cria uma lista simples de strings: ["Barbacena", "Prata", ...]
            lista_filiais = [row.nome_filial for row in result]
            
            return jsonify(lista_filiais)
        
        except Exception as e:
            return jsonify({"erro": str(e)}), 500
        finally:
            session.close()


    @app.route("/produtos")
    @api_login_required
    def produtos():
        session = get_session()
        categoria = request.args.get("categoria")
        try:
            query = bi_queries.get_produtos(categoria)
            result = session.execute(
                query,
                {"categoria": categoria}
                )

            lista_produtos = [row.nome_produto for row in result]

            return jsonify(lista_produtos)
        except Exception as e:
            return jsonify({"erro": str(e)}),500
        finally:
            session.close()


    @app.route("/produtos", methods=["POST"])
    @api_login_required
    def criar_produto():
        bloqueio = exigir_permissao("dados:criar")
        if bloqueio:
            return bloqueio
        session = get_session()
        dados = request.get_json(silent=True) or {}

        try:
            produto = bi_queries.criar_produto(
                session,
                nome=dados.get("produto"),
                categoria=dados.get("categoria"),
                marca=dados.get("marca"),
                preco=dados.get("preco"),
                custo=dados.get("custo"),
                status=dados.get("status", "ATIVO")
            )
            session.commit()
            return jsonify(produto), 201
        except ValueError as e:
            session.rollback()
            return jsonify({"erro": str(e)}), 400
        except Exception as e:
            session.rollback()
            return jsonify({"erro": str(e)}), 500
        finally:
            session.close()


    @app.route("/produtos_detalhados")
    @api_login_required
    def produtos_detalhados():
        session = get_session()
        categoria = request.args.get("categoria")
        try:
            query, params = bi_queries.get_produtos_detalhados(categoria)
            result = session.execute(query, params)

            lista_produtos = [
                {
                    "produto": row.produto,
                    "id": int(row.id),
                    "categoria": row.categoria,
                    "marca": row.marca,
                    "preco": float(row.preco or 0),
                    "status": row.status,
                    "vendidos": int(row.vendidos or 0),
                    "receita": float(row.receita or 0)
                }
                for row in result
            ]

            return jsonify(lista_produtos)
        except Exception as e:
            return jsonify({"erro": str(e)}), 500
        finally:
            session.close()


    @app.route("/clientes")
    @api_login_required
    def clientes():
        session = get_session()
        try:
            query = bi_queries.get_clientes()
            result = session.execute(query)

            lista_clientes = [
                {
                    "nome": row.nome,
                    "id": int(row.id),
                    "tipo": row.tipo,
                    "cidade": row.cidade,
                    "uf": row.uf,
                    "cadastro": row.cadastro.isoformat() if row.cadastro else None
                }
                for row in result
            ]

            return jsonify(lista_clientes)
        except Exception as e:
            return jsonify({"erro": str(e)}), 500
        finally:
            session.close()


    @app.route("/clientes", methods=["POST"])
    @api_login_required
    def criar_cliente():
        bloqueio = exigir_permissao("dados:criar")
        if bloqueio:
            return bloqueio
        session = get_session()
        dados = request.get_json(silent=True) or {}

        try:
            cliente = bi_queries.criar_cliente(
                session,
                nome=dados.get("nome"),
                tipo=dados.get("tipo"),
                cidade=dados.get("cidade"),
                uf=dados.get("uf"),
                data_cadastro=dados.get("cadastro")
            )
            session.commit()
            return jsonify(cliente), 201
        except ValueError as e:
            session.rollback()
            return jsonify({"erro": str(e)}), 400
        except Exception as e:
            session.rollback()
            return jsonify({"erro": str(e)}), 500
        finally:
            session.close()


    @app.route("/usuarios", methods=["GET"])
    @api_login_required
    def listar_usuarios():
        bloqueio = exigir_permissao("usuarios:gerenciar")
        if bloqueio:
            return bloqueio
        session = get_session()
        try:
            usuarios = bi_queries.get_usuarios(session)
            session.commit()
            return jsonify(usuarios)
        except Exception as e:
            session.rollback()
            return jsonify({"erro": str(e)}), 500
        finally:
            session.close()


    @app.route("/auth/login", methods=["POST"])
    def autenticar_usuario():
        db_session = get_session()
        dados = request.get_json(silent=True) or request.form

        try:
            usuario = bi_queries.autenticar_usuario_por_email(
                db_session,
                dados.get("email"),
                dados.get("password")
            )
            db_session.commit()
            session.clear()
            session["usuario"] = usuario
            if request.is_json:
                return jsonify(usuario)
            return redirect(url_for("index"))
        except ValueError as e:
            db_session.rollback()
            if request.is_json:
                return jsonify({"erro": str(e)}), 401
            return render_template("login.html", erro=str(e), email=dados.get("email", "")), 401
        except Exception as e:
            db_session.rollback()
            if request.is_json:
                return jsonify({"erro": str(e)}), 500
            return render_template("login.html", erro=str(e), email=dados.get("email", "")), 500
        finally:
            db_session.close()


    @app.route("/auth/login-perfil", methods=["POST"])
    @api_login_required
    def autenticar_usuario_por_id():
        db_session = get_session()
        dados = request.get_json(silent=True) or {}

        try:
            usuario = bi_queries.autenticar_usuario(
                db_session,
                dados.get("id"),
                dados.get("password")
            )
            session["usuario"] = usuario
            return jsonify(usuario)
        except ValueError as e:
            return jsonify({"erro": str(e)}), 401
        except Exception as e:
            return jsonify({"erro": str(e)}), 500
        finally:
            db_session.close()


    @app.route("/usuarios", methods=["POST"])
    @api_login_required
    def criar_usuario():
        bloqueio = exigir_permissao("usuarios:criar")
        if bloqueio:
            return bloqueio
        session = get_session()
        dados = request.get_json(silent=True) or {}

        try:
            usuario = bi_queries.criar_usuario(
                session,
                nome=dados.get("name"),
                email=dados.get("email"),
                senha=dados.get("password"),
                perfil=dados.get("roleId"),
                status=dados.get("status", "Ativo")
            )
            session.commit()
            return jsonify(usuario), 201
        except ValueError as e:
            session.rollback()
            return jsonify({"erro": str(e)}), 400
        except Exception as e:
            session.rollback()
            return jsonify({"erro": str(e)}), 500
        finally:
            session.close()


    @app.route("/usuarios/<user_id>/status", methods=["PATCH"])
    @api_login_required
    def atualizar_status_usuario(user_id):
        bloqueio = exigir_permissao("usuarios:editar")
        if bloqueio:
            return bloqueio
        session = get_session()
        dados = request.get_json(silent=True) or {}

        try:
            usuario = bi_queries.atualizar_status_usuario(
                session,
                user_id,
                dados.get("status")
            )
            session.commit()
            return jsonify(usuario)
        except ValueError as e:
            session.rollback()
            return jsonify({"erro": str(e)}), 400
        except Exception as e:
            session.rollback()
            return jsonify({"erro": str(e)}), 500
        finally:
            session.close()


    @app.route("/usuarios/<user_id>", methods=["DELETE"])
    @api_login_required
    def remover_usuario(user_id):
        bloqueio = exigir_permissao("usuarios:remover")
        if bloqueio:
            return bloqueio
        session = get_session()

        try:
            bi_queries.remover_usuario(session, user_id)
            session.commit()
            return jsonify({"ok": True})
        except ValueError as e:
            session.rollback()
            return jsonify({"erro": str(e)}), 404
        except Exception as e:
            session.rollback()
            return jsonify({"erro": str(e)}), 500
        finally:
            session.close()


    @app.route("/vendas", methods=["POST"])
    @api_login_required
    def criar_venda():
        bloqueio = exigir_permissao("vendas:criar")
        if bloqueio:
            return bloqueio
        session = get_session()
        dados = request.get_json(silent=True) or {}
        campos_obrigatorios = ["cliente", "produto", "filial", "quantidade", "data"]

        if any(not dados.get(campo) for campo in campos_obrigatorios):
            session.close()
            return jsonify({"erro": "Informe cliente, produto, filial, quantidade e data."}), 400

        try:
            venda = bi_queries.criar_venda(
                session=session,
                cliente=dados.get("cliente"),
                produto=dados.get("produto"),
                filial=dados.get("filial"),
                quantidade=dados.get("quantidade"),
                desconto=dados.get("desconto"),
                data_venda=dados.get("data"),
                usuario_id=usuario_logado().get("dbId"),
                canal=dados.get("canal", "Loja Fisica")
            )
            session.commit()
            return jsonify(venda), 201
        except ValueError as e:
            session.rollback()
            return jsonify({"erro": str(e)}), 400
        except Exception as e:
            session.rollback()
            return jsonify({"erro": str(e)}), 500
        finally:
            session.close()


    @app.route("/vendas", methods=["GET"])
    @api_login_required
    def listar_vendas():
        session = get_session()
        try:
            vendas = bi_queries.get_vendas_recentes(
                session,
                limite=request.args.get("limite", 50)
            )
            session.commit()
            return jsonify(vendas)
        except Exception as e:
            session.rollback()
            return jsonify({"erro": str(e)}), 500
        finally:
            session.close()


    @app.route("/canais")
    @api_login_required
    def canais():
        session = get_session()
        try:
            return jsonify(bi_queries.get_canais(session))
        except Exception as e:
            return resposta_erro_banco(e)
        finally:
            session.close()


    @app.route("/resumo_subqueries")
    @api_login_required
    def resumo_subqueries():
        session = get_session()
        try:
            return jsonify(bi_queries.get_resumo_subqueries(session))
        except Exception as e:
            return resposta_erro_banco(e)
        finally:
            session.close()
        

    @app.route("/categorias")
    @api_login_required
    def categorias():
        session = get_session()
        try:
            query = bi_queries.get_categorias()
            result = session.execute(query)

            lista_categorias = [row.nome_categoria for row in result]
            return jsonify(lista_categorias)
        except Exception as e:
            return jsonify({"erro": str(e)}),500
        finally:
            session.close()

    @app.route("/faturamento", methods=["GET"])
    @api_login_required
    def get_faturamento():
        """Retorna o valor do faturamento formatado com 2 casas decimais."""
        session = get_session()
        
        # Captura os parâmetros da URL
        filial = request.args.get('filial')
        produto = request.args.get('produto')
        categoria = request.args.get('categoria')
        inicio = request.args.get('inicio')
        fim = request.args.get('fim')
        

        try:
            query, params = bi_queries.get_faturamento(filial,produto,categoria, inicio, fim)
            result = session.execute(query, params).fetchone()

            # Tratamento para não retornar erro se o banco estiver vazio
            valor_bruto = result[0] if result and result[0] is not None else 0.0
            
            # Força o formato "0.00"
            valor_formatado = "{:.2f}".format(float(valor_bruto))
            
            return jsonify(valor_formatado)
        except Exception as e:
            return jsonify({"erro": str(e)}), 500
        finally:
            session.close()


    @app.route("/receita_liquida", methods=["GET"])
    @api_login_required
    def get_receita_liquida():
        """Retorna o valor do faturamento formatado com 2 casas decimais."""
        session = get_session()
        
        # Captura os parâmetros da URL
        filial = request.args.get('filial')
        produto = request.args.get('produto')
        categoria = request.args.get('categoria')
        inicio = request.args.get('inicio')
        fim = request.args.get('fim')
        

        try:
            query, params = bi_queries.get_receitaLiquida(filial,produto,categoria, inicio, fim)
            result = session.execute(query, params).fetchone()

            # Tratamento para não retornar erro se o banco estiver vazio
            valor_bruto = result[0] if result and result[0] is not None else 0.0
            
            # Força o formato "0.00"
            valor_formatado = "{:.2f}".format(float(valor_bruto))
            
            return jsonify(valor_formatado)
        except Exception as e:
            return jsonify({"erro": str(e)}), 500
        finally:
            session.close()




    @app.route("/margem_bruta", methods=["GET"])
    @api_login_required
    def get_margem_bruta():
        """Retorna o valor do faturamento formatado com 2 casas decimais."""
        session = get_session()
        
        # Captura os parâmetros da URL
        filial = request.args.get('filial')
        produto = request.args.get('produto')
        categoria = request.args.get('categoria')
        inicio = request.args.get('inicio')
        fim = request.args.get('fim')
        

        try:
            query, params = bi_queries.get_margem_bruta(filial,produto,categoria, inicio, fim)
            result = session.execute(query, params).fetchone()

            # Tratamento para não retornar erro se o banco estiver vazio
            valor_bruto = result[0] if result and result[0] is not None else 0.0
            
            # Força o formato "0.00"
            valor_formatado = "{:.2f}".format(float(valor_bruto))
            
            return jsonify(valor_formatado)
        except Exception as e:
            return jsonify({"erro": str(e)}), 500
        finally:
            session.close()




    @app.route("/margem_bruta_percentual", methods=["GET"])
    @api_login_required
    def get_margem_bruta_percentual():
        """Retorna o valor do faturamento formatado com 2 casas decimais."""
        session = get_session()
        
        # Captura os parâmetros da URL
        filial = request.args.get('filial')
        produto = request.args.get('produto')
        categoria = request.args.get('categoria')
        inicio = request.args.get('inicio')
        fim = request.args.get('fim')
        

        try:
            query, params = bi_queries.get_margem_bruta_percentual(filial,produto,categoria, inicio, fim)
            result = session.execute(query, params).fetchone()

            # Tratamento para não retornar erro se o banco estiver vazio
            valor_bruto = result[0] if result and result[0] is not None else 0.0
            
            # Força o formato "0.00"
            valor_formatado = "{:.2f}".format(float(valor_bruto))
            
            return jsonify(valor_formatado)
        except Exception as e:
            return jsonify({"erro": str(e)}), 500
        finally:
            session.close()



    ## Rotas de GRaficos 
    ##Graficos Receita Bruta

    @app.route("/grafico_receita_bruta", methods=["GET"])
    @api_login_required
    def get_grafico_receita_bruta():
        """Retorna o valor do faturamento formatado com 2 casas decimais."""
        session = get_session()
        
        # Captura os parâmetros da URL
        filial = request.args.get('filial')
        produto = request.args.get('produto')
        categoria = request.args.get('categoria')
        inicio = request.args.get('inicio')
        fim = request.args.get('fim')
        

        try:
            query, params = bi_queries.get_grafico_receita_bruta(filial,produto,categoria, inicio, fim)
            result = session.execute(query, params).fetchall()

            dados = [
                {
                    "periodo": str(row.periodo),
                    "total": float(row.total)
                }
                for row in result
            ]

            return jsonify(dados)
        except Exception as e:
            return jsonify({"erro": str(e)}), 500
        finally:
            session.close()





    @app.route("/grafico_receita_liquida", methods=["GET"])
    @api_login_required
    def get_grafico_receita_liquida():
        """Retorna o valor do faturamento formatado com 2 casas decimais."""
        session = get_session()
        
        # Captura os parâmetros da URL
        filial = request.args.get('filial')
        produto = request.args.get('produto')
        categoria = request.args.get('categoria')
        inicio = request.args.get('inicio')
        fim = request.args.get('fim')
        

        try:
            query, params = bi_queries.get_grafico_receita_liquida(filial,produto,categoria, inicio, fim)
            result = session.execute(query, params).fetchall()

            dados = [
                {
                    "periodo": str(row.periodo),
                    "total": float(row.total)
                }
                for row in result
            ]

            return jsonify(dados)
        except Exception as e:
            return jsonify({"erro": str(e)}), 500
        finally:
            session.close()




    @app.route("/grafico_margem_bruta_percentual", methods=["GET"])
    @api_login_required
    def get_grafico_margem_bruta_percebtual():
        """Retorna o valor do faturamento formatado com 2 casas decimais."""
        session = get_session()
        
        # Captura os parâmetros da URL
        filial = request.args.get('filial')
        produto = request.args.get('produto')
        categoria = request.args.get('categoria')
        inicio = request.args.get('inicio')
        fim = request.args.get('fim')
        

        try:
            query, params = bi_queries.get_grafico_margem_bruta_percentual(filial,produto,categoria, inicio, fim)
            result = session.execute(query, params).fetchall()

            dados = [
                {
                    "periodo": str(row.periodo),
                    "total": round(float(row.total), 1)
                }
                for row in result
            ]

            return jsonify(dados)
        except Exception as e:
            return jsonify({"erro": str(e)}), 500
        finally:
            session.close()



    @app.route("/custo_total", methods=["GET"])
    @api_login_required
    def get_custo_total():
        """Retorna o valor do faturamento formatado com 2 casas decimais."""
        session = get_session()
        
        # Captura os parâmetros da URL
        filial = request.args.get('filial')
        produto = request.args.get('produto')
        categoria = request.args.get('categoria')
        inicio = request.args.get('inicio')
        fim = request.args.get('fim')
        

        try:
            query, params = bi_queries.get_custo_total(filial,produto,categoria, inicio, fim)
            result = session.execute(query, params).fetchone()

            # Tratamento para não retornar erro se o banco estiver vazio
            valor_bruto = result[0] if result and result[0] is not None else 0.0
            
            # Força o formato "0.00"
            valor_formatado = "{:.2f}".format(float(valor_bruto))
            
            return jsonify(valor_formatado)
        except Exception as e:
            return jsonify({"erro": str(e)}), 500
        finally:
            session.close()



  # =========================
# ROTAS DAS PERGUNTAS
# =========================

    @app.route("/pergunta_faturamento", methods=["GET"])
    @api_login_required
    def get_pergunta_faturamento():

        session = get_session()

        filial = request.args.get('filial')
        produto = request.args.get('produto')
        categoria = request.args.get('categoria')
        inicio = request.args.get('inicio')
        fim = request.args.get('fim')

        try:

            query, params = bi_queries.pergunta_faturamento(
                filial,
                produto,
                categoria,
                inicio,
                fim
            )

            result = session.execute(query, params).fetchall()

            dados = [
                {
                    "periodo": str(row.periodo),
                    "receita_bruta": float(row.receita_bruta or 0),
                    "desconto_total": float(row.desconto_total or 0),
                    "receita_liquida": float(row.receita_liquida or 0),
                    "quantidade_vendida": int(row.quantidade_vendida or 0),
                    "quantidade_de_vendas": int(row.quantidade_de_vendas or 0)
                }
                for row in result
            ]

            return jsonify(dados)

        except Exception as e:

            return jsonify({"erro": str(e)}), 500

        finally:

            session.close()


    @app.route("/pergunta_receita_liquida", methods=["GET"])
    @api_login_required
    def get_pergunta_receita_liquida():

        session = get_session()

        filial = request.args.get('filial')
        produto = request.args.get('produto')
        categoria = request.args.get('categoria')
        inicio = request.args.get('inicio')
        fim = request.args.get('fim')

        try:

            query, params = bi_queries.pergunta_receita_liquida(
                filial,
                produto,
                categoria,
                inicio,
                fim
            )

            result = session.execute(query, params).fetchall()

            dados = [
                {
                    "filial": row.nome_filial,
                    "receita_bruta": float(row.receita_bruta or 0),
                    "desconto_total": float(row.desconto_total or 0),
                    "receita_liquida": float(row.receita_liquida or 0),
                    "custo_total": float(row.custo_total or 0),
                    "margem_bruta": float(row.margem_bruta or 0),
                    "margem_bruta_percentual": float(row.margem_bruta_percentual or 0)
                }
                for row in result
            ]

            return jsonify(dados)

        except Exception as e:

            return jsonify({"erro": str(e)}), 500

        finally:

            session.close()


    @app.route("/pergunta_receita_liquida_categoria", methods=["GET"])
    @api_login_required
    def get_pergunta_receita_liquida_categoria():

        session = get_session()

        filial = request.args.get('filial')
        produto = request.args.get('produto')
        categoria = request.args.get('categoria')
        inicio = request.args.get('inicio')
        fim = request.args.get('fim')

        try:

            query, params = bi_queries.pergunta_receita_liquida_por_categoria(
                filial,
                produto,
                categoria,
                inicio,
                fim
            )

            result = session.execute(query, params).fetchall()

            dados = [
                {
                    "categoria": row.categoria,
                    "quantidade_vendida": int(row.quantidade_vendida or 0),
                    "receita_bruta": float(row.receita_bruta or 0),
                    "receita_liquida": float(row.receita_liquida or 0),
                    "margem_bruta": float(row.margem_bruta or 0),
                    "margem_bruta_percentual": float(row.margem_bruta_percentual or 0)
                }
                for row in result
            ]

            return jsonify(dados)

        except Exception as e:

            return jsonify({"erro": str(e)}), 500

        finally:

            session.close()


    @app.route("/pergunta_produtos_vendidos", methods=["GET"])
    @api_login_required
    def get_pergunta_produtos_vendidos():

        session = get_session()

        filial = request.args.get('filial')
        produto = request.args.get('produto')
        categoria = request.args.get('categoria')
        inicio = request.args.get('inicio')
        fim = request.args.get('fim')

        try:

            query, params = bi_queries.pergunta_produtos_vendidos(
                filial,
                produto,
                categoria,
                inicio,
                fim
            )

            result = session.execute(query, params).fetchall()

            dados = [
                {
                    "produto": row.nome_produto,
                    "categoria": row.categoria,
                    "quantidade_vendida": int(row.quantidade_vendida or 0),
                    "receita_bruta": float(row.receita_bruta or 0),
                    "receita_liquida": float(row.receita_liquida or 0)
                }
                for row in result
            ]

            return jsonify(dados)

        except Exception as e:

            return jsonify({"erro": str(e)}), 500

        finally:

            session.close()


    @app.route("/pergunta_margem_bruta", methods=["GET"])
    @api_login_required
    def get_pergunta_margem_bruta():

        session = get_session()

        filial = request.args.get('filial')
        produto = request.args.get('produto')
        categoria = request.args.get('categoria')
        inicio = request.args.get('inicio')
        fim = request.args.get('fim')

        try:

            query, params = bi_queries.pergunta_margem_bruta(
                filial,
                produto,
                categoria,
                inicio,
                fim
            )

            result = session.execute(query, params).fetchall()

            dados = [
                {
                    "periodo": str(row.periodo),
                    "filial": row.nome_filial,
                    "categoria": row.categoria,
                    "receita_liquida": float(row.receita_liquida or 0),
                    "custo_total": float(row.custo_total or 0),
                    "margem_bruta": float(row.margem_bruta or 0),
                    "margem_bruta_percentual": float(row.margem_bruta_percentual or 0)
                }
                for row in result
            ]

            return jsonify(dados)

        except Exception as e:

            return jsonify({"erro": str(e)}), 500

        finally:

            session.close()

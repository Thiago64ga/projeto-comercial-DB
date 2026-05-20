from flask import render_template, jsonify, request
from app.db import get_session
from app.services import bi_queries
from sqlalchemy import text 



def init_routes(app):
   

    


    @app.route("/")
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
            banco_online=banco_online
        )


 









    @app.route("/filiais")
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


    @app.route("/produtos_detalhados")
    def produtos_detalhados():
        session = get_session()
        categoria = request.args.get("categoria")
        try:
            query, params = bi_queries.get_produtos_detalhados(categoria)
            result = session.execute(query, params)

            lista_produtos = [
                {
                    "produto": row.produto,
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
    def clientes():
        session = get_session()
        try:
            query = bi_queries.get_clientes()
            result = session.execute(query)

            lista_clientes = [
                {
                    "nome": row.nome,
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


    @app.route("/usuarios", methods=["GET"])
    def listar_usuarios():
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
        session = get_session()
        dados = request.get_json(silent=True) or {}

        try:
            usuario = bi_queries.autenticar_usuario(
                session,
                dados.get("id"),
                dados.get("password")
            )
            return jsonify(usuario)
        except ValueError as e:
            return jsonify({"erro": str(e)}), 401
        except Exception as e:
            return jsonify({"erro": str(e)}), 500
        finally:
            session.close()


    @app.route("/usuarios", methods=["POST"])
    def criar_usuario():
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
    def atualizar_status_usuario(user_id):
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
    def remover_usuario(user_id):
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
    def criar_venda():
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
                data_venda=dados.get("data")
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
        

    @app.route("/categorias")
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

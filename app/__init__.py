import os

from flask import Flask, jsonify
from sqlalchemy.exc import OperationalError, ProgrammingError

from .routes import init_routes


def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

    init_routes(app)

    # ✅ handler global automático de erro de banco
    @app.errorhandler(OperationalError)
    def handle_db_error(error):
        return jsonify({
            "error": "Banco de dados indisponível",
            "status": "db_down"
        }), 503

    @app.errorhandler(ProgrammingError)
    def handle_programming_error(error):
        sqlstate = getattr(getattr(error, "orig", None), "sqlstate", "")
        if sqlstate == "42703":
            return jsonify({
                "erro": "Coluna inexistente no banco de dados. Execute os scripts de criacao ou correcao de schema.",
                "status": "db_schema_error"
            }), 500
        if sqlstate == "42P01":
            return jsonify({
                "erro": "Tabela inexistente no banco de dados. Execute o script de criacao do banco.",
                "status": "db_schema_error"
            }), 500
        return jsonify({
            "erro": "Erro de estrutura ou sintaxe SQL no banco de dados.",
            "status": "db_sql_error"
        }), 500

    return app

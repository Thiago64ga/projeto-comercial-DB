import os

from flask import Flask, jsonify
from sqlalchemy.exc import OperationalError

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

    return app

from flask import Flask, jsonify

from config import configure_app
from extensions import db
from signing import auth as auth_module


def create_app():
    app = Flask(__name__)
    configure_app(app)

    db.init_app(app)
    auth_module.jwt.init_app(app)
    auth_module.redis_client = auth_module.init_redis(app)

    app.register_blueprint(auth_module.auth_bp, url_prefix="/auth")

    @app.route("/health")
    def health_check():
        return jsonify({"service": "signing", "status": "healthy"}), 200

    with app.app_context():
        if not app.config.get("SKIP_DATABASE_INIT", False):
            db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(app.config.get("PORT", 5001)), debug=bool(app.config.get("FLASK_DEBUG", False)))

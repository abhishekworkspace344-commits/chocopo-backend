from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from extensions import db, jwt


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)

    db.init_app(app)
    jwt.init_app(app)

    from routes import api
    app.register_blueprint(api)

    @app.route("/")
    def home():
        return jsonify({
            "message": "Welcome to CHOCOPO Cafe API",
            "status": "Backend is running"
        })

    with app.app_context():
        import models
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
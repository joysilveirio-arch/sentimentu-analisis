from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_class=Config):
    app = Flask(__name__,
                template_folder="../frontend/templates",
                static_folder="../frontend/static")
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login_page"
    login_manager.login_message = "Please log in to access this page."

    from backend.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from backend.routes.auth import auth_bp
    from backend.routes.dashboard import dashboard_bp
    from backend.routes.data import data_bp
    from backend.routes.admin import admin_bp
    from backend.routes.sentiment import sentiment_bp
    from backend.routes.labeling import labeling_bp
    from backend.routes.visualization import viz_bp
    from backend.routes.ml import ml_bp
    from backend.routes.pages import pages_bp
    
    app.register_blueprint(pages_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(sentiment_bp)
    app.register_blueprint(labeling_bp)
    app.register_blueprint(viz_bp)
    app.register_blueprint(ml_bp)

    from backend.utils.logging_config import setup_logging
    setup_logging(app)

    return app
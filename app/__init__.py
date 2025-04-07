from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from authlib.integrations.flask_client import OAuth
from config import Config
import openai

db = SQLAlchemy()
login_manager = LoginManager()
oauth = OAuth()
client = None  # This will be set during app creation

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    login_manager.init_app(app)
    oauth.init_app(app)
    
    # Set up the OpenAI client using the API key from configuration.
    global client
    client = openai.OpenAI(api_key=app.config['OPENAI_API_KEY'])
    
    # Import and register blueprints.
    from .main import main_bp
    from .auth import auth_bp
    from .admin import admin_bp
    from .chat import chat_bp
    from .store import store_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(chat_bp, url_prefix="/chat")
    app.register_blueprint(store_bp, url_prefix="/store")
    
    return app

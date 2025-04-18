from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_client import OAuth
from models import db

import openai
import os
import re
import time
from dotenv import load_dotenv

login_manager = LoginManager()
oauth = OAuth()

def create_app():
    load_dotenv()

    app = Flask(__name__)

    app.config.from_object("config.Config")

    db.init_app(app)
    login_manager.init_app(app)
    oauth.init_app(app)

    from models.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from routes.auth_routes import auth_bp
    from routes.chat_routes import chat_bp
    from routes.admin_routes import admin_bp
    from routes.general_routes import general_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(general_bp)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8000)



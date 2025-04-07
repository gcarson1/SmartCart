from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Store(db.Model):
    __tablename__ = 'stores'
    store_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(255), nullable=False)
    state = db.Column(db.String(255), nullable=False)
    zip_code = db.Column(db.String(20), nullable=False)
    inventory_file_id = db.Column(db.String(255))
    assistant_id = db.Column(db.String(255))
    vector_store_id = db.Column(db.String(255))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(255), unique=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def get_id(self):
        return str(self.user_id)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)

class ChatSession(db.Model):
    __tablename__ = 'chat_sessions'
    session_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.store_id'), nullable=True)
    title = db.Column(db.String(255), default='New Chat')
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    message_id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_sessions.session_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    sender = db.Column(db.String(10), nullable=False)  # 'user' or 'bot'
    message = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, server_default=db.func.now())

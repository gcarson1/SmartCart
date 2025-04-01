from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_client import OAuth

import openai
import os
import re
import time
from dotenv import load_dotenv

# Load environment variables (API key & existing assistant/vector store IDs)
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")
VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID")

app = Flask(__name__)

# Initialize OAuth and register the Google client
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),  # Set these in your .env file
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    access_token_url='https://oauth2.googleapis.com/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    api_base_url='https://www.googleapis.com/oauth2/v2/',
    client_kwargs={'scope': 'openid email profile'},
)

# Get the DATABASE_URL and fix the dialect if needed.
uri = os.getenv("DATABASE_URL")
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = uri

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

db = SQLAlchemy(app)

# Initialize OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

login_manager = LoginManager(app)
login_manager.login_view = 'user_login'

# ------------------
# Models
# ------------------

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(255), unique=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def get_id(self):
        return str(self.user_id)

    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# New Model: ChatSession to track each conversation
class ChatSession(db.Model):
    __tablename__ = 'chat_sessions'
    session_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    title = db.Column(db.String(255), default='New Chat')
    created_at = db.Column(db.DateTime, server_default=db.func.now())

# Updated ChatMessage model with session reference
class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    message_id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_sessions.session_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    sender = db.Column(db.String(10), nullable=False)  # 'user' or 'bot'
    message = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, server_default=db.func.now())

# ------------------
# OpenAI Helper Functions
# ------------------

def get_existing_assistant():
    assistants = client.beta.assistants.list()
    for assistant in assistants.data:
        if assistant.id == ASSISTANT_ID:
            print(f"Using existing Assistant ID: {ASSISTANT_ID}")
            return ASSISTANT_ID
    return None

def get_existing_vector_store():
    vector_stores = client.beta.vector_stores.list()
    for store in vector_stores.data:
        if store.id == VECTOR_STORE_ID:
            print(f"Using existing Vector Store ID: {VECTOR_STORE_ID}")
            return VECTOR_STORE_ID
    return None

def run_assistant(user_input):
    thread = client.beta.threads.create()
    print(f"Thread Created: {thread.id}")

    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_input
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id, assistant_id=ASSISTANT_ID
    )

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    
    response_text = ""
    for block in messages.data[0].content:
        if block.type == "text":
            response_text += block.text.value

    pattern = r'【\d+†source】'
    response_text = re.sub(pattern, '', response_text)

    return response_text

# ------------------
# Routes
# ------------------

@app.route("/")
def index():
    return render_template("index.html")

# New Route: Create a new chat session
@app.route("/new_chat", methods=["POST"])
@login_required
def new_chat():
    title = request.json.get("title", "New Chat")
    new_session = ChatSession(user_id=current_user.user_id, title=title)
    db.session.add(new_session)
    db.session.commit()
    return jsonify({"session_id": new_session.session_id, "title": new_session.title})

# New Route: Get list of chat sessions for the logged in user
@app.route("/chat_sessions", methods=["GET"])
@login_required
def chat_sessions():
    sessions = ChatSession.query.filter_by(user_id=current_user.user_id).order_by(ChatSession.created_at.desc()).all()
    session_list = [{
        "session_id": s.session_id,
        "title": s.title,
        "created_at": s.created_at.isoformat()
    } for s in sessions]
    return jsonify(session_list)

# Updated Route: Get chat history for a specific session
@app.route("/chat_history", methods=["GET"])
@login_required
def chat_history():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"error": "No session id provided."}), 400
    messages = ChatMessage.query.filter_by(user_id=current_user.user_id, session_id=session_id).order_by(ChatMessage.sent_at).all()
    history = [{'sender': msg.sender, 'message': msg.message} for msg in messages]
    return jsonify(history)

# Updated Route: Send a message (requires session_id)
@app.route("/get", methods=["POST"])
@login_required
def get_bot_response():
    data = request.get_json() or {}
    user_input = data.get('msg')
    session_id = data.get('session_id')
    
    if not session_id:
        return jsonify({'error': 'No session id provided.'}), 400
    if not user_input:
        return jsonify({'error': 'No message provided.'}), 400

    # Save the user's message
    user_message = ChatMessage(
        session_id=session_id,
        user_id=current_user.user_id,
        sender='user',
        message=user_input
    )
    db.session.add(user_message)
    db.session.commit()

    # Generate bot response
    bot_response = run_assistant(user_input)

    # Save the bot's response
    bot_message = ChatMessage(
        session_id=session_id,
        user_id=current_user.user_id,
        sender='bot',
        message=bot_response
    )
    db.session.add(bot_message)
    db.session.commit()

    return jsonify({'response': bot_response})

@app.route('/refresh')
def refresh():
    time.sleep(600)
    return redirect('/refresh')

@app.route('/admin_login', methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "user1234" and password == "pass1234":
            return redirect("/admin_panel")
        else:
            error = "Invalid credentials. Please try again."
    return render_template("admin_login.html", error=error)

def create_dynamic_assistant(txt_file):
    # Ensure the file pointer is at the start
    txt_file.seek(0)
    try:
        # Step 1: Upload the text file using the underlying stream
        uploaded_file = client.files.create(
            file=(txt_file.filename, txt_file.stream, "text/plain"),
            purpose="assistants"
        )
        print(f"Uploaded file, id: {uploaded_file.id}")
    except Exception as e:
        raise Exception(f"Failed to upload file: {e}")

    try:
        # Step 2: Create a new vector store and attach the uploaded file via its file ID.
        vector_store = client.beta.vector_stores.create(
            name=f"Dynamic Vector Store {int(time.time())}",
            file_ids=[uploaded_file.id]
        )
        new_vector_store_id = vector_store.id
        print(f"Created new vector store with ID: {new_vector_store_id}")
    except Exception as e:
        raise Exception(f"Failed to create vector store: {e}")

    try:
        # Step 3: Create a new assistant with file_search enabled and attach the vector store.
        assistant = client.beta.assistants.create(
            name=f"Dynamic Assistant {int(time.time())}",
            instructions="You are a helpful assistant that uses file search to answer questions based on the uploaded document.",
            model="gpt-4o-mini",
            tools=[{"type": "file_search"}],
            tool_resources={
                "file_search": {"vector_store_ids": [new_vector_store_id]}
            }
        )
        new_assistant_id = assistant.id
        print(f"Created new assistant with ID: {new_assistant_id}")
    except Exception as e:
        raise Exception(f"Failed to create dynamic assistant: {e}")

    # Return the assistant ID, vector store ID, and the uploaded file's ID.
    return new_assistant_id, new_vector_store_id, uploaded_file.id

@app.route('/admin_panel', methods=["GET", "POST"])
def admin_panel():
    message = None
    if request.method == "POST":
        txt_file = request.files.get("txtFile")
        if txt_file:
            try:
                # Reset file pointer
                txt_file.seek(0)
                new_assistant_id, new_vector_store_id, uploaded_file_id = create_dynamic_assistant(txt_file)
                message = (f"Store Inventory Created. Assistant ID: {new_assistant_id}, Vector Store ID: {new_vector_store_id}, File ID: {uploaded_file_id}")
            except Exception as e:
                message = f"Error creating dynamic assistant: {str(e)}"
        else:
            message = "No file selected."
    return render_template("admin_panel.html", message=message)

# New endpoint: Delete an uploaded file from vector store
@app.route('/delete_uploaded_file', methods=["POST"])
def delete_uploaded_file():
    data = request.get_json() or {}
    file_id = data.get("file_id")
    if not file_id:
        return jsonify({"error": "No file id provided."}), 400
    try:
        # Delete the file from OpenAI (this removes it from all vector store associations)
        deletion_result = client.files.delete(file_id)
        return jsonify({"success": True, "message": "File deleted from vector store.", "result": deletion_result})
    except Exception as e:
        print("Error deleting file:", e)
        return jsonify({"success": False, "error": str(e)})

@app.route('/user_login', methods=["GET", "POST"])
def user_login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            error = "Invalid username or password. Please try again."
        else:
            login_user(user)
            return redirect(url_for('index'))
    return render_template("user_login.html", error=error)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/user_panel')
def user_panel():
    return render_template("user_login.html")

@app.route('/signup', methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        email = request.form.get("email")
        if not username or not password or not confirm_password:
            error = "All fields are required."
        elif password != confirm_password:
            error = "Passwords do not match."
        else:
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                error = "Username already exists."
            else:
                new_user = User(username=username, email=email)
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for('user_login'))
    return render_template("signup.html", error=error)

@app.route("/delete_chat_history", methods=["POST"])
@login_required
def delete_chat_history():
    data = request.get_json() or {}
    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"error": "No session id provided."}), 400

    try:
        session_id = int(session_id)
    except ValueError:
        return jsonify({"error": "Invalid session id provided."}), 400

    # Retrieve the chat session for the current user
    session_to_delete = ChatSession.query.filter_by(session_id=session_id, user_id=current_user.user_id).first()
    if not session_to_delete:
        return jsonify({"message": "Chat session not found."}), 200

    # Delete associated chat messages
    ChatMessage.query.filter_by(session_id=session_id, user_id=current_user.user_id).delete()
    # Delete the session itself
    db.session.delete(session_to_delete)
    db.session.commit()
    
    return jsonify({"message": "Chat session deleted successfully."})

@app.route('/google_login')
def google_login():
    # Redirect user to Google's OAuth consent page.
    redirect_uri = url_for('google_authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/google_authorize')
def google_authorize():
    # Handle the callback from Google
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    user_info = resp.json()
    email = user_info.get('email')
    
    # Check if the user exists; if not, create one.
    user = User.query.filter_by(email=email).first()
    if not user:
        # Creating a user for Google login: username is set as email.
        # A random password is generated since our model requires one.
        random_password = os.urandom(16).hex()
        user = User(username=email, email=email)
        user.set_password(random_password)
        db.session.add(user)
        db.session.commit()
    
    login_user(user)
    return redirect(url_for('index'))


if __name__ == "__main__":
    if not get_existing_assistant():
        print("⚠️ Assistant ID not found in OpenAI. Make sure it exists or update your .env file.")
    if not get_existing_vector_store():
        print("⚠️ Vector Store ID not found in OpenAI. Make sure it exists or update your .env file.")
    app.run(debug=True)

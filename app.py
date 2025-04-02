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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class ChatSession(db.Model):
    __tablename__ = 'chat_sessions'
    session_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.store_id'), nullable=True)  # New field
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

@app.route("/new_chat", methods=["POST"])
@login_required
def new_chat():
    data = request.get_json() or {}
    store_id = data.get("store_id")  # Capture the selected store_id from the client
    if store_id:
        # Count existing sessions for this user and store
        count = ChatSession.query.filter_by(user_id=current_user.user_id, store_id=store_id).count()
        # Retrieve the store name from the Store model
        store = Store.query.get(store_id)
        store_name = store.name if store else "Store"
        title = f"{store_name} Chat {count + 1}"
    else:
        title = "New Chat"
        
    new_session = ChatSession(user_id=current_user.user_id, title=title, store_id=store_id)
    db.session.add(new_session)
    db.session.commit()
    return jsonify({"session_id": new_session.session_id, "title": new_session.title})

@app.route("/chat_sessions", methods=["GET"])
@login_required
def chat_sessions():
    sessions = ChatSession.query.filter_by(user_id=current_user.user_id).order_by(ChatSession.created_at.desc()).all()
    session_list = [{
        "session_id": s.session_id,
        "title": s.title,
        "store_id": s.store_id,  # add this line
        "created_at": s.created_at.isoformat()
    } for s in sessions]
    return jsonify(session_list)

@app.route("/chat_history", methods=["GET"])
@login_required
def chat_history():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"error": "No session id provided."}), 400
    messages = ChatMessage.query.filter_by(user_id=current_user.user_id, session_id=session_id).order_by(ChatMessage.sent_at).all()
    history = [{'sender': msg.sender, 'message': msg.message} for msg in messages]
    return jsonify(history)

def run_assistant_for_store(assistant_id, user_input):
    thread = client.beta.threads.create()
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_input
    )
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant_id
    )
    messages = client.beta.threads.messages.list(thread_id=thread.id)

    response_text = ""
    for block in messages.data[0].content:
        if block.type == "text":
            response_text += block.text.value

    pattern = r'【\d+†source】'
    response_text = re.sub(pattern, '', response_text)
    return response_text


@app.route("/get", methods=["POST"])
def get_bot_response():
    print("⚠️ Assistant ID not found in OpenAI. Make sure it exists or update your .env file.")

    data = request.get_json() or {}
    user_input = data.get('msg')
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({'error': 'No session id provided.'}), 400
    if not user_input:
        return jsonify({'error': 'No message provided.'}), 400

    # Retrieve the chat session and its associated store
    session_obj = ChatSession.query.filter_by(session_id=session_id, user_id=current_user.user_id).first()
    store_id = session_obj.store_id if session_obj else None

    # Save the user's message
    user_message = ChatMessage(
        session_id=session_id,
        user_id=current_user.user_id,
        sender='user',
        message=user_input
    )
    db.session.add(user_message)
    db.session.commit()

    # Use the store's assistant if store_id exists; otherwise, fall back to the generic assistant.
    if store_id:
        store = Store.query.get(store_id)
        if store and store.assistant_id:
            bot_response = run_assistant_for_store(store.assistant_id, user_input)
        else:
            bot_response = run_assistant(user_input)
    else:
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

@app.route('/admin_signup', methods=["GET", "POST"])
def admin_signup():
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
                new_admin = User(username=username, email=email, is_admin=True)
                new_admin.set_password(password)
                db.session.add(new_admin)
                db.session.commit()
                return redirect(url_for('admin_login'))
    return render_template("admin_signup.html", error=error)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = User.query.filter_by(username=username, is_admin=True).first()
        if not admin or not admin.check_password(password):
            error = "Invalid credentials or not an admin user."
            return render_template('admin_login.html', error=error)
        login_user(admin)
        return redirect('/admin_panel')
    return render_template('admin_login.html', error=error)

@app.route('/refresh')
def refresh():
    time.sleep(600)
    return redirect('/refresh')

def add_admin(username, password, email):
    hashed_password = generate_password_hash(password)
    query = "INSERT INTO users (username, password, email, is_admin) VALUES (:username, :password, :email, true)"
    db.session.execute(query, {'username': username, 'password': hashed_password, 'email': email})
    db.session.commit()

@app.route("/stores")
@login_required
def list_stores():
    all_stores = Store.query.all()
    results = []
    for s in all_stores:
        results.append({
            "store_id": s.store_id,
            "name": s.name,
            "address": s.address,
            "assistant_id": s.assistant_id
        })
    return jsonify(results)

def create_dynamic_assistant(txt_file):
    txt_file.seek(0)
    try:
        uploaded_file = client.files.create(
            file=(txt_file.filename, txt_file.stream, "text/plain"),
            purpose="assistants"
        )
        print(f"Uploaded file, id: {uploaded_file.id}")
    except Exception as e:
        raise Exception(f"Failed to upload file: {e}")

    try:
        vector_store = client.beta.vector_stores.create(
            name=f"Dynamic Vector Store {int(time.time())}",
            file_ids=[uploaded_file.id]
        )
        new_vector_store_id = vector_store.id
        print(f"Created new vector store with ID: {new_vector_store_id}")
    except Exception as e:
        raise Exception(f"Failed to create vector store: {e}")

    try:
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

    return new_assistant_id, new_vector_store_id, uploaded_file.id

@app.route('/admin_panel', methods=["GET", "POST"])
@login_required
def admin_panel():
    store = Store.query.filter_by(user_id=current_user.user_id).first()
    message = None
    
    # Step 1: If no store exists, show the Store Info Form.
    if not store:
        if request.method == "POST" and 'name' in request.form:
            name = request.form.get("name")
            address = request.form.get("address")
            city = request.form.get("city")
            state = request.form.get("state")
            zip_code = request.form.get("zip_code")
            if not (name and address and city and state and zip_code):
                message = "All fields are required."
            else:
                new_store = Store(
                    user_id=current_user.user_id,
                    name=name,
                    address=address,
                    city=city,
                    state=state,
                    zip_code=zip_code
                )
                db.session.add(new_store)
                db.session.commit()
                message = "Store information saved. Please upload your inventory file."
                store = new_store
        return render_template("admin_panel.html", message=message, store=store)
    
    # Step 2: If store exists but no inventory file is present, handle file upload.
    if not store.inventory_file_id:
        if request.method == "POST" and 'txtFile' in request.files:
            txt_file = request.files.get("txtFile")
            if txt_file:
                try:
                    txt_file.seek(0)
                    # Check if an assistant already exists for the store.
                    if store.assistant_id:
                        # Upload the new file.
                        uploaded_file = client.files.create(
                            file=(txt_file.filename, txt_file.stream, "text/plain"),
                            purpose="assistants"
                        )
                        new_file_id = uploaded_file.id
                        print(f"Uploaded new file, id: {new_file_id}")
                        
                        # Create a new vector store using the new file.
                        vector_store = client.beta.vector_stores.create(
                            name=f"Dynamic Vector Store {int(time.time())}",
                            file_ids=[new_file_id]
                        )
                        new_vector_store_id = vector_store.id
                        print(f"Created new vector store with ID: {new_vector_store_id}")
                        
                        # Update the existing assistant to use the new vector store.
                        client.beta.assistants.update(
                            store.assistant_id,
                            tool_resources={"file_search": {"vector_store_ids": [new_vector_store_id]}}
                        )
                        new_assistant_id = store.assistant_id
                        print(f"Updated existing assistant {new_assistant_id} with new vector store.")
                    else:
                        # No assistant exists, so create one.
                        new_assistant_id, new_vector_store_id, new_file_id = create_dynamic_assistant(txt_file)
                    
                    # Update the store record with new file and vector store info.
                    store.inventory_file_id = new_file_id
                    store.vector_store_id = new_vector_store_id
                    store.assistant_id = new_assistant_id  # preserves existing assistant if present
                    db.session.commit()
                    message = f"Inventory updated. New File ID: {new_file_id}"
                except Exception as e:
                    message = f"Error updating inventory: {str(e)}"
            else:
                message = "No file selected."
        return render_template("admin_panel.html", message=message, store=store)
    
    # Step 3: If store has an inventory file, show the dashboard view.
    return render_template("admin_panel.html", message=message, store=store)

@app.route('/update_inventory', methods=["GET", "POST"])
@login_required
def update_inventory():
    store = Store.query.filter_by(user_id=current_user.user_id).first()
    if not store:
        return redirect(url_for('admin_panel'))
    
    message = None
    if request.method == "POST":
        if 'txtFile' not in request.files:
            message = "No file selected."
        else:
            txt_file = request.files.get("txtFile")
            if txt_file:
                try:
                    # If an old file exists, try to delete it.
                    if store.inventory_file_id:
                        try:
                            client.files.delete(store.inventory_file_id)
                        except Exception as e:
                            print(f"Error deleting old file: {e}")
                    
                    # Create new file in OpenAI
                    txt_file.seek(0)
                    try:
                        uploaded_file = client.files.create(
                            file=(txt_file.filename, txt_file.stream, "text/plain"),
                            purpose="assistants"
                        )
                        new_file_id = uploaded_file.id
                        print(f"Uploaded new file, id: {new_file_id}")
                    except Exception as e:
                        raise Exception(f"Failed to upload file: {e}")
                    
                    # Create a new vector store with the new file
                    try:
                        vector_store = client.beta.vector_stores.create(
                            name=f"Dynamic Vector Store {int(time.time())}",
                            file_ids=[new_file_id]
                        )
                        new_vector_store_id = vector_store.id
                        print(f"Created new vector store with ID: {new_vector_store_id}")
                    except Exception as e:
                        raise Exception(f"Failed to create vector store: {e}")
                    
                    # If an assistant already exists, update its tool_resources;
                    # otherwise, create a new assistant.
                    if store.assistant_id:
                        try:
                            client.beta.assistants.update(
                                store.assistant_id,
                                tool_resources={"file_search": {"vector_store_ids": [new_vector_store_id]}}
                            )
                            new_assistant_id = store.assistant_id
                            print(f"Updated existing assistant {new_assistant_id} with new vector store.")
                        except Exception as e:
                            print(f"Error updating assistant: {e}")
                            new_assistant_id = store.assistant_id
                    else:
                        try:
                            assistant = client.beta.assistants.create(
                                name=f"Dynamic Assistant {int(time.time())}",
                                instructions="You are a helpful assistant that uses file search to answer questions based on the uploaded document.",
                                model="gpt-4o-mini",
                                tools=[{"type": "file_search"}],
                                tool_resources={"file_search": {"vector_store_ids": [new_vector_store_id]}}
                            )
                            new_assistant_id = assistant.id
                            print(f"Created new assistant with ID: {new_assistant_id}")
                        except Exception as e:
                            raise Exception(f"Failed to create dynamic assistant: {e}")
                    
                    # Update the store record with the new file and vector store IDs.
                    store.inventory_file_id = new_file_id
                    store.vector_store_id = new_vector_store_id
                    # Preserve the existing assistant_id if it exists.
                    store.assistant_id = new_assistant_id  
                    db.session.commit()
                    
                    message = f"Inventory updated. New File ID: {new_file_id}"
                except Exception as e:
                    message = f"Error updating inventory: {str(e)}"
            else:
                message = "No file selected."
    return render_template("update_inventory.html", message=message, store=store)

@app.route('/delete_uploaded_file', methods=["POST"])
def delete_uploaded_file():
    data = request.get_json() or {}
    file_id = data.get("file_id")
    if not file_id:
        return jsonify({"error": "No file id provided."}), 400
    try:
        deletion_result = client.files.delete(file_id)
    except Exception as e:
        error_message = str(e)
        if "No such File object" in error_message:
            deletion_result = {"message": "File not found; treating as deleted."}
        else:
            print("Error deleting file:", e)
            return jsonify({"success": False, "error": error_message})
    
    store = Store.query.filter_by(inventory_file_id=file_id).first()
    if store:
        # If a vector store exists, delete it too.
        if store.vector_store_id:
            try:
                client.beta.vector_stores.delete(store.vector_store_id)
            except Exception as e:
                print("Error deleting vector store:", e)
        # Clear the file and vector store IDs from the store record.
        store.inventory_file_id = None
        store.vector_store_id = None
        db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "File and associated vector store deleted, store record updated.",
        "result": deletion_result
    })


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

    session_to_delete = ChatSession.query.filter_by(session_id=session_id, user_id=current_user.user_id).first()
    if not session_to_delete:
        return jsonify({"message": "Chat session not found."}), 200

    ChatMessage.query.filter_by(session_id=session_id, user_id=current_user.user_id).delete()
    db.session.delete(session_to_delete)
    db.session.commit()
    
    return jsonify({"message": "Chat session deleted successfully."})

@app.route('/google_login')
def google_login():
    redirect_uri = url_for('google_authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/google_authorize')
def google_authorize():
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    user_info = resp.json()
    email = user_info.get('email')
    
    user = User.query.filter_by(email=email).first()
    if not user:
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
    app.run(debug=True)
